import json
import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.ai.validators import extract_json_from_text, AIValidationError

VALID_STYLES = {"sarcastic", "relatable", "dark_humor", "wholesome", "absurd", "educational_roast"}
VALID_FORMATS = {"classic", "pov", "story", "reaction", "animated", "short"}
REQUIRED_SCORES = [
    "relatability", "punchline_timing", "visual_synergy",
    "shareability", "trend_alignment", "hook_power", "simplicity"
]

def sanitize_meme_item(raw: Dict[str, Any], default_topic: str = "") -> Optional[Dict[str, Any]]:
    """Sanitizes and strictly validates a single meme item."""
    concept = str(raw.get("concept") or raw.get("premise") or default_topic).strip()
    hook = str(raw.get("hook") or "").strip()
    joke = str(raw.get("joke") or raw.get("punchline") or "").strip()

    if not hook and not joke:
        return None

    if not hook:
        hook = concept
    if not joke:
        joke = hook

    style = str(raw.get("style", "sarcastic")).strip().lower()
    if style not in VALID_STYLES:
        style = "sarcastic"

    fmt = str(raw.get("format", "pov")).strip().lower()
    if fmt not in VALID_FORMATS:
        fmt = "pov"

    visual_query = str(raw.get("visual_query") or f"{concept} funny meme").strip()

    # Screen text validation
    screen_text = raw.get("screen_text", [])
    sanitized_screen_text = []
    if isinstance(screen_text, list):
        for st in screen_text:
            if isinstance(st, dict) and st.get("text"):
                pos = str(st.get("position", "top")).lower()
                if pos not in ("top", "middle", "bottom"):
                    pos = "top"
                st_style = str(st.get("style", "impact")).lower()
                if st_style not in ("impact", "pill", "subtitle", "bubble"):
                    st_style = "impact"
                sanitized_screen_text.append({
                    "text": str(st["text"]).strip(),
                    "position": pos,
                    "style": st_style
                })

    if not sanitized_screen_text:
        # Generate default screen text from hook and joke
        sanitized_screen_text = [
            {"text": hook, "position": "top", "style": "pill" if fmt == "pov" else "impact"},
            {"text": joke, "position": "bottom", "style": "impact"}
        ]

    # Voice script
    voice_script = str(raw.get("voice_script") or f"{hook}. {joke}").strip()

    # Scores
    scores_raw = raw.get("scores", {})
    sanitized_scores = {}
    total_val = 0.0
    for s_name in REQUIRED_SCORES:
        try:
            val = float(scores_raw.get(s_name, 85))
            val = max(10.0, min(100.0, val))
        except (ValueError, TypeError):
            val = 85.0
        sanitized_scores[s_name] = round(val, 1)
        total_val += val

    quality_score = round(total_val / len(REQUIRED_SCORES), 1)

    title = str(raw.get("title") or f"{hook} 😂 #shorts #memes").strip()
    if "#shorts" not in title.lower():
        title = f"{title} #shorts"

    description = str(raw.get("description") or f"{concept}\n\n#shorts #memes #humor").strip()
    hashtags = raw.get("hashtags", ["#shorts", "#memes", "#humor", "#viral"])
    if not isinstance(hashtags, list):
        hashtags = ["#shorts", "#memes", "#humor"]

    duration = 7.5
    try:
        duration = float(raw.get("duration", 7.5))
        duration = max(4.0, min(15.0, duration))
    except (ValueError, TypeError):
        pass

    return {
        "concept": concept,
        "hook": hook,
        "joke": joke,
        "style": style,
        "format": fmt,
        "visual_query": visual_query,
        "screen_text": sanitized_screen_text,
        "voice_script": voice_script,
        "scores": sanitized_scores,
        "quality_score": quality_score,
        "duration": duration,
        "title": title,
        "description": description,
        "hashtags": hashtags
    }

def validate_meme_generation_response(raw_text: str, default_topic: str = "") -> List[Dict[str, Any]]:
    """Extracts, repairs, and validates meme generation response."""
    data = extract_json_from_text(raw_text)

    memes_raw = []
    if isinstance(data, dict):
        if "memes" in data and isinstance(data["memes"], list):
            memes_raw = data["memes"]
        elif "shorts" in data and isinstance(data["shorts"], list):
            memes_raw = data["shorts"]
        else:
            # Maybe single object
            memes_raw = [data]
    elif isinstance(data, list):
        memes_raw = data
    else:
        raise AIValidationError("Parsed JSON is not a valid list or dictionary structure.")

    valid_memes = []
    seen_hooks = set()

    for item in memes_raw:
        if not isinstance(item, dict):
            continue
        sanitized = sanitize_meme_item(item, default_topic)
        if not sanitized:
            continue

        hook_key = sanitized["hook"].lower()[:40]
        if hook_key in seen_hooks:
            continue
        seen_hooks.add(hook_key)
        valid_memes.append(sanitized)

    if not valid_memes:
        raise AIValidationError("No valid memes could be extracted from AI response.")

    return valid_memes

def validate_regenerate_joke_response(raw_text: str) -> Dict[str, Any]:
    """Validates joke regeneration response."""
    data = extract_json_from_text(raw_text)
    if not isinstance(data, dict):
        raise AIValidationError("Expected dict for joke regeneration response.")

    hook = str(data.get("hook", "")).strip()
    joke = str(data.get("joke", "")).strip()
    screen_text = data.get("screen_text", [])
    voice_script = str(data.get("voice_script", f"{hook}. {joke}")).strip()
    title = str(data.get("title", f"{hook} #shorts #memes")).strip()
    description = str(data.get("description", "")).strip()
    hashtags = data.get("hashtags", ["#shorts", "#memes", "#humor"])

    return {
        "hook": hook,
        "joke": joke,
        "screen_text": screen_text,
        "voice_script": voice_script,
        "title": title,
        "description": description,
        "hashtags": hashtags
    }
