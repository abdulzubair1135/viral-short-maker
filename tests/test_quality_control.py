import pytest
from pathlib import Path
from backend.app.quality.quality_control import QualityControlEngine
from backend.app.video.ffmpeg_wrapper import ffmpeg

def test_quality_control_checks(tmp_path):
    # Render a small 1080x1920 test MP4
    test_file = tmp_path / "qc_test_clip.mp4"
    args = [
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=15:size=1080x1920:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=15",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-ar", "44100",
        "-shortest",
        str(test_file)
    ]
    ffmpeg.run_command(args, timeout=60)
    assert test_file.exists()

    # Run QC with confirmed rights
    report = QualityControlEngine.run_checks(
        clip_file_path=str(test_file),
        expected_duration=15.0,
        rights_status="I own this content",
        caption_preset="dynamic"
    )

    assert report["passed"] is True
    assert report["score"] >= 85.0
    assert len(report["checks"]) == 15

    # Run QC with unconfirmed rights
    unconfirmed_report = QualityControlEngine.run_checks(
        clip_file_path=str(test_file),
        expected_duration=15.0,
        rights_status="Not confirmed",
        caption_preset="dynamic"
    )
    assert unconfirmed_report["passed"] is False
    assert unconfirmed_report["score"] < report["score"]
