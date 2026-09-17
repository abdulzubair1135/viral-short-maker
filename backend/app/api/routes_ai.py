import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.app.core.database import get_db_connection
from backend.app.ai.router.ai_router import ai_router

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/providers")
async def get_providers_status():
    """Returns availability and human-intervention readiness of all AI providers."""
    return await ai_router.get_all_statuses()

@router.get("/jobs")
def get_ai_jobs(project_id: Optional[str] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if project_id:
            cursor.execute("SELECT * FROM ai_jobs WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
        else:
            cursor.execute("SELECT * FROM ai_jobs ORDER BY created_at DESC LIMIT 50")
        return [dict(r) for r in cursor.fetchall()]

@router.get("/prompts")
def list_prompts():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompt_templates ORDER BY category, name")
        return [dict(r) for r in cursor.fetchall()]

@router.post("/prompts")
def create_prompt(payload: Dict[str, Any]):
    p_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prompt_templates (id, category, name, description, prompt_text, is_default, version)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            p_id, payload.get("category", "Custom"), payload["name"],
            payload.get("description", ""), payload["prompt_text"],
            1 if payload.get("is_default") else 0
        ))
    return {"id": p_id, "status": "created"}

class MetadataSuggestionRequest(BaseModel):
    clip_id: Optional[str] = None
    title: Optional[str] = "Viral YouTube Short"
    transcript: Optional[str] = None
    style: str = "Viral Hook & Curiosity"
    provider: str = "gemini"

@router.post("/suggest_metadata")
async def suggest_metadata_endpoint(req: MetadataSuggestionRequest):
    """
    Asks Gemini or DeepSeek browser AI to suggest high-performing titles,
    rich descriptions, and trending hashtags based on the Short's content.
    """
    clip_title = req.title or "Viral YouTube Short"
    clip_transcript = req.transcript or ""

    if req.clip_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
            clip = cursor.fetchone()
            if clip:
                clip_title = clip["title"] or clip_title
                clip_transcript = clip["hook"] or clip["summary"] or clip_transcript

    res = await ai_router.generate_metadata_suggestions(
        transcript_snippet=clip_transcript,
        video_title=clip_title,
        style_preference=req.style,
        provider_name=req.provider
    )
    return res

