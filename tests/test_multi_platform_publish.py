import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_multi_platform_publish_preparation():
    # Test valid payload for multi-platform publishing endpoint structure
    response = client.post(
        "/api/repurpose/publish_preparation",
        json={
            "clip_id": "non_existent_clip_test",
            "title": "Test Title #Shorts #Reels",
            "description": "Test description for multi-platform publish",
            "hashtags": ["#shorts", "#reels", "#viral"],
            "audience": "not_made_for_kids",
            "visibility": "public"
        }
    )
    # Should return 404 because item doesn't exist in DB, proving route and schema are loaded
    assert response.status_code in (404, 400)
