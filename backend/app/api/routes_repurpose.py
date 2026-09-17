import json
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.core.database import get_db_connection
from backend.app.services.auto_repurpose import AutoRepurposeService

router = APIRouter(prefix="/repurpose", tags=["repurpose"])

class RepurposeRequest(BaseModel):
    url_or_path: str = Field(..., min_length=1)
    rights_confirmed: bool = Field(..., description="User confirmation of content rights")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

HUMAN_STAGE_TRANSLATIONS = {
    "QUEUED": "Starting repurposing studio engine...",
    "VALIDATING": "Validating video audio and video streams...",
    "TRANSCRIBING": "Transcribing speech with word timestamps...",
    "ANALYZING": "AI finding best viral moments from transcript...",
    "GENERATING_CLIPS": "Optimizing boundaries & selecting quality moments...",
    "RENDERING": "Creating 9:16 Shorts with dynamic captions...",
    "QUALITY_CHECK": "Checking final quality with 15-point inspection...",
    "READY": "Your Shorts are ready!",
    "FAILED": "Processing encountered an issue"
}

@router.post("")
@router.post("/")
async def repurpose_video(req: RepurposeRequest):
    """
    Primary One-Click Endpoint:
    Accepts video URL or local file path, validates rights, automatically
    creates project, transcribes, analyzes with browser AI, reframes to 9:16,
    burns dynamic captions, and runs quality checks.
    """
    if not req.rights_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Content rights confirmation is required before repurposing video."
        )

    try:
        import asyncio
        from backend.app.jobs.queue import job_queue
        job_queue.loop = asyncio.get_running_loop()

        res = await asyncio.to_thread(
            AutoRepurposeService.start_pipeline,
            url_or_path=req.url_or_path,
            rights_confirmed=req.rights_confirmed,
            options=req.options
        )
        return res
    except Exception as e:
        logger.error(f"Error starting pipeline: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{job_id}")
def get_repurpose_status(job_id: str):
    """
    Polls real-time progress for the one-click workflow.
    Returns human-friendly stage messages, progress percentage, and finished clips once ready.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        project_id = job["project_id"]
        status = job["status"]
        progress = job["progress"]
        stage = job["checkpoint_stage"] or status

        human_msg = HUMAN_STAGE_TRANSLATIONS.get(stage, HUMAN_STAGE_TRANSLATIONS.get(status, "Processing video..."))

        # If completed, fetch all rendered clips & rejected candidates
        clips = []
        rejected = []
        if status in ("READY", "CANDIDATE"):
            cursor.execute("SELECT * FROM clips WHERE project_id = ? ORDER BY score_total DESC", (project_id,))
            for r in cursor.fetchall():
                c = dict(r)
                c["scores"] = json.loads(c.get("scores_json") or "{}")
                c["hashtags"] = json.loads(c.get("hashtags") or "[]")
                c["keywords"] = json.loads(c.get("keywords") or "[]")
                c["tags"] = json.loads(c.get("tags") or "[]")
                c["analysis"] = json.loads(c.get("analysis_json") or "{}")
                c["narration_script"] = json.loads(c.get("script_json") or "[]")
                clips.append(c)

            cursor.execute("SELECT * FROM rejected_candidates WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
            for r in cursor.fetchall():
                rj = dict(r)
                rj["scores"] = json.loads(rj.get("scores_json") or "{}")
                rejected.append(rj)

        return {
            "job_id": job_id,
            "project_id": project_id,
            "status": status,
            "progress": progress,
            "stage": stage,
            "human_message": human_msg,
            "error_message": job["error_message"],
            "clips": clips,
            "rejected_candidates": rejected,
            "short_count": len(clips),
            "rejected_count": len(rejected)
        }

@router.get("/rejected/{project_id}")
def get_rejected_candidates(project_id: str):
    """Returns all candidate moments rejected by AI with detailed reasons."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rejected_candidates WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
        rows = cursor.fetchall()
        rejected = []
        for r in rows:
            item = dict(r)
            item["scores"] = json.loads(item.get("scores_json") or "{}")
            rejected.append(item)
        return {"project_id": project_id, "rejected_candidates": rejected}


class YouTubePublishPrepRequest(BaseModel):
    clip_id: str
    title: str
    description: str
    hashtags: List[str]
    audience: str = Field(..., description="'made_for_kids' or 'not_made_for_kids'")
    visibility: str = Field("private", description="'private', 'unlisted', or 'public'")

@router.post("/publish_preparation")
def prepare_youtube_publish(req: YouTubePublishPrepRequest):
    """
    Validates YouTube upload preparation for a generated Short.
    Requires explicit audience confirmation ('made_for_kids' or 'not_made_for_kids').
    """
    if req.audience not in ("made_for_kids", "not_made_for_kids"):
        raise HTTPException(
            status_code=400,
            detail="Audience must be explicitly confirmed as 'made_for_kids' or 'not_made_for_kids'."
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
        clip = cursor.fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

        cursor.execute("""
            UPDATE clips 
            SET title = ?, description = ?, hashtags = ?
            WHERE id = ?
        """, (req.title, req.description, json.dumps(req.hashtags), req.clip_id))

    return {
        "status": "prepared",
        "clip_id": req.clip_id,
        "title": req.title,
        "visibility": req.visibility,
        "audience": req.audience,
        "ready_for_upload": True
    }

@router.post("/publish_upload")
async def execute_youtube_upload(req: YouTubePublishPrepRequest):
    """
    Executes real-time upload of the generated Short to YouTube Studio
    via the authenticated Chrome browser session.
    """
    if req.audience not in ("made_for_kids", "not_made_for_kids"):
        raise HTTPException(
            status_code=400,
            detail="Audience must be explicitly confirmed as 'made_for_kids' or 'not_made_for_kids'."
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
        clip = cursor.fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        output_path = clip["output_path"]

    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=400, detail="Clip video file has not been rendered to disk yet.")

    from backend.app.publishing.youtube_api import YouTubeApiService
    try:
        res = await YouTubeApiService.upload_short(
            clip_id=req.clip_id,
            file_path=output_path,
            title=req.title,
            description=req.description,
            hashtags=req.hashtags,
            audience=req.audience,
            visibility=req.visibility
        )
        return res
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube upload error: {str(e)}")


