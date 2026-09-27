import asyncio
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from backend.app.config import STORAGE_DIR
from backend.app.core.logging import logger

CHROME_DEBUG_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CHROME_DEBUG_PORT}"

# Preferred profile path: check omnidev profile first (where user already logged in), fallback to local storage
OMNIDEV_PROFILE = Path("C:/Users/abdul/OneDrive/ドキュメント/ai/omnidev/chrome_profile")
LOCAL_PROFILE = STORAGE_DIR / "chrome_profile"
CHROME_PROFILE_DIR = OMNIDEV_PROFILE if OMNIDEV_PROFILE.exists() else LOCAL_PROFILE

POSSIBLE_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

def get_chrome_executable() -> str:
    for path in POSSIBLE_CHROME_PATHS:
        if os.path.exists(path):
            return path
    return "chrome.exe"

class BrowserSessionManager:
    _instance: Optional["BrowserSessionManager"] = None

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    @classmethod
    def get_instance(cls) -> "BrowserSessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure_chrome_running(self):
        """Starts Chrome with remote debugging on port 9222 if not already open, waiting until port is ready."""
        def is_port_open():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            res = sock.connect_ex(('127.0.0.1', CHROME_DEBUG_PORT))
            sock.close()
            return res == 0

        if is_port_open():
            return

        logger.info(f"Starting Chrome with profile '{CHROME_PROFILE_DIR}' on debug port {CHROME_DEBUG_PORT}...")
        chrome_exe = get_chrome_executable()
        CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        cmd = [
            chrome_exe,
            f"--remote-debugging-port={CHROME_DEBUG_PORT}",
            f"--user-data-dir={str(CHROME_PROFILE_DIR)}",
            "https://gemini.google.com/app",
            "https://chat.deepseek.com/",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Poll up to 15 seconds for port 9222 to open
        for _ in range(30):
            time.sleep(0.5)
            if is_port_open():
                logger.info("Chrome debug port 9222 is active and listening!")
                time.sleep(1.0)
                return
        logger.warning("Chrome debug port 9222 did not open within timeout.")

    async def get_cdp_context(self) -> BrowserContext:
        """Connects to Chrome session over CDP (port 9222) with automatic retries."""
        self.ensure_chrome_running()

        if self.playwright is None:
            self.playwright = await async_playwright().start()

        for attempt in range(3):
            try:
                if self.browser is None or not self.browser.is_connected():
                    logger.info(f"Connecting Playwright over CDP to {CDP_URL} (Attempt {attempt+1}/3)...")
                    self.browser = await self.playwright.chromium.connect_over_cdp(CDP_URL)
                break
            except Exception as e:
                logger.warning(f"CDP connection attempt {attempt+1} failed: {e}")
                await asyncio.sleep(2.0)

        if not self.browser or not self.browser.is_connected():
            raise RuntimeError(f"Could not connect to Chrome on debug port {CHROME_DEBUG_PORT}.")

        contexts = self.browser.contexts
        self.context = contexts[0] if contexts else await self.browser.new_context()
        return self.context

    async def get_or_create_page(self, url_keyword: str, default_url: str) -> Page:
        """Finds existing tab with url_keyword or opens a new tab."""
        context = await self.get_cdp_context()
        for p in context.pages:
            if url_keyword in p.url.lower():
                await p.bring_to_front()
                return p

        page = await context.new_page()
        await page.goto(default_url, wait_until="domcontentloaded", timeout=45000)
        await page.bring_to_front()
        return page

    async def close_all(self):
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

browser_manager = BrowserSessionManager.get_instance()
