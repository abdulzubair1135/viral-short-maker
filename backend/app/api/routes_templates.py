import uuid
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.core.database import get_db_connection

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/")
def list_templates():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY is_default DESC, name ASC")
        rows = cursor.fetchall()
        templates = []
        for r in rows:
            t = dict(r)
            t["audio_settings"] = json.loads(t.get("audio_settings") or "{}")
            t["effects_settings"] = json.loads(t.get("effects_settings") or "{}")
            t["is_default"] = bool(t.get("is_default"))
            templates.append(t)
        return templates

@router.post("/")
def create_template(payload: Dict[str, Any]):
    t_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO templates (
                id, name, description, is_default, aspect_ratio, resolution,
                caption_preset, font_name, font_size, crop_mode, audio_settings, effects_settings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t_id, payload["name"], payload.get("description", ""),
            1 if payload.get("is_default") else 0,
            payload.get("aspect_ratio", "9:16"),
            payload.get("resolution", "1080x1920"),
            payload.get("caption_preset", "dynamic"),
            payload.get("font_name", "Arial"),
            payload.get("font_size", 24),
            payload.get("crop_mode", "speaker_tracking"),
            json.dumps(payload.get("audio_settings", {})),
            json.dumps(payload.get("effects_settings", {}))
        ))
    return {"id": t_id, "status": "created"}
