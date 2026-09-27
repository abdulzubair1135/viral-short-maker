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
    audience: str = Field("not_made_for_kids", description="'made_for_kids' or 'not_made_for_kids'")
    visibility: str = Field("public", description="'private', 'unlisted', or 'public'")

class MultiPlatformPublishRequest(BaseModel):
    item_id: str
    item_type: str = Field("clip", description="'clip' or 'meme'")
    platform: str = Field("both", description="'youtube', 'facebook', or 'both'")
    title: str
    description: str
    hashtags: List[str]
    audience: str = Field("not_made_for_kids", description="'made_for_kids' or 'not_made_for_kids'")
    visibility: str = Field("public", description="'private', 'unlisted', or 'public'")

@router.post("/publish_preparation")
def prepare_youtube_publish(req: YouTubePublishPrepRequest):
    """
    Validates upload preparation for a generated Short / Reel.
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
            # Check memes table fallback
            cursor.execute("SELECT * FROM memes WHERE id = ?", (req.clip_id,))
            clip = cursor.fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Item not found")

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
    Executes upload to YouTube Studio.
    """
    from backend.app.publishing.youtube_api import YouTubeApiService
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
        item = cursor.fetchone()
        if not item:
            cursor.execute("SELECT * FROM memes WHERE id = ?", (req.clip_id,))
            item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        output_path = item["output_path"]

    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=400, detail="Video file has not been rendered to disk yet.")

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

@router.post("/publish_multi_platform")
async def execute_multi_platform_upload(req: MultiPlatformPublishRequest):
    """
    Executes automated publishing to YouTube, Facebook, or BOTH simultaneously.
    """
    from backend.app.publishing.youtube_api import YouTubeApiService
    from backend.app.publishing.facebook_api import FacebookApiService

    from pathlib import Path

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if req.item_type == "meme":
            cursor.execute("SELECT * FROM memes WHERE id = ?", (req.item_id,))
        else:
            cursor.execute("SELECT * FROM clips WHERE id = ?", (req.item_id,))
        item = cursor.fetchone()
        if not item:
            # Fallback search across both tables
            cursor.execute("SELECT * FROM clips WHERE id = ?", (req.item_id,))
            item = cursor.fetchone()
            if not item:
                cursor.execute("SELECT * FROM memes WHERE id = ?", (req.item_id,))
                item = cursor.fetchone()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found in clips or memes DB.")
        output_path = item["output_path"]

    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=400, detail="Video file has not been rendered to disk yet.")

    results = {}
    errors = []

    # 1. YouTube Upload
    if req.platform in ("youtube", "both"):
        try:
            yt_res = await YouTubeApiService.upload_short(
                clip_id=req.item_id,
                file_path=output_path,
                title=req.title,
                description=req.description,
                hashtags=req.hashtags,
                audience=req.audience,
                visibility=req.visibility
            )
            results["youtube"] = yt_res
        except Exception as e:
            logger.error(f"YouTube publishing failed: {e}")
            errors.append(f"YouTube: {str(e)}")

    # 2. Facebook Upload
    if req.platform in ("facebook", "both"):
        try:
            fb_res = await FacebookApiService.upload_reel(
                clip_id=req.item_id,
                file_path=output_path,
                title=req.title,
                description=req.description,
                hashtags=req.hashtags,
                visibility=req.visibility
            )
            results["facebook"] = fb_res
        except Exception as e:
            logger.error(f"Facebook publishing failed: {e}")
            errors.append(f"Facebook: {str(e)}")

    if not results and errors:
        raise HTTPException(status_code=500, detail=" Publishing failed on all selected platforms: " + " | ".join(errors))

    return {
        "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
        "platform_requested": req.platform,
        "results": results,
        "errors": errors
    }



