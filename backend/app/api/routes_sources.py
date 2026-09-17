import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.app.core.database import get_db_connection
from backend.app.config import PROJECTS_DIR
from backend.app.video.ingestion import validate_video_source
from backend.app.core.security import check_rights_permission

router = APIRouter(prefix="/sources", tags=["sources"])

@router.post("/attach_local")
def attach_local_source(
    project_id: str = Form(...),
    file_path: str = Form(...),
    rights_status: str = Form("Not confirmed")
):
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Source video file not found at: {file_path}")

    try:
        meta = validate_video_source(str(path), rights_status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    source_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sources (
                id, project_id, file_path, filename, file_size, duration,
                width, height, fps, video_codec, audio_codec, audio_channels,
                audio_sample_rate, rights_status, validated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            source_id, project_id, meta["file_path"], meta["filename"],
            meta["file_size"], meta["duration"], meta["width"], meta["height"],
            meta["fps"], meta["video_codec"], meta["audio_codec"], meta["audio_channels"],
            meta["audio_sample_rate"], rights_status
        ))

        # Update project rights status
        cursor.execute("UPDATE projects SET rights_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (rights_status, project_id))

    return {"status": "attached", "source_id": source_id, "meta": meta}

@router.post("/upload")
async def upload_source_video(
    project_id: str = Form(...),
    rights_status: str = Form("Not confirmed"),
    file: UploadFile = File(...)
):
    proj_dir = PROJECTS_DIR / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)
    target_path = proj_dir / file.filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        meta = validate_video_source(str(target_path), rights_status)
    except Exception as e:
        if target_path.exists(): target_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))

    source_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sources (
                id, project_id, file_path, filename, file_size, duration,
                width, height, fps, video_codec, audio_codec, audio_channels,
                audio_sample_rate, rights_status, validated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            source_id, project_id, str(target_path), file.filename,
            meta["file_size"], meta["duration"], meta["width"], meta["height"],
            meta["fps"], meta["video_codec"], meta["audio_codec"], meta["audio_channels"],
            meta["audio_sample_rate"], rights_status
        ))
        cursor.execute("UPDATE projects SET rights_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (rights_status, project_id))

    return {"status": "uploaded", "source_id": source_id, "meta": meta}
