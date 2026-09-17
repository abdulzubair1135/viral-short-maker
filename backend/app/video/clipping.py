from typing import Dict, Any, List, Optional
from backend.app.core.logging import logger

DEFAULT_SCORING_WEIGHTS = {
    "hook": 0.25,
    "story": 0.20,
    "emotion": 0.15,
    "curiosity": 0.15,
    "clarity": 0.10,
    "visual": 0.10,
    "length": 0.05,
}

def calculate_composite_score(scores: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """Calculate weighted composite score (0-100)."""
    w = weights or DEFAULT_SCORING_WEIGHTS
    total = sum(scores.get(k, 50.0) * weight for k, weight in w.items())
    return round(min(max(total, 0.0), 100.0), 1)

def optimize_boundaries(
    raw_start: float,
    raw_end: float,
    transcript_segments: List[Dict[str, Any]],
    video_duration: float,
    pre_roll: float = 0.5,
    post_roll: float = 0.8
) -> Dict[str, float]:
    """
    Optimizes clip boundaries:
    - Snaps to natural sentence/word start and end boundaries to avoid cutting mid-syllable.
    - Applies configurable pre-roll and post-roll padding.
    - Clamps to video duration.
    """
    opt_start = max(0.0, raw_start - pre_roll)
    opt_end = min(video_duration, raw_end + post_roll)

    # Find closest sentence boundary near opt_start
    best_start = opt_start
    for seg in transcript_segments:
        # If segment start is within 1.5s of opt_start, snap to it
        if abs(seg["start"] - opt_start) <= 1.5:
            best_start = max(0.0, seg["start"] - 0.1)
            break

    # Find closest sentence boundary near opt_end
    best_end = opt_end
    for seg in reversed(transcript_segments):
        # If segment end is within 2.0s of opt_end, snap to it
        if abs(seg["end"] - opt_end) <= 2.0:
            best_end = min(video_duration, seg["end"] + 0.3)
            break

    # Ensure minimum duration (15s) and maximum (60s)
    final_duration = best_end - best_start
    if final_duration < 15.0:
        needed = 15.0 - final_duration
        best_end = min(video_duration, best_end + needed)
        if (best_end - best_start) < 15.0:
            best_start = max(0.0, best_end - 15.0)

    if (best_end - best_start) > 60.0:
        best_end = best_start + 60.0

    return {
        "start": round(best_start, 2),
        "end": round(best_end, 2),
        "duration": round(best_end - best_start, 2)
    }

def compute_temporal_iou(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    """Calculate Intersection-over-Union between two time intervals."""
    intersection = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    if union <= 0.0:
        return 0.0
    return intersection / union

def filter_duplicate_clips(candidates: List[Dict[str, Any]], iou_threshold: float = 0.4) -> List[Dict[str, Any]]:
    """
    Prunes redundant clips covering the same moment.
    Sorts by score descending, keeps the higher scoring clip, and discards overlapping duplicates.
    """
    if not candidates:
        return []

    # Sort descending by composite score
    sorted_candidates = sorted(candidates, key=lambda c: c.get("score_total", 0.0), reverse=True)
    kept = []

    for cand in sorted_candidates:
        c_start = cand["start"]
        c_end = cand["end"]
        is_dup = False
        for k in kept:
            iou = compute_temporal_iou(c_start, c_end, k["start"], k["end"])
            if iou >= iou_threshold:
                logger.info(f"Filtered duplicate clip '{cand.get('title')}' (IoU={iou:.2f} with '{k.get('title')}')")
                is_dup = True
                break
        if not is_dup:
            kept.append(cand)

    return kept
