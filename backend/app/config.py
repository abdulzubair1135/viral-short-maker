import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
PROJECTS_DIR = STORAGE_DIR / "projects"
ASSETS_DIR = STORAGE_DIR / "assets"
LOGS_DIR = STORAGE_DIR / "logs"
BROWSER_PROFILES_DIR = STORAGE_DIR / "browser_profiles"

for p in [STORAGE_DIR, PROJECTS_DIR, ASSETS_DIR, LOGS_DIR, BROWSER_PROFILES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = STORAGE_DIR / "studio.db"
DB_URL = f"sqlite:///{DB_PATH}"

# FFmpeg detection
def get_ffmpeg_binary() -> str:
    # 1. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # 2. Check imageio_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # 3. Check common Windows paths
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Python/Python310/lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe",
        Path(os.environ.get("ProgramFiles", "")) / "ffmpeg/bin/ffmpeg.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_binary()

# AI Provider Settings
AI_PROVIDER_DEFAULT = "mock"  # "gemini", "chatgpt", "deepseek", or "mock"
HEADLESS_BROWSER = False  # Set to False to allow user login/CAPTCHA resolution

# Video Rendering Defaults
DEFAULT_SHORT_WIDTH = 1080
DEFAULT_SHORT_HEIGHT = 1920
DEFAULT_FPS = 30
DEFAULT_MAX_DURATION = 60.0
DEFAULT_MIN_DURATION = 15.0
