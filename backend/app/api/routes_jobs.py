from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.core.database import get_db_connection
from backend.app.jobs.queue import job_queue
from backend.app.jobs.checkpoint import CheckpointManager

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/start_pipeline")
async def start_pipeline(payload: Dict[str, Any]):
    project_id = payload.get("project_id")
    ai_provider = payload.get("ai_provider", "mock")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    import asyncio
    job_queue.loop = asyncio.get_running_loop()
    job_id = job_queue.submit_project_job(project_id, ai_provider=ai_provider)
    return {"job_id": job_id, "status": "QUEUED"}

@router.get("/")
def list_jobs(project_id: Optional[str] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if project_id:
            cursor.execute("SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
        else:
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 30")
        return [dict(r) for r in cursor.fetchall()]

@router.get("/{job_id}")
def get_job(job_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return dict(row)

@router.post("/{job_id}/resume")
def resume_job(job_id: str, payload: Optional[Dict[str, Any]] = None):
    """Resume a failed or interrupted job from its last valid checkpoint."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT project_id FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        project_id = row["project_id"]

    new_provider = (payload or {}).get("ai_provider", "mock")
    new_job_id = job_queue.submit_project_job(project_id, ai_provider=new_provider)
    return {"status": "resumed", "new_job_id": new_job_id, "resumed_from_job": job_id}
