import asyncio
from typing import Dict, Any, List
from backend.app.browser.facebook_uploader import FacebookUploader
from backend.app.core.logging import logger

class FacebookApiService:
    @classmethod
    async def upload_reel(
        cls,
        clip_id: str,
        file_path: str,
        title: str,
        description: str,
        hashtags: List[str],
        visibility: str = "public"
    ) -> Dict[str, Any]:
        """Publishes a short or meme directly to Facebook Reels using browser automation."""
        try:
            res = await FacebookUploader.upload_reel(
                clip_id=clip_id,
                file_path=file_path,
                title=title,
                description=description,
                hashtags=hashtags,
                visibility=visibility
            )
            return res
        except Exception as e:
            logger.error(f"Facebook Reel upload failed for clip {clip_id}: {e}")
            raise RuntimeError(f"Facebook upload error: {str(e)}")
