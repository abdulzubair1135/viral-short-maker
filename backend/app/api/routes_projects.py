import uuid
import json
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional
from backend.app.core.database import get_db_connection
from backend.app.models.schemas import ProjectCreate, ProjectUpdate
from backend.app.config import PROJECTS_DIR
from backend.app.core.security import check_rights_permission

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("")
@router.get("/")
def list_projects(
    search: Optional[str] = None,
    status: Optional[str] = None,
    archived: bool = False,
    sort_by: str = "newest"
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM projects WHERE archived = ?"
        params = [1 if archived else 0]

        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        if status:
            query += " AND status = ?"
            params.append(status)

        if sort_by == "newest":
            query += " ORDER BY created_at DESC"
        elif sort_by == "oldest":
            query += " ORDER BY created_at ASC"
        elif sort_by == "name":
            query += " ORDER BY name ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            p_dict = dict(r)
            p_dict["tags"] = json.loads(p_dict.get("tags") or "[]")
            p_dict["settings"] = json.loads(p_dict.get("settings") or "{}")

            # Get generated clips count
            cursor.execute("SELECT COUNT(*) as cnt FROM clips WHERE project_id = ?", (p_dict["id"],))
            c_cnt = cursor.fetchone()
            p_dict["clip_count"] = c_cnt["cnt"] if c_cnt else 0

            # Get generated memes count
            cursor.execute("SELECT COUNT(*) as cnt FROM memes WHERE project_id = ?", (p_dict["id"],))
            m_cnt = cursor.fetchone()
            p_dict["meme_count"] = m_cnt["cnt"] if m_cnt else 0

            # Get source video metadata (duration, filename)
            cursor.execute("SELECT duration, filename FROM sources WHERE project_id = ? ORDER BY created_at DESC LIMIT 1", (p_dict["id"],))
            s_row = cursor.fetchone()
            if s_row:
                p_dict["source"] = dict(s_row)

            projects.append(p_dict)
        return projects


@router.post("/")
def create_project(data: ProjectCreate):
    proj_id = str(uuid.uuid4())
    proj_dir = PROJECTS_DIR / proj_id
    proj_dir.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (id, name, description, rights_status, tags, settings, status)
            VALUES (?, ?, ?, ?, ?, ?, 'DRAFT')
        """, (
            proj_id, data.name, data.description or "",
            data.rights_status, json.dumps(data.tags), json.dumps(data.settings)
        ))

    return {"id": proj_id, "name": data.name, "status": "DRAFT", "rights_status": data.rights_status}

@router.get("/{project_id}")
def get_project(project_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        p = dict(row)
        p["tags"] = json.loads(p.get("tags") or "[]")
        p["settings"] = json.loads(p.get("settings") or "{}")

        # Include source video if present
        cursor.execute("SELECT * FROM sources WHERE project_id = ? ORDER BY created_at DESC LIMIT 1", (project_id,))
        src = cursor.fetchone()
        p["source"] = dict(src) if src else None

        # Include clip count
        cursor.execute("SELECT count(*) as count FROM clips WHERE project_id = ?", (project_id,))
        p["clip_count"] = cursor.fetchone()["count"]

        return p

@router.put("/{project_id}")
def update_project(project_id: str, data: ProjectUpdate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        updates = []
        params = []
        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)
        if data.rights_status is not None:
            updates.append("rights_status = ?")
            params.append(data.rights_status)
        if data.tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(data.tags))
        if data.settings is not None:
            updates.append("settings = ?")
            params.append(json.dumps(data.settings))
        if data.archived is not None:
            updates.append("archived = ?")
            params.append(1 if data.archived else 0)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
            params.append(project_id)
            cursor.execute(sql, params)

    return {"status": "updated", "id": project_id}

@router.delete("/{project_id}")
def delete_project(project_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    return {"status": "deleted", "id": project_id}

@router.post("/{project_id}/duplicate")
def duplicate_project(project_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        orig = cursor.fetchone()
        if not orig:
            raise HTTPException(status_code=404, detail="Original project not found")

        new_id = str(uuid.uuid4())
        new_name = f"{orig['name']} (Copy)"
        cursor.execute("""
            INSERT INTO projects (id, name, description, rights_status, tags, settings, status)
            VALUES (?, ?, ?, ?, ?, ?, 'DRAFT')
        """, (
            new_id, new_name, orig["description"], orig["rights_status"],
            orig["tags"], orig["settings"]
        ))
        return {"id": new_id, "name": new_name}

@router.get("/{project_id}/export_bundle")
def export_project_bundle(project_id: str):
    """Export project metadata, edit plans, transcripts, and settings into a portable .acs zip bundle."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        proj = cursor.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

        cursor.execute("SELECT * FROM clips WHERE project_id = ?", (project_id,))
        clips = [dict(c) for c in cursor.fetchall()]

        cursor.execute("SELECT * FROM transcripts WHERE project_id = ?", (project_id,))
        transcript = cursor.fetchone()

        bundle_data = {
            "project": dict(proj),
            "clips": clips,
            "transcript": dict(transcript) if transcript else None,
            "version": "1.0.0"
        }

    proj_dir = PROJECTS_DIR / project_id
    bundle_path = proj_dir / f"{proj['name'].replace(' ', '_')}.acs"

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(bundle_data, indent=2))

    return FileResponse(
        path=str(bundle_path),
        filename=bundle_path.name,
        media_type="application/zip"
    )
