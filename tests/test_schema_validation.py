import pytest
from backend.app.ai.validators import (
    extract_json_from_text,
    validate_clip_candidate_schema,
    validate_and_repair_candidates,
    AIValidationError
)

def test_extract_json_from_markdown():
    raw = """
    Here are the best viral clips:
    ```json
    [
      {
        "title": "Unbelievable Fact",
        "start": 10.5,
        "end": 35.0,
        "hook": "Did you know this?",
        "summary": "Explains a fact",
        "scores": {"hook": 90, "story": 85},
        "decision_reason": "Curiosity hook"
      }
    ]
    ```
    Hope this helps!
    """
    data = extract_json_from_text(raw)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Unbelievable Fact"

def test_extract_json_trailing_comma_repair():
    raw = '[{"title": "Test", "start": 5.0, "end": 20.0, "hook": "h", "summary": "s",},]'
    data = extract_json_from_text(raw)
    assert len(data) == 1
    assert data[0]["start"] == 5.0

def test_validate_candidate_schema_valid():
    candidate = {
        "title": "Secret Revealed",
        "start": 12.0,
        "end": 38.0,
        "hook": "Nobody told you this",
        "summary": "Reveals the secret",
        "scores": {"hook": 95, "story": 90}
    }
    validated = validate_clip_candidate_schema(candidate, max_duration=120.0)
    assert validated["start"] == 12.0
    assert validated["end"] == 38.0
    assert validated["scores"]["hook"] == 95.0

def test_validate_candidate_invalid_timestamps():
    # End before start
    with pytest.raises(AIValidationError):
        validate_clip_candidate_schema({"start": 50.0, "end": 20.0}, max_duration=100.0)

    # Negative start
    v = validate_clip_candidate_schema({"start": -5.0, "end": 25.0}, max_duration=100.0)
    assert v["start"] == 0.0

def test_validate_candidate_too_short():
    with pytest.raises(AIValidationError):
        validate_clip_candidate_schema({"start": 10.0, "end": 14.0}, max_duration=100.0)
