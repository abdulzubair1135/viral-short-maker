import asyncio
from typing import Dict, Any, Optional
from backend.app.ai.base_provider import AIProvider
from backend.app.browser.playwright_manager import browser_manager
from backend.app.ai.prompts import SYSTEM_MOMENT_DETECTION_PROMPT
from backend.app.ai.validators import validate_and_repair_candidates
from backend.app.core.logging import logger

class ChatGPTBrowserProvider(AIProvider):
    URL = "https://chatgpt.com"

    @property
    def name(self) -> str:
        return "chatgpt"

    async def health_check(self) -> Dict[str, Any]:
        try:
            context = await browser_manager.get_context(self.name)
            page = await context.new_page()
            await page.goto(self.URL, wait_until="domcontentloaded", timeout=30000)

            login_needed = False
            if await page.locator("button:has-text('Log in'), a:has-text('Log in')").count() > 0:
                login_needed = True

            await page.close()
            return {
                "provider": self.name,
                "ready": not login_needed,
                "status": "Ready" if not login_needed else "PAUSED — Human intervention required (Log in needed)",
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
        prompt_template = prompt_override or SYSTEM_MOMENT_DETECTION_PROMPT
        prompt = prompt_template.format(
            title=title,
            video_url=video_url or "https://youtube.com",
            duration=duration,
            transcript=transcript_text,
            max_shorts=10,
            min_duration=20,
            max_duration=60
        )

        context = await browser_manager.get_context(self.name)
        page = context.pages[0] if context.pages else await context.new_page()

        logger.info(f"Navigating to ChatGPT web interface ({self.URL})...")
        await page.goto(self.URL, wait_until="networkidle", timeout=45000)

        # Check for authentication / Cloudflare challenge
        if await page.locator("button:has-text('Log in'), #cf-challenge-running").count() > 0:
            raise RuntimeError("PAUSED — Human intervention required: Please log in or complete verification on ChatGPT.")

        # Locate prompt textarea
        input_locator = page.locator("#prompt-textarea, div[contenteditable='true']").first
        await input_locator.wait_for(state="visible", timeout=15000)
        await input_locator.click()
        await input_locator.fill(prompt)

        # Click send
        send_btn = page.locator("button[data-testid='send-button'], button[aria-label*='Send prompt']").first
        if await send_btn.is_visible():
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")

        logger.info("Waiting for ChatGPT response stream to complete...")
        # Wait for stop-button to disappear
        try:
            stop_btn = page.locator("button[data-testid='stop-button']")
            await stop_btn.wait_for(state="attached", timeout=5000)
            await stop_btn.wait_for(state="detached", timeout=60000)
        except Exception:
            await asyncio.sleep(8.0)

        # Extract last assistant message
        response_locator = page.locator("article[data-testid*='conversation-turn'] div[data-message-author-role='assistant']").last
        await response_locator.wait_for(state="visible", timeout=30000)
        response_text = await response_locator.inner_text()

        return response_text

    def validate_response(self, response_text: str) -> Dict[str, Any]:
        return validate_structured_ai_response(response_text, source_duration=3600.0)
