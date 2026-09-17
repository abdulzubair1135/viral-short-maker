import re
from pathlib import Path
from typing import Dict, Any, List
from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.core.logging import logger

class VideoAnalyzer:
    @staticmethod
    def detect_scene_changes(video_path: str, threshold: float = 0.35) -> List[float]:
        """Detect scene change timestamps using FFmpeg select filter."""
        args = [
            "-i", str(video_path),
            "-filter_complex", f"select='gt(scene,{threshold})',metadata=print:file=-",
            "-f", "null", "-"
        ]
        try:
            res = ffmpeg.run_command(args, timeout=60)
            pts_matches = re.findall(r"pts_time:([\d.]+)", res.stderr + res.stdout)
            return [float(x) for x in pts_matches]
        except Exception as e:
            logger.warning(f"Scene detection warning: {e}")
            return []

    @staticmethod
    def detect_silence(video_path: str, noise_db: float = -30.0, duration: float = 0.8) -> List[Dict[str, float]]:
        """Detect silence intervals using FFmpeg silencedetect."""
        args = [
            "-i", str(video_path),
            "-af", f"silencedetect=noise={noise_db}dB:d={duration}",
            "-f", "null", "-"
        ]
        try:
            res = ffmpeg.run_command(args, timeout=60)
            starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", res.stderr)]
            ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", res.stderr)]
            intervals = []
            for s, e in zip(starts, ends):
                intervals.append({"start": s, "end": e, "duration": e - s})
            return intervals
        except Exception as e:
            logger.warning(f"Silence detection warning: {e}")
            return []

    @staticmethod
    def calculate_speech_density(segments: List[Dict[str, Any]], window_start: float, window_end: float) -> float:
        """Calculate word count per second in a time window."""
        window_duration = max(window_end - window_start, 1.0)
        word_count = 0
        for seg in segments:
            if seg["end"] >= window_start and seg["start"] <= window_end:
                words = seg.get("words", [])
                if words:
                    for w in words:
                        if w["start"] >= window_start and w["end"] <= window_end:
                            word_count += 1
                else:
                    word_count += len(seg.get("text", "").split())
        return round(word_count / window_duration, 2)
