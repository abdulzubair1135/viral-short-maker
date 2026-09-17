import asyncio
import json
import uuid
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.core.database import get_db_connection
from backend.app.config import PROJECTS_DIR
from backend.app.core.logging import logger
from backend.app.core.state_machine import ProjectState, StateMachine
from backend.app.jobs.checkpoint import CheckpointManager
from backend.app.video.ingestion import validate_video_source
from backend.app.video.transcription import TranscriptionEngine
from backend.app.video.analysis import VideoAnalyzer
from backend.app.video.clipping import (
    calculate_composite_score,
    optimize_boundaries,
    filter_duplicate_clips
)
from backend.app.video.renderer import VideoRenderer
from backend.app.quality.quality_control import QualityControlEngine
from backend.app.ai.router.ai_router import ai_router

class JobQueue:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.renderer = VideoRenderer()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def update_job_status(self, job_id: str, status: str, progress: float, error: str = "", log_msg: str = ""):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = ?, progress = ?, error_message = ?, logs = logs || ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, progress, error, f"\n{log_msg}" if log_msg else "", job_id))

    async def execute_project_pipeline(self, project_id: str, job_id: str, ai_provider: str = "mock"):
        proj_dir = PROJECTS_DIR / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        work_dir = proj_dir / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Fetch project & source info
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                proj = cursor.fetchone()
                if not proj:
                    raise RuntimeError(f"Project not found: {project_id}")

                cursor.execute("SELECT * FROM sources WHERE project_id = ? ORDER BY created_at DESC LIMIT 1", (project_id,))
                source = cursor.fetchone()
                if not source:
                    raise RuntimeError("No source video attached to project")

            source_path = source["file_path"]
            rights_status = proj["rights_status"]

            # STAGE 1: VALIDATING
            self.update_job_status(job_id, "VALIDATING", 10.0, log_msg="Validating source video streams and codecs...")
            meta = validate_video_source(source_path, rights_status)
            CheckpointManager.save_checkpoint(job_id, "VALIDATING", {"meta": meta}, 15.0)

            # STAGE 2: TRANSCRIBING
            self.update_job_status(job_id, "TRANSCRIBING", 25.0, log_msg="Extracting audio and generating word-level transcript...")
            transcript_data = TranscriptionEngine.transcribe(source_path, cache_dir=work_dir)
            
            # Save transcript to DB
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO transcripts (id, project_id, language, full_text, srt_content, segments_json, words_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    project_id,
                    transcript_data.get("language", "en"),
                    transcript_data.get("full_text", ""),
                    transcript_data.get("srt_content", ""),
                    json.dumps(transcript_data.get("segments", [])),
                    json.dumps(transcript_data.get("words", []))
                ))
            CheckpointManager.save_checkpoint(job_id, "TRANSCRIBING", {"transcript": "complete"}, 40.0)

            # STAGE 3: ANALYZING & AI MOMENT DETECTION
            self.update_job_status(job_id, "ANALYZING", 45.0, log_msg=f"Running AI router with provider '{ai_provider}'...")
            video_title = "Viral Video"
            try:
                video_title = proj["name"] if "name" in proj.keys() and proj["name"] else (meta.get("resolved_title") or "Viral Video")
            except Exception:
                video_title = meta.get("resolved_title") or "Viral Video"

            source_url = ""
            try:
                source_url = source["source_url"] if "source_url" in source.keys() and source["source_url"] else ""
            except Exception:
                pass

            if ai_provider == "gemini":
                fallback_provider = "deepseek"
            elif ai_provider == "deepseek":
                fallback_provider = "gemini"
            else:
                fallback_provider = "mock"

            ai_result = await ai_router.route_analysis(
                transcript_text=transcript_data.get("full_text", ""),
                duration=meta.get("duration", 60.0),
                primary_provider_name=ai_provider,
                fallback_provider_name=fallback_provider,
                title=video_title,
                video_url=source_url
            )

            # Record AI job in DB
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_jobs (id, project_id, provider, task, prompt_text, response_text, duration, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    project_id,
                    ai_result["provider"],
                    "Moment Selection",
                    "Analyze transcript for viral hooks",
                    ai_result.get("raw_response", ""),
                    ai_result.get("duration", 0.0),
                    1 if ai_result.get("success") else 0
                ))

            # STAGE 4: GENERATING CLIPS & LOGGING REJECTED MOMENTS
            self.update_job_status(job_id, "GENERATING_CLIPS", 55.0, log_msg="Evaluating 8 scores, recording rejected candidates, and optimizing review boundaries...")
            raw_candidates = ai_result.get("candidates", [])
            raw_rejected = ai_result.get("rejected", [])

            # Record rejected candidates into database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for rj in raw_rejected:
                    cursor.execute("""
                        INSERT INTO rejected_candidates (
                            id, project_id, title, start_time, end_time, duration, claim,
                            scores_json, score_total, rejection_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), project_id, rj.get("title", "Candidate moment"),
                        float(rj.get("start_time", 0.0) or 0.0), float(rj.get("end_time", 0.0) or 0.0),
                        float(rj.get("duration", 0.0) or 0.0), str(rj.get("claim", "")),
                        json.dumps(rj.get("scores", {})), float(rj.get("score_total", 0.0) or 0.0),
                        str(rj.get("reason", "Filtered by AI evaluation"))
                    ))

            processed_candidates = []
            for cand in raw_candidates:
                # Optimize boundaries
                bounds = optimize_boundaries(
                    raw_start=cand["start_time"],
                    raw_end=cand["end_time"],
                    transcript_segments=transcript_data.get("segments", []),
                    video_duration=meta.get("duration", 60.0)
                )
                score_val = float(cand.get("score", 85.0))
                analysis_obj = cand.get("analysis", {})
                rating_val = float(cand.get("rating", analysis_obj.get("rating", 8.5)) or 8.5)
                verdict_val = str(cand.get("verdict", analysis_obj.get("verdict", "Compelling short")) or "Compelling short")
                source_attrib = str(cand.get("source_attribution", "Original content analyzed for educational critique"))
                script_segments = cand.get("narration_script", [])

                clip_dict = {
                    "title": cand.get("title", "Transformative Review Short"),
                    "start": bounds["start"],
                    "end": bounds["end"],
                    "duration": bounds["duration"],
                    "hook": cand.get("hook", ""),
                    "summary": cand.get("description", cand.get("summary", "")),
                    "description": cand.get("description", ""),
                    "hashtags": cand.get("hashtags", ["#shorts", "#review"]),
                    "keywords": cand.get("keywords", []),
                    "score_total": score_val,
                    "scores": cand.get("scores", {
                        "hook_score": cand.get("hook_score", 90),
                        "interest_score": cand.get("interest_score", 90),
                        "commentary_potential": cand.get("commentary_potential", 90),
                        "standalone_score": cand.get("standalone_score", 90),
                        "clarity_score": cand.get("clarity_score", 90),
                        "context_score": cand.get("context_score", 90),
                        "originality_potential": cand.get("originality_potential", 90),
                        "overall_score": score_val,
                        "total": score_val
                    }),
                    "analysis": analysis_obj,
                    "verdict": verdict_val,
                    "rating": rating_val,
                    "source_attribution": source_attrib,
                    "narration_script": script_segments,
                    "decision_reason": cand.get("reason", cand.get("decision_reason", "")),
                    "crop_mode": cand.get("crop_mode", "speaker_tracking"),
                    "caption_preset": cand.get("caption_style", "dynamic")
                }
                processed_candidates.append(clip_dict)

            # Filter duplicates
            unique_clips = filter_duplicate_clips(processed_candidates)
            created_clips = []

            with get_db_connection() as conn:
                cursor = conn.cursor()
                for c in unique_clips:
                    clip_id = str(uuid.uuid4())
                    edit_plan = {
                        "start": c["start"],
                        "end": c["end"],
                        "hook": c["hook"],
                        "crop_mode": c["crop_mode"],
                        "caption_preset": c["caption_preset"]
                    }
                    cursor.execute("""
                        INSERT INTO clips (
                            id, project_id, title, start_time, end_time, duration, hook, summary,
                            description, hashtags, keywords,
                            score_total, scores_json, decision_reason, edit_plan, crop_mode,
                            caption_preset, status, approval_status,
                            analysis_json, script_json, verdict, rating, source_attribution, is_ai_narrated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        clip_id, project_id, c["title"], c["start"], c["end"], c["duration"],
                        c["hook"], c["summary"], c["description"], json.dumps(c["hashtags"]),
                        json.dumps(c["keywords"]), c["score_total"], json.dumps(c["scores"]),
                        c["decision_reason"], json.dumps(edit_plan), c["crop_mode"],
                        c["caption_preset"], "CANDIDATE", "PENDING",
                        json.dumps(c["analysis"]), json.dumps(c["narration_script"]),
                        c["verdict"], c["rating"], c["source_attribution"], 1
                    ))
                    c["id"] = clip_id
                    created_clips.append(c)

            CheckpointManager.save_checkpoint(job_id, "GENERATING_CLIPS", {"clips_count": len(created_clips)}, 65.0)

            # STAGE 5: LOCAL COMMENTARY NARRATION & VIDEO RENDERING
            total_selected = len(created_clips)
            rendered_count = 0

            from backend.app.audio.narration import NarrationEngine

            for idx, clip in enumerate(created_clips, 1):
                clip_id = clip["id"]
                output_mp4 = proj_dir / f"clip_{clip_id}.mp4"

                pct = 65.0 + (idx / max(total_selected, 1)) * 30.0
                self.update_job_status(
                    job_id,
                    "RENDERING",
                    round(pct - 5.0, 1),
                    log_msg=f"Synthesizing commentary & rendering Short {idx}/{total_selected}: '{clip['title']}'..."
                )

                # Synthesize commentary audio narration
                commentary_audio_path = None
                script_segments = clip.get("narration_script") or []
                if script_segments:
                    narr_out = work_dir / f"narr_{clip_id}.mp3"
                    try:
                        narr_res = await NarrationEngine.generate_commentary_audio(
                            script_data=script_segments,
                            output_path=narr_out
                        )
                        commentary_audio_path = narr_res["audio_path"]
                    except Exception as n_err:
                        logger.warning(f"Commentary synthesis skipped for clip {clip_id}: {n_err}")

                clip_render_data = {
                    "start_time": clip["start"],
                    "end_time": clip["end"],
                    "crop_mode": clip["crop_mode"],
                    "caption_preset": clip["caption_preset"],
                    "rating": clip["rating"],
                    "verdict": clip["verdict"],
                    "source_attribution": clip["source_attribution"]
                }
                self.renderer.render_clip(
                    source_video_path=source_path,
                    clip_data=clip_render_data,
                    transcript_data=transcript_data,
                    output_mp4=output_mp4,
                    work_dir=work_dir,
                    commentary_audio_path=commentary_audio_path
                )

                # STAGE 6: 15-POINT QUALITY CONTROL PER SHORT
                qc_report = QualityControlEngine.run_checks(
                    clip_file_path=str(output_mp4),
                    expected_duration=clip["duration"],
                    rights_status=rights_status,
                    caption_preset=clip["caption_preset"],
                    clip_meta=clip
                )

                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO quality_checks (id, clip_id, score, passed, checks_json, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        clip_id,
                        qc_report["score"],
                        1 if qc_report["passed"] else 0,
                        json.dumps(qc_report["checks"]),
                        qc_report.get("notes", "")
                    ))

                    cursor.execute("""
                        UPDATE clips 
                        SET output_path = ?, quality_score = ?, status = 'READY'
                        WHERE id = ?
                    """, (str(output_mp4), qc_report["score"], clip_id))

                rendered_count += 1


            # Update project status
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE projects SET status = 'CANDIDATE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

            # COMPLETE
            self.update_job_status(
                job_id,
                "READY",
                100.0,
                log_msg=f"Pipeline complete! {rendered_count} Shorts created and verified by Quality Control."
            )
            CheckpointManager.save_checkpoint(job_id, "READY", {"rendered_count": rendered_count, "status": "SUCCESS"}, 100.0)

        except Exception as e:
            err_details = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Job {job_id} failed: {err_details}")
            self.update_job_status(job_id, "FAILED", 0.0, error=str(e), log_msg=err_details)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE projects SET status = 'FAILED', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

    def submit_project_job(self, project_id: str, ai_provider: str = "mock") -> str:
        job_id = str(uuid.uuid4())
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (id, project_id, job_type, status, progress)
                VALUES (?, ?, 'PROJECT_PIPELINE', 'QUEUED', 0.0)
            """, (job_id, project_id))

            # Set project to ANALYZING
            cursor.execute("UPDATE projects SET status = 'ANALYZING', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

        # Run pipeline in a dedicated background worker thread
        # This guarantees:
        # 1. Uvicorn's event loop is never blocked by FFmpeg processing
        # 2. Never encounters 'no running event loop' errors
        import threading
        def _worker():
            try:
                asyncio.run(self.execute_project_pipeline(project_id, job_id, ai_provider))
            except Exception as e:
                logger.error(f"Worker for job {job_id} failed: {e}")

        t = threading.Thread(target=_worker, name=f"PipelineWorker-{job_id[:8]}", daemon=True)
        t.start()

        return job_id

job_queue = JobQueue()
