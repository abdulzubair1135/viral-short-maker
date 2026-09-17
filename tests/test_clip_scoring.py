import pytest
from backend.app.video.clipping import (
    calculate_composite_score,
    optimize_boundaries,
    compute_temporal_iou,
    filter_duplicate_clips
)

def test_calculate_composite_score():
    scores = {
        "hook": 90,       # 90 * 0.25 = 22.5
        "story": 80,      # 80 * 0.20 = 16.0
        "emotion": 80,    # 80 * 0.15 = 12.0
        "curiosity": 90,  # 90 * 0.15 = 13.5
        "clarity": 85,    # 85 * 0.10 = 8.5
        "visual": 70,     # 70 * 0.10 = 7.0
        "length": 80      # 80 * 0.05 = 4.0
    }
    # Expected: 22.5 + 16.0 + 12.0 + 13.5 + 8.5 + 7.0 + 4.0 = 83.5
    total = calculate_composite_score(scores)
    assert total == 83.5

def test_optimize_boundaries_sentence_snapping():
    segments = [
        {"start": 4.8, "end": 10.2, "text": "First sentence here."},
        {"start": 10.5, "end": 35.1, "text": "Second complete statement."},
        {"start": 35.4, "end": 40.0, "text": "Third final conclusion."}
    ]
    # If raw is 10.0 to 35.0, opt_start is 9.5. Close to 10.5 -> snaps
    res = optimize_boundaries(
        raw_start=10.0,
        raw_end=35.0,
        transcript_segments=segments,
        video_duration=60.0,
        pre_roll=0.5,
        post_roll=0.5
    )
    assert res["start"] <= 10.5
    assert res["end"] >= 35.0
    assert 15.0 <= res["duration"] <= 60.0

def test_filter_duplicate_clips():
    candidates = [
        {
            "title": "Clip A High",
            "start": 10.0,
            "end": 40.0,
            "score_total": 92.0
        },
        {
            "title": "Clip A Duplicate",
            "start": 12.0,
            "end": 38.0,
            "score_total": 85.0
        },
        {
            "title": "Clip B Unique",
            "start": 60.0,
            "end": 90.0,
            "score_total": 88.0
        }
    ]
    filtered = filter_duplicate_clips(candidates, iou_threshold=0.5)
    # The lower-scoring duplicate (85.0) should be dropped
    assert len(filtered) == 2
    titles = [c["title"] for c in filtered]
    assert "Clip A High" in titles
    assert "Clip B Unique" in titles
    assert "Clip A Duplicate" not in titles
