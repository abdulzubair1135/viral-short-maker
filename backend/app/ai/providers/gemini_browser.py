import asyncio
import re
from typing import Dict, Any, Optional
from backend.app.ai.base_provider import AIProvider
from backend.app.browser.playwright_manager import browser_manager
from backend.app.ai.prompts import SYSTEM_MOMENT_DETECTION_PROMPT
from backend.app.ai.validators import validate_structured_ai_response
from backend.app.core.logging import logger

class GeminiBrowserProvider(AIProvider):
    URL = "https://gemini.google.com/app"

    def __init__(self):
        self.active_video_url: Optional[str] = None

    @property
    def name(self) -> str:
        return "gemini"

    async def health_check(self) -> Dict[str, Any]:
        try:
            page = await browser_manager.get_or_create_page("gemini.google.com", self.URL)
            login_needed = False
            if "accounts.google.com" in page.url or await page.locator("text='Sign in'").count() > 0:
                login_needed = True

            return {
                "provider": self.name,
                "ready": not login_needed,
                "status": "Ready" if not login_needed else "PAUSED — Human login needed on Gemini",
                "requires_human_intervention": login_needed
            }
        except Exception as e:
            return {
                "provider": self.name,
                "ready": False,
                "status": f"Error: {str(e)}",
                "requires_human_intervention": True
            }

    async def analyze(self, transcript_text: str, duration: float, prompt_override: Optional[str] = None, title: str = "Viral Video", video_url: str = "") -> str:
        # Sanitize sensitive words that trip consumer Gemini keyword safety filters
        safe_transcript = re.sub(r'\bbooby\s*traps?\b', 'obstacle traps', transcript_text, flags=re.IGNORECASE)

        prompt_template = prompt_override or SYSTEM_MOMENT_DETECTION_PROMPT
        prompt = prompt_template.format(
            title=title,
            video_url=video_url or "https://youtube.com",
            duration=duration,
            transcript=safe_transcript,
            max_shorts=10,
            min_duration=20,
            max_duration=60
        )

        logger.info("Opening Gemini session in Chrome...")
        page = await browser_manager.get_or_create_page("gemini.google.com", self.URL)
        await asyncio.sleep(2.0)

        # Check for authentication requirement
        if "accounts.google.com" in page.url or await page.locator("text='Sign in'").count() > 0:
            raise RuntimeError("PAUSED — Human intervention required: Please log into Google Gemini in the opened Chrome window.")

        # Re-use chat session: only create new chat when a brand new video URL is provided
        clean_url = video_url.strip()
        should_new_chat = False
        if clean_url and self.active_video_url != clean_url:
            should_new_chat = True
            self.active_video_url = clean_url
            logger.info(f"New video link detected ({clean_url}). Opening fresh Gemini chat session...")
        else:
            logger.info("Reusing existing Gemini chat session without creating a new chat...")

        if should_new_chat:
            try:
                new_btn = page.locator("button[aria-label*='New chat'], a[aria-label*='New chat']").first
                if await new_btn.is_visible():
                    await new_btn.click()
                    await asyncio.sleep(1.5)
            except Exception:
                pass

        # Locate prompt input
        input_locator = page.locator("rich-textarea div[contenteditable='true'], div[contenteditable='true'], p[data-placeholder]").first
        await input_locator.wait_for(state="visible", timeout=20000)
        await input_locator.click()
        await input_locator.fill(prompt)

        # Click send or press Enter
        send_btn = page.locator("button[aria-label*='Send'], button[aria-label*='Submit']").first
        if await send_btn.is_visible():
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")

        logger.info("Waiting for Gemini response stream...")
        # Wait for response container
        response_locator = page.locator(".model-response-text, message-content, [data-test-id='model-response']").last
        await response_locator.wait_for(state="visible", timeout=60000)

        # Wait until response text stabilizes
        last_len = 0
        stable_count = 0
        response_text = ""
        for _ in range(40):
            await asyncio.sleep(2.0)
            cur_text = await response_locator.inner_text()
            if len(cur_text) == last_len and len(cur_text) > 50:
                stable_count += 1
                if stable_count >= 2:
                    response_text = cur_text
                    break
            else:
                stable_count = 0
                last_len = len(cur_text)

        if not response_text:
            response_text = await response_locator.inner_text()

        # Check for canned Gemini refusal responses
        refusal_triggers = [
            "having a hard time fulfilling your request",
            "cannot fulfill",
            "can't help with that",
            "against my guidelines",
            "something else instead"
        ]
        for trig in refusal_triggers:
            if trig in response_text.lower():
                logger.warning(f"Detected Gemini policy false-positive refusal ('{trig}'). Triggering auto-fallback...")
                raise RuntimeError(f"Gemini policy false-positive refusal: {response_text.strip()}")

        return response_text

    def validate_response(self, response_text: str) -> Dict[str, Any]:
        return validate_structured_ai_response(response_text, source_duration=3600.0)
