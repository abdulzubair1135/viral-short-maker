from pathlib import Path
from typing import Dict, Any
from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.core.security import check_rights_permission

class VideoValidationError(Exception):
    pass

def validate_video_source(file_path: str, rights_status: str) -> Dict[str, Any]:
    """
    Validates a source video file:
    - Checks file existence and minimum size
    - Probes duration, resolution, codecs, fps, and streams
    - Validates presence of video and audio streams
    - Records content rights status
    """
    path = Path(file_path)
    if not path.exists():
        raise VideoValidationError(f"File does not exist: {file_path}")

    if path.stat().st_size < 1024:
        raise VideoValidationError("File is corrupted or empty (size < 1KB)")

    # Probe file with FFmpeg
    meta = ffmpeg.probe(str(path))

    if not meta["has_video"]:
        raise VideoValidationError("No valid video stream detected in source file")

    if not meta["has_audio"]:
        raise VideoValidationError("No valid audio stream detected in source file (audio is required for speech & viral shorts)")

    if meta["duration"] <= 0.0:
        raise VideoValidationError("Invalid video duration (0s detected)")

    meta["filename"] = path.name
    meta["file_path"] = str(path.resolve())
    meta["rights_status"] = rights_status
    meta["rights_confirmed"] = check_rights_permission(rights_status)

    return meta
