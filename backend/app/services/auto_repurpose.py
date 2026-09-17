import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.config import STORAGE_DIR, PROJECTS_DIR
from backend.app.core.database import get_db_connection
from backend.app.core.logging import logger
from backend.app.video.ingestion import validate_video_source
from backend.app.jobs.queue import job_queue

DOWNLOADS_DIR = STORAGE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

class AutoRepurposeService:
    @staticmethod
    def resolve_video_source(url_or_path: str, rights_status: str) -> Dict[str, Any]:
        """
        Resolves a video from a local file path or downloads from a permitted video URL via yt-dlp.
        Returns validated source metadata and video title.
        """
        url_or_path = url_or_path.strip().strip('"').strip("'")
        is_url = url_or_path.startswith("http://") or url_or_path.startswith("https://") or url_or_path.startswith("www.")

        if is_url:
            logger.info(f"Acquiring video from URL: {url_or_path} ...")
            try:
                from backend.app.video.youtube_downloader import YouTubeDownloader
                dl_result = YouTubeDownloader.extract_metadata_and_download(url_or_path, max_duration_sec=60.0)
                local_path = dl_result["file_path"]
                video_title = dl_result["title"]
            except Exception as e:
                logger.error(f"URL acquisition error: {e}")
                raise RuntimeError(f"Could not acquire permitted video from URL: {str(e)}")
        else:
            local_path = url_or_path
            path_obj = Path(local_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Local video file not found at: {local_path}")
            video_title = path_obj.stem.replace("_", " ").replace("-", " ").title()

        # Validate video file with FFmpeg
        meta = validate_video_source(local_path, rights_status=rights_status)
        meta["resolved_title"] = video_title
        meta["source_url"] = url_or_path if is_url else ""
        return meta

    @classmethod
    def start_pipeline(
        cls,
        url_or_path: str,
        rights_confirmed: bool = True,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        One-click end-to-end orchestration:
        1. Validate rights
        2. Resolve & validate source
        3. Create internal project
        4. Attach source video
        5. Submit job to queue
        6. Return project_id & job_id
        """
        if not rights_confirmed:
            raise ValueError("Content rights confirmation is required to proceed.")

        opts = options or {}
        rights_status = "I own this content" if rights_confirmed else "Not confirmed"

        # 1. Resolve source
        meta = cls.resolve_video_source(url_or_path, rights_status=rights_status)
        title = meta.get("resolved_title", "Repurposed Video")

        # 2. Create Project in DB
        proj_id = str(uuid.uuid4())
        proj_dir = PROJECTS_DIR / proj_id
        proj_dir.mkdir(parents=True, exist_ok=True)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (id, name, description, rights_status, status)
                VALUES (?, ?, ?, ?, 'ANALYZING')
            """, (proj_id, title, f"Auto-generated Shorts for {title}", rights_status))

            # 3. Attach Source in DB
            source_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO sources (
                    id, project_id, file_path, filename, source_url, file_size, duration,
                    width, height, fps, video_codec, audio_codec, audio_channels,
                    audio_sample_rate, rights_status, validated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                source_id, proj_id, meta["file_path"], meta["filename"], meta.get("source_url", ""),
                meta["file_size"], meta["duration"], meta["width"], meta["height"],
                meta["fps"], meta["video_codec"], meta["audio_codec"], meta["audio_channels"],
                meta["audio_sample_rate"], rights_status
            ))

        # 4. Submit Job to Queue
        ai_provider = opts.get("ai_provider", "auto")
        if ai_provider == "auto":
            # Hierarchy: Gemini -> ChatGPT -> DeepSeek (or mock if no browser session configured)
            ai_provider = "gemini"

        job_id = job_queue.submit_project_job(proj_id, ai_provider=ai_provider)

        return {
            "project_id": proj_id,
            "job_id": job_id,
            "title": title,
            "duration": meta.get("duration", 0.0),
            "status": "QUEUED"
        }
