import json
import re
from typing import List, Dict, Any, Tuple, Optional

class AIValidationError(Exception):
    pass

def extract_json_from_text(raw_text: str) -> Any:
    """
    Extracts and repairs JSON from raw AI text output.
    Handles Markdown backticks (```json ... ```), trailing commas, and leading/trailing chatter.
    """
    cleaned = raw_text.strip()

    # 1. Strip markdown code fences
    md_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if md_match:
        cleaned = md_match.group(1).strip()

    # 2. Locate outermost JSON structure ({ ... } or [ ... ])
    obj_start = cleaned.find("{")
    arr_start = cleaned.find("[")

    if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
        obj_end = cleaned.rfind("}")
        if obj_end != -1 and obj_end > obj_start:
            cleaned = cleaned[obj_start:obj_end + 1]
    elif arr_start != -1:
        arr_end = cleaned.rfind("]")
        if arr_end != -1 and arr_end > arr_start:
            cleaned = cleaned[arr_start:arr_end + 1]

    # 3. Attempt parsing with strict=False to allow unescaped control chars
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        # Repair trailing commas before brackets/braces
        repaired = re.sub(r",\s*([\]}])", r"\1", cleaned)
        try:
            return json.loads(repaired, strict=False)
        except json.JSONDecodeError:
            # Sanitize unescaped newlines/tabs or invalid control characters
            sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda m: ' ' if m.group(0) in '\r\n\t' else '', repaired)
            try:
                return json.loads(sanitized, strict=False)
            except json.JSONDecodeError as e:
                raise AIValidationError(f"Could not parse valid JSON from AI response: {e}")

