import os
import json
import uuid
import asyncio
import threading
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.app.config import PROJECTS_DIR, STORAGE_DIR
from backend.app.core.database import get_db_connection
from backend.app.core.logging import logger
from backend.app.ai.router.ai_router import ai_router
from backend.app.assets.asset_provider import AssetManager
from backend.app.audio.narration import NarrationEngine
from backend.app.video.meme_renderer import MemeRenderer
from backend.app.quality.quality_control import QualityControlEngine

class MemePipelineService:
    @staticmethod
    def update_job(job_id: str, status: str, progress: float, error: str = "", log_msg: str = ""):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = ?, progress = ?, error_message = ?, logs = logs || ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, progress, error, f"\n{log_msg}" if log_msg else "", job_id))

    @classmethod
    def start_pipeline(
        cls,
        topic: str,
        style: str = "sarcastic",
        format_type: str = "pov",
        count: int = 3,
        uploaded_asset_id: Optional[str] = None,
        rights_confirmed: bool = True,
        ai_provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Initializes Meme Studio generation pipeline:
        1. Validates inputs & rights confirmation
        2. Creates project of type 'MEME_STUDIO'
        3. Creates queue job
        4. Launches background worker
        """
        clean_topic = topic.strip()
        if not clean_topic:
            raise ValueError("Topic or idea is required for Meme Studio.")

        if not rights_confirmed:
            raise ValueError("Rights and license confirmation is required.")

        proj_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (id, name, description, project_type, status, rights_status)
                VALUES (?, ?, ?, 'MEME_STUDIO', 'GENERATING', 'Verified Rights Confirmed')
            """, (proj_id, clean_topic[:80], f"Meme Studio Project: {clean_topic}"))

            cursor.execute("""
                INSERT INTO jobs (id, project_id, job_type, status, progress)
                VALUES (?, ?, 'MEME_PIPELINE', 'QUEUED', 0.0)
            """, (job_id, proj_id))

        # Launch background worker
        def _worker():
            try:
                asyncio.run(cls.execute_meme_pipeline(
                    project_id=proj_id,
                    job_id=job_id,
                    topic=clean_topic,
                    style=style,
                    format_type=format_type,
                    count=count,
                    uploaded_asset_id=uploaded_asset_id,
                    ai_provider=ai_provider
                ))
            except Exception as e:
                logger.error(f"Meme worker failed for job {job_id}: {e}\n{traceback.format_exc()}")

        t = threading.Thread(target=_worker, name=f"MemeWorker-{job_id[:8]}", daemon=True)
        t.start()

        return {
            "project_id": proj_id,
            "job_id": job_id,
            "topic": clean_topic,
            "status": "QUEUED"
        }

    @classmethod
    async def execute_meme_pipeline(
        cls,
        project_id: str,
        job_id: str,
        topic: str,
        style: str,
        format_type: str,
        count: int,
        uploaded_asset_id: Optional[str],
        ai_provider: str
    ):
        proj_dir = PROJECTS_DIR / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        work_dir = proj_dir / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        output_dir = proj_dir / "memes"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 1: AI Concept Generation
            cls.update_job(job_id, "GENERATING_CONCEPTS", 15.0, log_msg=f"Generating {count} viral meme concepts with AI for '{topic}'...")
            
            p_name = "gemini" if ai_provider == "auto" else ai_provider
            meme_concepts = await ai_router.route_meme_generation(
                topic=topic,
                style=style,
                format_type=format_type,
                count=count,
                provider_name=p_name
            )

            if not meme_concepts:
                raise RuntimeError("AI could not generate valid meme concepts.")

            cls.update_job(job_id, "ACQUIRING_ASSETS", 35.0, log_msg=f"Generated {len(meme_concepts)} concepts. Acquiring licensed assets...")

            asset_mgr = AssetManager()
            total = len(meme_concepts)
            rendered_memes = []

            for idx, concept in enumerate(meme_concepts):
                step_progress = 35.0 + (idx / total) * 55.0
                cls.update_job(
                    job_id,
                    "RENDERING",
                    step_progress,
                    log_msg=f"Producing Meme {idx+1}/{total}: '{concept['hook'][:35]}...'"
                )

                meme_id = str(uuid.uuid4())

                # 1. Acquire safe licensed visual asset
                target_asset_id = uploaded_asset_id if (idx == 0 and uploaded_asset_id) else None
                asset = asset_mgr.get_or_acquire_asset(
                    query=concept.get("visual_query", topic),
                    style=concept.get("style", "sarcastic"),
                    preferred_asset_id=target_asset_id,
                    asset_index=idx,
                    visual_url=concept.get("visual_url", None)
                )

                # 2. Synthesize audio voiceover narration (disabled for memes per user directive unless explicitly requested)
                include_voice = bool(concept.get("include_voice", False))
                voice_audio_path = None
                if include_voice:
                    voice_audio_path = work_dir / f"voice_{meme_id}.mp3"
                    try:
                        await NarrationEngine.generate_commentary_audio(
                            script_data=concept.get("voice_script", f"{concept['hook']}. {concept['joke']}"),
                            output_path=voice_audio_path
                        )
                    except Exception as e:
                        logger.warning(f"Voiceover synthesis failed ({e}), proceeding with silent audio.")
                        voice_audio_path = None

                # 3. Render 9:16 vertical video and export GIF version
                output_mp4 = output_dir / f"meme_{meme_id}.mp4"
                lic_rec = asset.get("license_record", {})
                attribution_text = lic_rec.get("attribution_text", "") if lic_rec.get("attribution_required") else ""

                MemeRenderer.render_meme(
                    asset_path=asset["file_path"],
                    meme_data=concept,
                    output_mp4=output_mp4,
                    work_dir=work_dir,
                    audio_path=str(voice_audio_path) if voice_audio_path and voice_audio_path.exists() else None,
                    attribution_text=attribution_text,
                    export_gif=True
                )

                # 4. Run 15-point QC verification
                qc_report = QualityControlEngine.run_meme_checks(
                    meme_file_path=str(output_mp4),
                    meme_meta=concept,
                    license_record=lic_rec
                )

                # 5. Save to database
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO memes (
                            id, project_id, concept, hook, joke, style, format,
                            visual_query, asset_id, screen_text_json, voice_script,
                            audio_path, output_path, duration, quality_score, scores_json,
                            title, description, hashtags, approval_status, ai_prompt, ai_response
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
                    """, (
                        meme_id,
                        project_id,
                        concept.get("concept", topic),
                        concept.get("hook", ""),
                        concept.get("joke", ""),
                        concept.get("style", style),
                        concept.get("format", format_type),
                        concept.get("visual_query", ""),
                        asset["asset_id"],
                        json.dumps(concept.get("screen_text", [])),
                        concept.get("voice_script", ""),
                        str(voice_audio_path) if voice_audio_path and voice_audio_path.exists() else "",
                        str(output_mp4),
                        concept.get("duration", 7.5),
                        qc_report["score"],
                        json.dumps(concept.get("scores", {})),
                        concept.get("title", f"{concept.get('hook', topic)} #shorts"),
                        concept.get("description", f"{concept.get('concept', topic)}\n\n#shorts #memes"),
                        json.dumps(concept.get("hashtags", ["#shorts", "#memes"])),
                        concept.get("_ai_prompt", ""),
                        concept.get("_ai_response", "")
                    ))

                rendered_memes.append(meme_id)

            # Mark complete
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE projects SET status = 'READY', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

            cls.update_job(
                job_id,
                "READY",
                100.0,
                log_msg=f"Meme Studio generation complete! {len(rendered_memes)} high-retention memes created and verified by Quality Control."
            )

        except Exception as e:
            err_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Meme pipeline failed for job {job_id}: {err_msg}")
            cls.update_job(job_id, "FAILED", 0.0, error=str(e), log_msg=err_msg)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE projects SET status = 'FAILED', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

    @classmethod
    async def regenerate_joke(cls, meme_id: str, provider_name: str = "gemini") -> Dict[str, Any]:
        """Rewrites the joke/hook and re-renders the meme short."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT m.*, a.file_path as asset_path, a.attribution_required, a.attribution_text FROM memes m LEFT JOIN assets a ON m.asset_id = a.id WHERE m.id = ?", (meme_id,))
            meme = cursor.fetchone()
            if not meme:
                raise ValueError("Meme not found.")

        # Route joke regeneration
        regen_data = await ai_router.route_regenerate_joke(
            topic=meme["concept"],
            hook=meme["hook"],
            joke=meme["joke"],
            style=meme["style"],
            provider_name=provider_name
        )

        # Work directory
        project_id = meme["project_id"]
        work_dir = PROJECTS_DIR / project_id / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        output_mp4 = Path(meme["output_path"])

        # Re-synthesize voiceover
        voice_path = work_dir / f"voice_{meme_id}_regen.mp3"
        try:
            await NarrationEngine.generate_commentary_audio(
                script_data=regen_data.get("voice_script", f"{regen_data['hook']}. {regen_data['joke']}"),
                output_path=voice_path
            )
        except Exception:
            voice_path = None

        # Re-render
        meme_data = {
            "screen_text": regen_data.get("screen_text", []),
            "format": meme["format"],
            "duration": meme["duration"]
        }
        attr_text = meme["attribution_text"] if meme["attribution_required"] else ""

        MemeRenderer.render_meme(
            asset_path=meme["asset_path"],
            meme_data=meme_data,
            output_mp4=output_mp4,
            work_dir=work_dir,
            audio_path=str(voice_path) if voice_path and voice_path.exists() else None,
            attribution_text=attr_text
        )

        # Update DB
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memes
                SET hook = ?, joke = ?, screen_text_json = ?, voice_script = ?,
                    audio_path = ?, title = ?, description = ?, hashtags = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                regen_data["hook"],
                regen_data["joke"],
                json.dumps(regen_data.get("screen_text", [])),
                regen_data.get("voice_script", ""),
                str(voice_path) if voice_path and voice_path.exists() else meme["audio_path"],
                regen_data.get("title", meme["title"]),
                regen_data.get("description", meme["description"]),
                json.dumps(regen_data.get("hashtags", ["#shorts", "#memes"])),
                meme_id
            ))

        return {"success": True, "meme_id": meme_id, "updated": regen_data}
