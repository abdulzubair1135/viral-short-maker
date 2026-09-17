import json
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.app.config import FFMPEG_PATH
from backend.app.core.logging import logger

class FFmpegError(Exception):
    pass

class FFmpegWrapper:
    def __init__(self, binary_path: str = FFMPEG_PATH):
        self.binary_path = binary_path

    def run_command(self, args: List[str], timeout: Optional[int] = 300) -> subprocess.CompletedProcess:
        cmd = [self.binary_path] + args
        logger.info(f"Executing FFmpeg: {' '.join(cmd[:10])} ...")
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            if res.returncode != 0:
                logger.error(f"FFmpeg error (code {res.returncode}): {res.stderr[-500:]}")
                raise FFmpegError(f"FFmpeg command failed: {res.stderr[-300:]}")
            return res
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg process timed out after {timeout} seconds")
            raise FFmpegError(f"FFmpeg process timed out after {timeout}s")

    def probe(self, file_path: str) -> Dict[str, Any]:
        """Probe video file using ffmpeg -i and parse duration, streams, codec, resolution, and fps."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # Run ffmpeg -i to inspect streams from stderr
        cmd = [self.binary_path, "-hide_banner", "-i", str(p)]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stderr_output = res.stderr

        info = {
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "video_codec": "unknown",
            "audio_codec": "none",
            "audio_channels": 0,
            "audio_sample_rate": 0,
            "has_video": False,
            "has_audio": False,
            "file_size": p.stat().st_size
        }

        # Parse duration: Duration: 00:01:23.45, start: ...
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", stderr_output)
        if dur_match:
            hours, minutes, seconds = dur_match.groups()
            info["duration"] = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

        # Parse Video stream: Stream #0:0: Video: h264 (...), yuv420p, 1920x1080 [SAR 1:1 DAR 16:9], 30 fps, ...
        vid_match = re.search(r"Stream.*Video:\s*([a-zA-Z0-9_-]+).*?,\s*(\d{2,5})x(\d{2,5}).*?,\s*([\d.]+)\s*fps", stderr_output)
        if vid_match:
            info["has_video"] = True
            info["video_codec"] = vid_match.group(1)
            info["width"] = int(vid_match.group(2))
            info["height"] = int(vid_match.group(3))
            info["fps"] = float(vid_match.group(4))
        else:
            # Fallback for video stream without fps in same line
            alt_vid = re.search(r"Stream.*Video:\s*([a-zA-Z0-9_-]+).*?,\s*(\d{2,5})x(\d{2,5})", stderr_output)
            if alt_vid:
                info["has_video"] = True
                info["video_codec"] = alt_vid.group(1)
                info["width"] = int(alt_vid.group(2))
                info["height"] = int(alt_vid.group(3))
                info["fps"] = 30.0

        # Parse Audio stream: Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, ...
        aud_match = re.search(r"Stream.*Audio:\s*([a-zA-Z0-9_-]+).*?,\s*(\d+)\s*Hz,\s*([a-zA-Z0-9_]+)", stderr_output)
        if aud_match:
            info["has_audio"] = True
            info["audio_codec"] = aud_match.group(1)
            info["audio_sample_rate"] = int(aud_match.group(2))
            channel_str = aud_match.group(3)
            info["audio_channels"] = 2 if "stereo" in channel_str else (1 if "mono" in channel_str else 2)

        return info

ffmpeg = FFmpegWrapper()
