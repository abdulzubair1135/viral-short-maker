import json
from fastapi import APIRouter, HTTPException, Response
from backend.app.core.database import get_db_connection
from backend.app.video.transcription import generate_srt

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

@router.get("/{project_id}")
def get_transcript(project_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcripts WHERE project_id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No transcript found for project")

        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "language": row["language"],
            "full_text": row["full_text"],
            "srt_content": row["srt_content"],
            "segments": json.loads(row["segments_json"] or "[]"),
            "words": json.loads(row["words_json"] or "[]")
        }

@router.put("/{project_id}/segments")
def update_transcript_segments(project_id: str, payload: dict):
    segments = payload.get("segments", [])
    full_text = " ".join([s["text"] for s in segments])
    new_srt = generate_srt(segments)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transcripts 
            SET full_text = ?, srt_content = ?, segments_json = ?
            WHERE project_id = ?
        """, (full_text, new_srt, json.dumps(segments), project_id))

    return {"status": "updated", "segments_count": len(segments)}

@router.get("/{project_id}/export_srt")
def export_srt_file(project_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT srt_content FROM transcripts WHERE project_id = ?", (project_id,))
        row = cursor.fetchone()
        if not row or not row["srt_content"]:
            raise HTTPException(status_code=404, detail="Transcript not ready")

    return Response(
        content=row["srt_content"],
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=transcript_{project_id}.srt"}
    )
