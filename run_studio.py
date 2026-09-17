"""
AI Content Repurposing Studio Launcher
Starts the backend server and opens the studio application in your default browser.
"""
import webbrowser
import threading
import time
import uvicorn
from backend.app.core.logging import logger

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    logger.info(f"Opening AI Content Repurposing Studio at {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
