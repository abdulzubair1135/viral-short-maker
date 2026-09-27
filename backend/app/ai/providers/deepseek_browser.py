import asyncio
from typing import Dict, Any, Optional
from backend.app.ai.base_provider import AIProvider
from backend.app.browser.playwright_manager import browser_manager
from backend.app.ai.prompts import SYSTEM_MOMENT_DETECTION_PROMPT
from backend.app.ai.validators import validate_structured_ai_response
from backend.app.core.logging import logger

class DeepSeekBrowserProvider(AIProvider):
    URL = "https://chat.deepseek.com"

    def __init__(self):
        self.active_video_url: Optional[str] = None

    @property
    def name(self) -> str:
        return "deepseek"

    async def health_check(self) -> Dict[str, Any]:
        try:
            page = await browser_manager.get_or_create_page("deepseek.com", self.URL)
            login_needed = False
            if await page.locator("button:has-text('Log in'), button:has-text('Sign in')").count() > 0:
                login_needed = True

            return {
                "provider": self.name,
                "ready": not login_needed,
                "status": "Ready" if not login_needed else "PAUSED — Human login needed on DeepSeek",
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
        if prompt_override:
            prompt = prompt_override
        else:
            prompt = SYSTEM_MOMENT_DETECTION_PROMPT.format(
                title=title,
                video_url=video_url or "https://youtube.com",
                duration=duration,
                transcript=transcript_text,
                max_shorts=10,
                min_duration=20,
                max_duration=60
            )

        logger.info("Opening DeepSeek session in Chrome...")
        page = await browser_manager.get_or_create_page("deepseek.com", self.URL)
        await page.bring_to_front()
        await asyncio.sleep(1.5)

        # Check login
        if await page.locator("button:has-text('Log in'), button:has-text('Sign in')").count() > 0:
            raise RuntimeError("PAUSED — Human intervention required: Please sign into DeepSeek in the opened Chrome window.")

        # Re-use chat session: only click new chat when link changes
        clean_url = video_url.strip()
        should_new_chat = False
        if clean_url and self.active_video_url != clean_url:
            should_new_chat = True
            self.active_video_url = clean_url
            logger.info(f"New video link detected ({clean_url}). Starting fresh DeepSeek chat...")
        else:
            logger.info("Reusing existing DeepSeek chat session...")

        if should_new_chat:
            try:
                new_btn = page.locator("div:has-text('New chat'), button:has-text('New chat')").first
                if await new_btn.is_visible():
                    await new_btn.click()
                    await asyncio.sleep(1.5)
            except Exception:
                pass

        # Input
        input_locator = page.locator("#chat-input, textarea").first
        await input_locator.wait_for(state="visible", timeout=20000)
        await input_locator.fill(prompt)

        # Send
        send_btn = page.locator("div[role='button']:has-text('Send'), button:has-text('Send'), div[aria-label*='Send']").first
        if await send_btn.is_visible():
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")

        logger.info("Waiting for DeepSeek response stream...")
        response_locator = page.locator(".ds-markdown, .chat-message-assistant").last
        await response_locator.wait_for(state="visible", timeout=60000)

        # Wait until response completes
        last_len = 0
        stable_count = 0
        response_text = ""
        for _ in range(45):
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

        return response_text

    def validate_response(self, response_text: str) -> Dict[str, Any]:
        return validate_structured_ai_response(response_text, source_duration=3600.0)
