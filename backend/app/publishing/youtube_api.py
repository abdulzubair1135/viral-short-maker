import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.core.database import get_db_connection
from backend.app.core.logging import logger

class YouTubeApiService:
    @classmethod
    def get_connection_status(cls) -> Dict[str, Any]:
        """Checks if a YouTube channel is authenticated via OAuth / Data API."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM youtube_auth WHERE id = 'primary'")
            row = cursor.fetchone()
            if not row or not row["is_authenticated"]:
                return {
                    "is_authenticated": False,
                    "channel_title": "",
                    "channel_id": "",
                    "thumbnail_url": "",
                    "message": "Not connected to YouTube Data API (Browser Studio upload available)"
                }
            return {
                "is_authenticated": True,
                "channel_title": row["channel_title"],
                "channel_id": row["channel_id"],
                "thumbnail_url": row["thumbnail_url"],
                "message": f"Connected to {row['channel_title']}"
            }

    @classmethod
    def save_connection(cls, channel_id: str, channel_title: str, credentials_dict: Dict[str, Any], thumbnail_url: str = ""):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO youtube_auth (id, channel_id, channel_title, credentials_json, is_authenticated, thumbnail_url, updated_at)
                VALUES ('primary', ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            """, (channel_id, channel_title, json.dumps(credentials_dict), thumbnail_url))

    @classmethod
    async def upload_short(
        cls,
        clip_id: str,
        file_path: str,
        title: str,
        description: str,
        hashtags: List[str],
        audience: str = "not_made_for_kids",
        visibility: str = "private"
    ) -> Dict[str, Any]:
        """
        Uploads Short via YouTube Data API v3 if OAuth connected,
        otherwise falls back to Chrome CDP browser session.
        """
        if audience not in ("made_for_kids", "not_made_for_kids"):
            raise ValueError("Audience must be explicitly confirmed as 'made_for_kids' or 'not_made_for_kids'.")

        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Video file not found at: {file_path}")

        status = cls.get_connection_status()

        if status["is_authenticated"]:
            # Official Google Data API v3 upload
            logger.info("Executing upload via official YouTube Data API v3...")
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credentials_json FROM youtube_auth WHERE id = 'primary'")
                row = cursor.fetchone()
                creds_data = json.loads(row["credentials_json"])

            creds = Credentials.from_authorized_user_info(creds_data)
            youtube = build("youtube", "v3", credentials=creds)

            full_title = title if "#shorts" in title.lower() else f"{title} #Shorts"
            full_title = full_title[:100]

            tags = [t.replace("#", "") for t in hashtags] if hashtags else ["shorts", "review"]
            body = {
                "snippet": {
                    "title": full_title,
                    "description": f"{description}\n\n{' '.join(hashtags)}".strip(),
                    "tags": tags,
                    "categoryId": "22"  # People & Blogs / Entertainment
                },
                "status": {
                    "privacyStatus": visibility,
                    "selfDeclaredMadeForKids": (audience == "made_for_kids")
                }
            }

            media = MediaFileUpload(str(path_obj.resolve()), mimetype="video/mp4", resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = None
            while response is None:
                _, response = request.next_chunk()

            video_id = response.get("id")
            video_url = f"https://youtube.com/shorts/{video_id}"
            return {
                "success": True,
                "provider": "youtube_api_v3",
                "video_id": video_id,
                "video_url": video_url,
                "visibility": visibility,
                "audience": audience
            }
        else:
            # Fallback to authenticated Chrome CDP session
            logger.info("YouTube Data API not configured. Routing upload via Chrome Studio session...")
            from backend.app.browser.youtube_uploader import YouTubeUploader
            return await YouTubeUploader.upload_short(
                clip_id=clip_id,
                file_path=file_path,
                title=title,
                description=description,
                hashtags=hashtags,
                audience=audience,
                visibility=visibility
            )
