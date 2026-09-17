import pytest
import uuid
import json
from pathlib import Path
from backend.app.core.database import init_db, get_db_connection
from backend.app.jobs.queue import job_queue
from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.api.routes_clips import approve_clip
from backend.app.api.routes_projects import export_project_bundle

@pytest.mark.asyncio
async def test_full_e2e_pipeline(tmp_path):
    init_db()

    # Step 1: Create synthetic 25-second source video
    source_vid = tmp_path / "longform_interview.mp4"
    args = [
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=25:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=25",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-ar", "44100",
        "-shortest",
        str(source_vid)
    ]
    ffmpeg.run_command(args, timeout=60)
    assert source_vid.exists()

    # Step 2: Create Project in DB
    proj_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (id, name, description, rights_status, status)
            VALUES (?, 'Masterclass Podcast Episode 1', 'Testing viral shorts pipeline', 'I own this content', 'DRAFT')
        """, (proj_id,))

        cursor.execute("""
            INSERT INTO sources (
                id, project_id, file_path, filename, file_size, duration,
                width, height, fps, video_codec, audio_codec, rights_status, validated
            ) VALUES (?, ?, ?, 'longform_interview.mp4', ?, 25.0, 1920, 1080, 30.0, 'h264', 'aac', 'I own this content', 1)
        """, (str(uuid.uuid4()), proj_id, str(source_vid), source_vid.stat().st_size))

    # Step 3: Run pipeline
    job_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs (id, project_id, job_type, status) VALUES (?, ?, 'PROJECT_PIPELINE', 'QUEUED')", (job_id, proj_id))

    await job_queue.execute_project_pipeline(project_id=proj_id, job_id=job_id, ai_provider="mock")

    # Step 4: Verify results in database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verify job
        cursor.execute("SELECT status, progress FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        assert job["status"] == "READY"
        assert job["progress"] == 100.0

        # Verify transcript
        cursor.execute("SELECT full_text, srt_content FROM transcripts WHERE project_id = ?", (proj_id,))
        transcript = cursor.fetchone()
        assert transcript is not None
        assert len(transcript["full_text"]) > 0

        # Verify clips
        cursor.execute("SELECT * FROM clips WHERE project_id = ?", (proj_id,))
        clips = cursor.fetchall()
        assert len(clips) >= 1

        top_clip = clips[0]
        assert top_clip["score_total"] > 0
        assert top_clip["output_path"] != ""
        assert Path(top_clip["output_path"]).exists()

        # Verify Quality Control
        cursor.execute("SELECT * FROM quality_checks WHERE clip_id = ?", (top_clip["id"],))
        qc = cursor.fetchone()
        assert qc is not None
        assert qc["score"] >= 80.0

    # Step 5: Test Human Approval
    res_approve = approve_clip(top_clip["id"])
    assert res_approve["status"] == "approved"

    # Step 6: Test Portable Project Bundle Export (.acs)
    res_export = export_project_bundle(proj_id)
    assert Path(res_export.path).exists()
    assert res_export.path.endswith(".acs")
