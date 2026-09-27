import pytest
import uuid
import json
from pathlib import Path
from backend.app.core.database import init_db, get_db_connection
from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.ai.validators import validate_structured_ai_response
from backend.app.services.auto_repurpose import AutoRepurposeService
from backend.app.jobs.queue import job_queue

@pytest.fixture(scope="module")
def sample_video_path(tmp_path_factory):
    """Generate a clean 25-second synthetic MP4 video with audio."""
    temp_dir = tmp_path_factory.mktemp("auto_repurpose_data")
    vid_file = temp_dir / "podcast_source.mp4"
    args = [
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=25:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=25",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-ar", "44100",
        "-shortest",
        str(vid_file)
    ]
    ffmpeg.run_command(args, timeout=60)
    assert vid_file.exists()
    return vid_file

def test_ai_candidate_count_variations():
    """
    Tests that the AI decides the number of shorts:
    1. AI returns 4 candidates -> Exactly 4 validated
    2. AI returns 2 candidates -> Exactly 2 validated
    3. AI returns 12 candidates with max_shorts_limit=10 -> Exactly 10 validated
    4. AI returns weak candidates below threshold -> Weak candidates are rejected
    """
    # 1. 4 Valid Candidates
    four_candidates = [
        {
            "id": f"s_{i}",
            "start_time": float(i * 5),
            "end_time": float(i * 5 + 20),
            "score": 90 - i,
            "standalone_score": 90,
            "title": f"Candidate {i}",
            "hook": f"Hook {i}",
            "description": f"Description {i}",
            "hashtags": ["#shorts"]
        }
        for i in range(4)
    ]
    res4 = validate_structured_ai_response(json.dumps({"shorts": four_candidates}), source_duration=60.0)
    assert len(res4["shorts"]) == 4

    # 2. 2 Valid Candidates
    two_candidates = four_candidates[:2]
    res2 = validate_structured_ai_response(json.dumps({"shorts": two_candidates}), source_duration=60.0)
    assert len(res2["shorts"]) == 2

    # 3. 12 Candidates with max_shorts_limit = 10 -> Capped at 10
    twelve_candidates = [
        {
            "id": f"s_{i}",
            "start_time": float(i * 2),
            "end_time": float(i * 2 + 18),
            "score": 95 - i,
            "standalone_score": 90,
            "title": f"Candidate {i}",
            "hook": f"Hook {i}",
            "description": f"Description {i}",
            "hashtags": ["#shorts"]
        }
        for i in range(12)
    ]
    res12 = validate_structured_ai_response(
        json.dumps({"shorts": twelve_candidates}),
        source_duration=120.0,
        max_shorts_limit=10
    )
    assert len(res12["shorts"]) == 10
    assert len(res12["rejected"]) >= 2

    # 4. Weak candidates below threshold -> Rejected
    mixed_candidates = [
        {
            "id": "good_1",
            "start_time": 10.0,
            "end_time": 35.0,
            "score": 92.0,
            "standalone_score": 90.0,
            "title": "Strong Moment",
            "hook": "Strong Hook",
            "description": "Strong Desc",
            "hashtags": ["#shorts"]
        },
        {
            "id": "weak_1",
            "start_time": 40.0,
            "end_time": 65.0,
            "score": 45.0,  # Below threshold 68.0!
            "standalone_score": 50.0,
            "title": "Weak Boring Moment",
            "hook": "Boring",
            "description": "Boring",
            "hashtags": ["#shorts"]
        },
        {
            "id": "no_context",
            "start_time": 70.0,
            "end_time": 95.0,
            "score": 85.0,
            "standalone_score": 40.0,  # Below standalone context threshold 60.0!
            "title": "Contextless Moment",
            "hook": "Wait what?",
            "description": "Needs 10 mins before",
            "hashtags": ["#shorts"]
        }
    ]
    res_mixed = validate_structured_ai_response(
        json.dumps({"shorts": mixed_candidates}),
        source_duration=120.0
    )
    assert len(res_mixed["shorts"]) == 1
    assert res_mixed["shorts"][0]["title"] == "Strong Moment"
    assert len(res_mixed["rejected"]) == 2

@pytest.mark.asyncio
async def test_auto_repurpose_end_to_end(sample_video_path):
    """
    Test the complete one-click workflow:
    AutoRepurposeService.start_pipeline(...)
    -> creates project
    -> attaches source
    -> executes pipeline
    -> renders every AI-selected short to a real MP4 on disk
    -> passes Quality Control
    -> stores unique metadata (title, description, hashtags)
    """
    init_db()

    # Step 1: Start pipeline
    pipeline_res = AutoRepurposeService.start_pipeline(
        url_or_path=str(sample_video_path),
        rights_confirmed=True,
        options={"ai_provider": "mock", "max_shorts": 10}
    )

    proj_id = pipeline_res["project_id"]
    job_id = pipeline_res["job_id"]
    assert proj_id is not None
    assert job_id is not None

    # Step 2: Execute pipeline
    await job_queue.execute_project_pipeline(project_id=proj_id, job_id=job_id, ai_provider="mock")

    # Step 3: Verify results
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        assert job["status"] == "READY"
        assert job["progress"] == 100.0

        cursor.execute("SELECT * FROM clips WHERE project_id = ?", (proj_id,))
        clips = cursor.fetchall()
        # Mock provider returns 2 quality moments for 25s video
        assert len(clips) >= 1

        for c in clips:
            assert c["output_path"] != ""
            assert Path(c["output_path"]).exists()
            assert c["quality_score"] >= 70.0
            assert c["title"] != ""
            assert c["description"] != ""
            assert len(json.loads(c["hashtags"])) > 0
