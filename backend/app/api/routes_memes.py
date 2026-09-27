import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse

from backend.app.core.database import get_db_connection
from backend.app.services.meme_pipeline import MemePipelineService
from backend.app.assets.asset_provider import UserUploadProvider

router = APIRouter(prefix="/memes", tags=["memes"])

class MemeGenerateRequest(BaseModel):
    topic: str
    style: str = "sarcastic"
    format: str = "pov"
    count: int = 3
    uploaded_asset_id: Optional[str] = None
    rights_confirmed: bool = True
    ai_provider: str = "auto"

class MemeApproveRequest(BaseModel):
    status: str = "APPROVED"

class RegenerateJokeRequest(BaseModel):
    ai_provider: str = "auto"

@router.post("/generate")
def generate_memes(req: MemeGenerateRequest):
    try:
        res = MemePipelineService.start_pipeline(
            topic=req.topic,
            style=req.style,
            format_type=req.format,
            count=req.count,
            uploaded_asset_id=req.uploaded_asset_id,
            rights_confirmed=req.rights_confirmed,
            ai_provider=req.ai_provider
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/project/{project_id}")
def get_project_memes(project_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        proj = cursor.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

        cursor.execute("""
            SELECT m.*, a.source, a.creator, a.license_name, a.license_url,
                   a.commercial_use, a.modification_allowed, a.attribution_required,
                   a.attribution_text, a.safety_state, a.file_path as asset_path
            FROM memes m
            LEFT JOIN assets a ON m.asset_id = a.id
            WHERE m.project_id = ?
            ORDER BY m.created_at ASC
        """, (project_id,))
        rows = cursor.fetchall()

        memes = []
        for r in rows:
            m_dict = dict(r)
            m_dict["screen_text"] = json.loads(m_dict.get("screen_text_json") or "[]")
            m_dict["scores"] = json.loads(m_dict.get("scores_json") or "{}")
            m_dict["hashtags"] = json.loads(m_dict.get("hashtags") or "[]")
            m_dict["video_url"] = f"/api/memes/video/{m_dict['id']}" if m_dict.get("output_path") else ""
            m_dict["gif_url"] = f"/api/memes/gif/{m_dict['id']}" if m_dict.get("output_path") else ""
            m_dict["license_record"] = {
                "source": m_dict.get("source", "unknown"),
                "creator": m_dict.get("creator", "Unknown"),
                "license_name": m_dict.get("license_name", "UNKNOWN"),
                "license_url": m_dict.get("license_url", ""),
                "commercial_use": bool(m_dict.get("commercial_use", 0)),
                "modification_allowed": bool(m_dict.get("modification_allowed", 0)),
                "attribution_required": bool(m_dict.get("attribution_required", 0)),
                "attribution_text": m_dict.get("attribution_text", ""),
                "safety_state": m_dict.get("safety_state", "VERIFIED_SAFE")
            }
            memes.append(m_dict)

        return {
            "project": dict(proj),
            "memes": memes
        }

@router.get("/status/{job_id}")
def get_meme_job_status(job_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_dict = dict(job)
        return {
            "job_id": job_dict["id"],
            "project_id": job_dict["project_id"],
            "status": job_dict["status"],
            "progress": job_dict["progress"],
            "error_message": job_dict.get("error_message", ""),
            "logs": job_dict.get("logs", "")
        }

@router.post("/{meme_id}/regenerate_joke")
async def regenerate_meme_joke(meme_id: str, req: RegenerateJokeRequest):
    try:
        res = await MemePipelineService.regenerate_joke(
            meme_id=meme_id,
            provider_name="gemini" if req.ai_provider == "auto" else req.ai_provider
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{meme_id}/approve")
def set_meme_approval(meme_id: str, req: MemeApproveRequest):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memes WHERE id = ?", (meme_id,))
        meme = cursor.fetchone()
        if not meme:
            raise HTTPException(status_code=404, detail="Meme not found")

        cursor.execute("UPDATE memes SET approval_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (req.status, meme_id))
        return {"status": req.status, "meme_id": meme_id}

@router.post("/upload_image")
async def upload_meme_image(
    file: UploadFile = File(...),
    rights_confirmed: bool = Form(...)
):
    if not rights_confirmed:
        raise HTTPException(status_code=400, detail="You must confirm you have the rights to use this image.")

    content = await file.read()
    try:
        res = UserUploadProvider.save_upload(
            file_bytes=content,
            filename=file.filename,
            rights_confirmed=rights_confirmed
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/{meme_id}")
def stream_meme_video(meme_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT output_path FROM memes WHERE id = ?", (meme_id,))
        row = cursor.fetchone()
        if not row or not row["output_path"]:
            raise HTTPException(status_code=404, detail="Video not found")

    p = Path(row["output_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="Video file does not exist on disk")

    return FileResponse(
        path=str(p),
        media_type="video/mp4",
        filename=f"meme_{meme_id[:8]}.mp4"
    )

@router.get("/gif/{meme_id}")
def stream_meme_gif(meme_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT output_path FROM memes WHERE id = ?", (meme_id,))
        row = cursor.fetchone()
        if not row or not row["output_path"]:
            raise HTTPException(status_code=404, detail="Meme not found")

    p = Path(row["output_path"]).with_suffix(".gif")
    if not p.exists():
        p = Path(row["output_path"])
        if not p.exists():
            raise HTTPException(status_code=404, detail="Meme file does not exist on disk")

    media_type = "image/gif" if p.suffix.lower() == ".gif" else "video/mp4"
    return FileResponse(
        path=str(p),
        media_type=media_type,
        filename=f"meme_{meme_id[:8]}{p.suffix}"
    )
