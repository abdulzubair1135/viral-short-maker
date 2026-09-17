import re
import os
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.config import STORAGE_DIR
from backend.app.core.logging import logger
from backend.app.video.ffmpeg_wrapper import ffmpeg

import ctypes

def get_windows_safe_path(p: Path) -> Path:
    """Converts a Path to its Windows 8.3 short path representation to prevent non-ASCII encoding issues."""
    p.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        try:
            buf = ctypes.create_unicode_buffer(1024)
            res = ctypes.windll.kernel32.GetShortPathNameW(str(p), buf, 1024)
            if res > 0:
                return Path(buf.value)
        except Exception:
            pass
    return p

DOWNLOADS_DIR = get_windows_safe_path(STORAGE_DIR / "downloads")

class YouTubeDownloader:
    @staticmethod
    def extract_metadata_and_download(url: str, max_duration_sec: float = 90.0) -> Dict[str, Any]:
        """
        Extracts video metadata and downloads clean 1.5 - 2 minute video chunk using yt-dlp & FFmpeg.
        Provides sufficient content for AI to generate 3 to 4 viral shorts rapidly.
        """
        import yt_dlp
        from backend.app.config import FFMPEG_PATH

        clean_url = url.strip()

        # Step 1: Extract basic metadata
        ydl_opts_meta = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
            meta = ydl.extract_info(clean_url, download=False)
            title = meta.get("title", "YouTube Video")
            video_id = meta.get("id", "yt_video")
            total_duration = float(meta.get("duration", 0))

        # Safe filename
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:40]
        target_path = DOWNLOADS_DIR / f"{safe_title}_{video_id}.mp4"
        sub_path = DOWNLOADS_DIR / f"{safe_title}_{video_id}.en.json3"

        # Ensure subtitles are acquired
        if not sub_path.exists():
            try:
                logger.info(f"Downloading official YouTube captions for '{title}'...")
                ydl_opts_sub = {
                    "skip_download": True,
                    "writeautomaticsub": True,
                    "writesubtitles": True,
                    "subtitleslangs": ["en", "en-US", "en-GB"],
                    "subtitlesformat": "json3",
                    "outtmpl": str(DOWNLOADS_DIR / f"{safe_title}_{video_id}.%(ext)s"),
                    "quiet": True,
                    "no_warnings": True
                }
                with yt_dlp.YoutubeDL(ydl_opts_sub) as ydl:
                    ydl.download([clean_url])
            except Exception as e:
                logger.warning(f"Could not download subtitles: {e}")

        if target_path.exists() and target_path.stat().st_size > 10000:
            logger.info(f"Using already cached downloaded video at {target_path}")
            return {
                "file_path": str(target_path),
                "title": title,
                "duration": total_duration,
                "subtitle_path": str(sub_path) if sub_path.exists() else None
            }

        # Step 2: Download high quality video segment
        clip_end = min(total_duration, max_duration_sec) if total_duration > 0 else max_duration_sec
        logger.info(f"Downloading video '{title}' segment [0s - {clip_end}s]...")

        ydl_opts_dl = {
            "outtmpl": str(target_path.with_suffix(".%(ext)s")),
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "ffmpeg_location": FFMPEG_PATH,
            "prefer_ffmpeg": True,
            "download_ranges": lambda info_dict, ydl: [{"start_time": 0, "end_time": clip_end}],
            "postprocessor_args": {"ffmpeg": ["-c:v", "copy", "-c:a", "copy"]},
            "quiet": True,
            "no_warnings": True
        }

        with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            actual_file = ydl.prepare_filename(info)

        # Ensure valid target_path
        if not Path(actual_file).exists():
            # Check glob
            found = list(DOWNLOADS_DIR.glob(f"{safe_title}_{video_id}.*"))
            if found:
                actual_file = str(found[0])
            else:
                raise FileNotFoundError(f"Downloaded video file not found for {clean_url}")

        return {
            "file_path": actual_file,
            "title": title,
            "duration": clip_end,
            "subtitle_path": str(sub_path) if sub_path.exists() else None
        }