def validate_short_item(
    item: Dict[str, Any],
    source_duration: float,
    min_dur: float = 15.0,
    max_dur: float = 65.0,
    min_quality_threshold: float = 55.0
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Validates a single candidate short.
    Returns (is_valid, sanitized_item, rejection_reason).
    """
    start = item.get("start_time", item.get("start"))
    end = item.get("end_time", item.get("end"))

    if start is None or end is None:
        return False, None, "Missing start_time or end_time"

    try:
        start = float(start)
        end = float(end)
    except (ValueError, TypeError):
        return False, None, "Timestamps are not numeric"

    if start < 0.0:
        start = 0.0

    if end <= start:
        return False, None, f"end_time ({end}) <= start_time ({start})"

    if source_duration > 0 and end > source_duration:
        end = source_duration

    duration = round(end - start, 2)
    # If source video itself is short, adapt minimum duration
    effective_min_dur = min(min_dur, max(source_duration * 0.7, 10.0))
    if duration < effective_min_dur:
        return False, None, f"Duration ({duration}s) too short (<{effective_min_dur}s)"

    if duration > max_dur:
        end = start + max_dur
        duration = max_dur

    scores_input = item.get("scores", {}) if isinstance(item.get("scores"), dict) else {}
    score = float(item.get("score", item.get("overall_score", item.get("score_total", scores_input.get("overall", scores_input.get("total", 85.0))))))
    hook_score = float(item.get("hook_score", scores_input.get("hook", 85.0)))
    interest_score = float(item.get("interest_score", item.get("value_score", scores_input.get("interest", 85.0))))
    commentary_potential = float(item.get("commentary_potential", scores_input.get("commentary_potential", 85.0)))
    standalone_score = float(item.get("standalone_score", scores_input.get("standalone", 85.0)))
    clarity_score = float(item.get("clarity_score", scores_input.get("clarity", 90.0)))
    context_score = float(item.get("context_score", scores_input.get("context", 85.0)))
    originality_potential = float(item.get("originality_potential", scores_input.get("originality", 85.0)))
    overall_score = score

    # Reject weak moments below quality threshold or with low commentary potential
    if score < min_quality_threshold:
        return False, None, f"Quality score ({score}) below threshold ({min_quality_threshold})"

    if standalone_score < 50.0:
        return False, None, f"Insufficient standalone context (score {standalone_score})"

    title = str(item.get("title", "High Impact Moment")).strip()
    hook = str(item.get("hook", "Key takeaway")).strip()
    description = str(item.get("description", f"Key highlight: {hook}")).strip()
    reason = str(item.get("reason", item.get("decision_reason", "Strong hook and narrative payoff."))).strip()

    analysis = item.get("analysis", {})
    if not isinstance(analysis, dict):
        analysis = {}
    
    rating = float(analysis.get("rating", item.get("rating", 8.5)))
    verdict = str(analysis.get("verdict", item.get("verdict", "Transformative breakdown"))).strip()
    source_attribution = str(item.get("source_attribution", "Original content analyzed for commentary & critique")).strip()
    
    narration_script = item.get("narration_script", [])
    if not isinstance(narration_script, list):
        narration_script = [{"segment": "commentary", "text": str(narration_script)}]

    hashtags = item.get("hashtags", ["#shorts", "#review", "#viral"])
    if not isinstance(hashtags, list):
        hashtags = ["#shorts", "#review"]
    hashtags = [h.strip() if h.strip().startswith("#") else f"#{h.strip()}" for h in hashtags if h.strip()]

    keywords = item.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []

    sanitized = {
        "id": str(item.get("id", f"short_{int(start)}")),
        "start": round(start, 2),
        "end": round(end, 2),
        "start_time": round(start, 2),
        "end_time": round(end, 2),
        "duration": duration,
        "score": round(score, 1),
        "hook_score": round(hook_score, 1),
        "interest_score": round(interest_score, 1),
        "commentary_potential": round(commentary_potential, 1),
        "standalone_score": round(standalone_score, 1),
        "clarity_score": round(clarity_score, 1),
        "context_score": round(context_score, 1),
        "originality_potential": round(originality_potential, 1),
        "overall_score": round(overall_score, 1),
        "scores": {
            "hook": round(hook_score, 1),
            "story": round(context_score, 1),
            "hook_score": round(hook_score, 1),
            "interest_score": round(interest_score, 1),
            "commentary_potential": round(commentary_potential, 1),
            "standalone_score": round(standalone_score, 1),
            "clarity_score": round(clarity_score, 1),
            "context_score": round(context_score, 1),
            "originality_potential": round(originality_potential, 1),
            "overall_score": round(overall_score, 1),
            "total": round(score, 1)
        },

        "reason": reason,
        "hook": hook,
        "title": title,
        "summary": description,
        "description": description,
        "hashtags": hashtags[:6],
        "keywords": keywords[:6],
        "analysis": analysis,
        "verdict": verdict,
        "rating": rating,
        "source_attribution": source_attribution,
        "narration_script": narration_script,
        "caption_style": item.get("caption_style", "dynamic"),
        "priority": int(item.get("priority", 1))
    }

    return True, sanitized, ""

def validate_structured_ai_response(
    raw_text: str,
    source_duration: float,
    max_shorts_limit: int = 10,
    min_dur: float = 15.0,
    max_dur: float = 65.0
) -> Dict[str, Any]:
    """
    Validates structured AI response where AI determines the number of quality shorts.
    Returns:
    {
      "source_analysis": { ... },
      "shorts": [ ... validated shorts up to max_shorts_limit ... ],
      "rejected": [ { "title": ..., "reason": ... } ]
    }
    """
    parsed = extract_json_from_text(raw_text)

    # Normalize if array returned directly
    if isinstance(parsed, list):
        raw_shorts = parsed
        analysis = {
            "overall_quality": 85,
            "summary": "AI identified moments from transcript",
            "recommended_short_count": len(parsed)
        }
        raw_rejected = []
    elif isinstance(parsed, dict):
        raw_shorts = parsed.get("shorts", parsed.get("clips", []))
        analysis = parsed.get("source_analysis", {
            "overall_quality": 85,
            "summary": "Source analysis complete",
            "recommended_short_count": len(raw_shorts)
        })
        raw_rejected = parsed.get("rejected_candidates", parsed.get("rejected", []))
    else:
        raise AIValidationError("AI response must be a JSON object or array of shorts")

    valid_shorts = []
    rejected_shorts = []

    # Preserve explicit AI-rejected candidates
    for rj in raw_rejected:
        if isinstance(rj, dict):
            st = float(rj.get("start_time", 0.0))
            et = float(rj.get("end_time", 0.0))
            rejected_shorts.append({
                "title": rj.get("title", "Excluded moment"),
                "start_time": round(st, 2),
                "end_time": round(et, 2),
                "duration": round(rj.get("duration", max(0.0, et - st)), 2),
                "claim": str(rj.get("claim", "")),
                "scores": rj.get("scores", {}),
                "score_total": float(rj.get("score_total", 0.0)),
                "reason": rj.get("rejection_reason", rj.get("reason", "Low commentary potential or filler"))
            })

    for raw in raw_shorts:
        if isinstance(raw, dict):
            is_valid, sanitized, reason = validate_short_item(
                raw,
                source_duration=source_duration,
                min_dur=min_dur,
                max_dur=max_dur
            )
            if is_valid and sanitized is not None:
                valid_shorts.append(sanitized)
            else:
                st = float(raw.get("start_time", raw.get("start", 0.0)) or 0.0)
                et = float(raw.get("end_time", raw.get("end", 0.0)) or 0.0)
                rejected_shorts.append({
                    "title": raw.get("title", "Candidate moment"),
                    "start_time": round(st, 2),
                    "end_time": round(et, 2),
                    "duration": round(max(0.0, et - st), 2),
                    "claim": str(raw.get("claim", "")),
                    "scores": raw.get("scores", {}),
                    "score_total": float(raw.get("score", 0.0)),
                    "reason": reason
                })

    # If all candidates were rejected due to high score threshold but timestamps are valid,
    # rescue the top candidate so user is never left with an empty project
    if not valid_shorts and raw_shorts:
        for raw in raw_shorts:
            if isinstance(raw, dict):
                is_valid, sanitized, _ = validate_short_item(
                    raw,
                    source_duration=source_duration,
                    min_dur=min_dur,
                    max_dur=max_dur,
                    min_quality_threshold=30.0
                )
                if is_valid and sanitized is not None:
                    valid_shorts.append(sanitized)
        valid_shorts.sort(key=lambda x: x["score"], reverse=True)
        if valid_shorts:
            valid_shorts = valid_shorts[:1]

    # Sort descending by score
    valid_shorts.sort(key=lambda x: x["score"], reverse=True)

    # Cap by max_shorts_limit if exceeded
    if len(valid_shorts) > max_shorts_limit:
        excess = valid_shorts[max_shorts_limit:]
        for ex in excess:
            rejected_shorts.append({
                "title": ex["title"],
                "start_time": ex["start"],
                "end_time": ex["end"],
                "duration": ex["duration"],
                "claim": "",
                "scores": ex.get("scores", {}),
                "score_total": ex.get("score", 0.0),
                "reason": f"Ranked below top {max_shorts_limit} maximum limit"
            })
        valid_shorts = valid_shorts[:max_shorts_limit]

    return {
        "source_analysis": analysis,
        "shorts": valid_shorts,
        "rejected": rejected_shorts
    }


def validate_and_repair_candidates(raw_text: str, max_duration: float = 3600.0) -> List[Dict[str, Any]]:
    """Backwards-compatible wrapper returning candidates list."""
    res = validate_structured_ai_response(raw_text, source_duration=max_duration)
    return res["shorts"]

def validate_clip_candidate_schema(candidate: Dict[str, Any], max_duration: float = 3600.0) -> Dict[str, Any]:
    """Validates single candidate dictionary and raises AIValidationError if invalid."""
    is_valid, item, reason = validate_short_item(candidate, source_duration=max_duration)
    if not is_valid or item is None:
        raise AIValidationError(reason)
    return item
