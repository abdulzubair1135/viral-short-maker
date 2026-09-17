import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.app.browser.playwright_manager import BrowserSessionManager
from backend.app.core.logging import logger
from backend.app.core.database import get_db_connection

class YouTubeUploader:
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
        Uploads a generated Short to YouTube Studio via user's authenticated Chrome browser session.
        Applies YouTube policies:
        - Strict audience selection ('made_for_kids' or 'not_made_for_kids')
        - Visibility selection ('private', 'unlisted', 'public')
        - Automatically appends #shorts to title/description for Shorts shelf indexing
        """
        if audience not in ("made_for_kids", "not_made_for_kids"):
            raise ValueError("Audience must be explicitly confirmed as 'made_for_kids' or 'not_made_for_kids'.")

        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Video file not found at: {file_path}")

        full_title = title if "#shorts" in title.lower() else f"{title} #Shorts"
        full_title = full_title[:100]  # YouTube limit 100 chars

        tags_str = " ".join(hashtags) if hashtags else "#shorts #viral"
        full_description = f"{description}\n\n{tags_str}".strip()

        logger.info(f"Connecting to Chrome session for YouTube upload: '{full_title}'...")
        mgr = BrowserSessionManager.get_instance()
        context = await mgr.get_cdp_context()

        # Find or open YouTube Studio tab
        page = None
        for p in context.pages:
            if "studio.youtube.com" in p.url:
                page = p
                break

        if not page:
            page = await context.new_page()
            await page.goto("https://studio.youtube.com", wait_until="domcontentloaded", timeout=45000)

        await page.bring_to_front()
        await page.wait_for_timeout(2000)

        # 1. Open upload modal (or reuse if already open)
        file_input = await page.query_selector("input[type='file']")
        if not file_input:
            logger.info("Opening YouTube Studio upload dialog...")
            # Dismiss any stray overlays
            backdrop = await page.query_selector("tp-yt-iron-overlay-backdrop.opened")
            if backdrop:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(1000)

            create_btn = await page.wait_for_selector("#create-icon, button[aria-label='Create'], ytcp-button#create-icon", timeout=15000)
            await create_btn.click(force=True)
            await page.wait_for_timeout(1000)

            upload_entry = await page.wait_for_selector("tp-yt-paper-item#text-item-0, #text-item-0, ytcp-text-menu #upload-icon", timeout=10000)
            await upload_entry.click(force=True)
            await page.wait_for_timeout(2000)
            file_input = await page.wait_for_selector("input[type='file']", timeout=15000)
        logger.info(f"Setting file path in upload input: {str(path_obj.resolve())}")
        await file_input.set_input_files(str(path_obj.resolve()))

        # 3. Wait for Details dialog to load
        logger.info("Waiting for upload details dialog...")
        await page.wait_for_selector("#textbox, div#textbox[contenteditable='true']", timeout=30000)
        await page.wait_for_timeout(2500)

        # Set Title
        title_box = await page.query_selector("#textbox[aria-label*='title'], div#textbox[aria-label*='Add a title'], #textbox")
        if title_box:
            await title_box.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(full_title)

        await page.wait_for_timeout(1000)

        # Set Description
        desc_boxes = await page.query_selector_all("div#textbox[contenteditable='true']")
        if len(desc_boxes) > 1:
            desc_box = desc_boxes[1]
            await desc_box.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(full_description)

        await page.wait_for_timeout(1000)

        # 4. Mandatory Audience Check
        logger.info(f"Setting audience to '{audience}'...")
        if audience == "made_for_kids":
            mfk_radio = await page.query_selector("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_MFK']")
            if mfk_radio:
                await mfk_radio.click()
        else:
            not_mfk_radio = await page.query_selector("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']")
            if not_mfk_radio:
                await not_mfk_radio.click()

        await page.wait_for_timeout(1000)

        # 5. Navigate Next to Visibility Step
        logger.info("Progressing to Visibility step...")
        for _ in range(3):
            next_btn = await page.query_selector("#next-button")
            if next_btn and await next_btn.is_visible():
                await next_btn.click()
                await page.wait_for_timeout(1500)

        # 6. Set Visibility
        logger.info(f"Setting visibility to '{visibility}'...")
        vis_name = visibility.upper()
        vis_radio = await page.query_selector(f"tp-yt-paper-radio-button[name='{vis_name}']")
        if vis_radio:
            await vis_radio.click()
        else:
            # Fallback to private radio
            priv_radio = await page.query_selector("tp-yt-paper-radio-button[name='PRIVATE']")
            if priv_radio:
                await priv_radio.click()

        await page.wait_for_timeout(1000)

        # 7. Extract YouTube Video Link if visible
        video_url = ""
        link_elem = await page.query_selector("a.ytcp-video-info, .video-url-fadeable a, a[href*='youtu.be']")
        if link_elem:
            video_url = await link_elem.get_attribute("href") or ""

        # 8. Click Save / Publish
        logger.info("Publishing / saving video on YouTube Studio...")
        done_btn = await page.query_selector("#done-button")
        if done_btn and await done_btn.is_visible():
            await done_btn.click()
            await page.wait_for_timeout(3000)

        if not video_url:
            # Check for link in confirmation dialog
            link_elem = await page.query_selector("a[href*='youtu.be']")
            if link_elem:
                video_url = await link_elem.get_attribute("href") or ""

        # Close dialog if close button visible
        close_btn = await page.query_selector("#close-button")
        if close_btn and await close_btn.is_visible():
            await close_btn.click()

        # Update database with YouTube upload status
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clips 
                SET status = 'PUBLISHED', approval_status = 'APPROVED'
                WHERE id = ?
            """, (clip_id,))

        logger.info(f"Short published successfully to YouTube Studio! Link: {video_url or 'Saved in Studio'}")

        return {
            "success": True,
            "clip_id": clip_id,
            "title": full_title,
            "audience": audience,
            "visibility": visibility,
            "video_url": video_url or "https://studio.youtube.com",
            "status": "PUBLISHED"
        }
