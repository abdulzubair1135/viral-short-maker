import pytest
from pathlib import Path
from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.video.renderer import VideoRenderer
from backend.app.config import STORAGE_DIR

@pytest.fixture(scope="module")
def synthetic_video(tmp_path_factory):
    """Generate a clean synthetic 20-second 16:9 MP4 test video with audio."""
    temp_dir = tmp_path_factory.mktemp("test_video_dir")
    vid_path = temp_dir / "synthetic_source.mp4"

    # FFmpeg command to generate 20s of video + audio
    args = [
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=20:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(vid_path)
    ]
    ffmpeg.run_command(args, timeout=60)
    assert vid_path.exists()
    return vid_path

def test_ffmpeg_probe(synthetic_video):
    meta = ffmpeg.probe(str(synthetic_video))
    assert meta["has_video"] is True
    assert meta["has_audio"] is True
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert abs(meta["duration"] - 20.0) < 1.0

def test_video_render_pipeline(synthetic_video, tmp_path):
    renderer = VideoRenderer()
    out_mp4 = tmp_path / "rendered_916.mp4"
    work_dir = tmp_path / "work"

    clip_data = {
        "start_time": 2.0,
        "end_time": 17.0,
        "crop_mode": "speaker_tracking",
        "caption_preset": "dynamic"
    }
    transcript_data = {
        "segments": [
            {
                "start": 2.5,
                "end": 8.0,
                "text": "This is a test viral moment",
                "words": [
                    {"word": "This", "start": 2.5, "end": 3.2},
                    {"word": "is", "start": 3.3, "end": 4.0},
                    {"word": "a", "start": 4.1, "end": 4.5},
                    {"word": "test", "start": 4.6, "end": 5.5},
                    {"word": "viral", "start": 5.6, "end": 6.8},
                    {"word": "moment", "start": 6.9, "end": 8.0}
                ]
            }
        ]
    }

    result_path = renderer.render_clip(
        source_video_path=str(synthetic_video),
        clip_data=clip_data,
        transcript_data=transcript_data,
        output_mp4=out_mp4,
        work_dir=work_dir
    )

    assert result_path.exists()
    out_meta = ffmpeg.probe(str(result_path))
    assert out_meta["has_video"] is True
    assert out_meta["has_audio"] is True
    assert out_meta["width"] == 1080
    assert out_meta["height"] == 1920
    assert abs(out_meta["duration"] - 15.0) < 1.5
