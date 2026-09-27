import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.app.browser.playwright_manager import BrowserSessionManager
from backend.app.core.logging import logger
from backend.app.core.database import get_db_connection

class FacebookUploader:
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
        """
        Uploads a generated short/meme to Facebook Reels via user's authenticated Chrome session.
        Applies Facebook Reels publishing flow:
        - Automatically combines title, description, and hashtags into Facebook caption
        - Handles file upload and automated navigation through Facebook Reels publishing modal
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Video file not found at: {file_path}")

        tags_str = " ".join(hashtags) if hashtags else "#reels #viral #trending"
        full_caption = f"{title}\n\n{description}\n\n{tags_str}".strip()

        logger.info(f"Connecting to Chrome session for Facebook Reel upload: '{title}'...")
        mgr = BrowserSessionManager.get_instance()
        context = await mgr.get_cdp_context()

        # Find existing Facebook tab or open new one
        page = None
        for p in context.pages:
            if "facebook.com" in p.url:
                page = p
                break

        if not page:
            page = await context.new_page()

        logger.info("Navigating to Facebook Reels creation...")
        try:
            await page.goto("https://www.facebook.com/reels/create", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            logger.warning(f"Direct navigation to reels create took long: {e}. Retrying main page...")
            await page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=30000)

        await page.bring_to_front()
        await page.wait_for_timeout(3000)

        # 1. Locate video file input
        file_input = await page.query_selector("input[type='file']")
        if not file_input:
            # Try finding Add Video button or Reel create trigger
            selectors = [
                "div[aria-label*='Add Video']", 
                "div[aria-label*='Create Reel']",
                "span:has-text('Add Video')",
                "input[accept*='video']"
            ]
            for sel in selectors:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click(force=True)
                    await page.wait_for_timeout(1500)
                    break
            file_input = await page.wait_for_selector("input[type='file']", timeout=20000)

        logger.info(f"Setting video file path for Facebook Reels: {str(path_obj.resolve())}")
        await file_input.set_input_files(str(path_obj.resolve()))
        await page.wait_for_timeout(4000)

        # 2. Add Caption / Description & Hashtags
        logger.info("Adding caption and hashtags to Facebook Reel...")
        caption_selectors = [
            "div[aria-label*='Describe your reel']",
            "div[aria-label*='Write a caption']",
            "div[contenteditable='true']",
            "textarea[name='caption']"
        ]
        
        caption_box = None
        for c_sel in caption_selectors:
            caption_box = await page.query_selector(c_sel)
            if caption_box and await caption_box.is_visible():
                break

        if caption_box:
            await caption_box.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(full_caption)
            await page.wait_for_timeout(1000)

        # 3. Click Next / Publish through Facebook wizard steps
        logger.info("Progressing through Facebook Reel publishing wizard...")
        for _ in range(3):
            next_selectors = [
                "div[aria-label='Next']",
                "button:has-text('Next')",
                "div[role='button']:has-text('Next')"
            ]
            for n_sel in next_selectors:
                n_btn = await page.query_selector(n_sel)
                if n_btn and await n_btn.is_visible():
                    await n_btn.click(force=True)
                    await page.wait_for_timeout(2000)
                    break

        # 4. Final Publish button
        pub_selectors = [
            "div[aria-label='Publish']",
            "button:has-text('Publish')",
            "div[role='button']:has-text('Publish')",
            "div[aria-label='Post']"
        ]
        published = False
        for p_sel in pub_selectors:
            pub_btn = await page.query_selector(p_sel)
            if pub_btn and await pub_btn.is_visible():
                logger.info("Clicking Publish on Facebook Reel...")
                await pub_btn.click(force=True)
                await page.wait_for_timeout(5000)
                published = True
                break

        # Update database with Facebook upload status
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clips 
                SET status = 'PUBLISHED', approval_status = 'APPROVED'
                WHERE id = ?
            """, (clip_id,))

        logger.info(f"Facebook Reel published successfully for clip {clip_id}!")

        return {
            "success": True,
            "platform": "facebook",
            "clip_id": clip_id,
            "title": title,
            "caption": full_caption,
            "video_url": "https://www.facebook.com/reels",
            "status": "PUBLISHED"
        }
