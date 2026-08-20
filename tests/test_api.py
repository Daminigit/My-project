"""
API Endpoint Tests — Phase 7.5.

Tests all FastAPI endpoints using TestClient.
Covers happy path, bad input (422), and service-unavailable (503) states.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture(scope="module")
def app():
    """Create the FastAPI application for testing."""
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    """Create a TestClient with a pre-loaded dataset fixture."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Sample test DataFrame injected into routes module
# ---------------------------------------------------------------------------

SAMPLE_DF = pd.DataFrame([
    {
        "restaurant_name": "Olive Garden",
        "cuisine": "Italian",
        "location": "Indiranagar",
        "rating": 4.5,
        "cost_for_two": 800,
        "budget_category": "medium",
        "votes": 200,
    },
    {
        "restaurant_name": "Curry House",
        "cuisine": "North Indian",
        "location": "Koramangala",
        "rating": 4.2,
        "cost_for_two": 500,
        "budget_category": "low",
        "votes": 150,
    },
    {
        "restaurant_name": "Sushi World",
        "cuisine": "Japanese",
        "location": "Indiranagar",
        "rating": 4.7,
        "cost_for_two": 1500,
        "budget_category": "high",
        "votes": 300,
    },
])


# ===========================================================================
# Health endpoint
# ===========================================================================

def test_health_check(client):
    """GET /api/health should always return 200 with status: healthy."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ===========================================================================
# Cuisines endpoint
# ===========================================================================

def test_get_cuisines_returns_list(client):
    """GET /api/cuisines should return a JSON object with a 'cuisines' list."""
    with patch("src.api.routes._df", SAMPLE_DF):
        response = client.get("/api/cuisines")
    assert response.status_code == 200
    data = response.json()
    assert "cuisines" in data
    assert isinstance(data["cuisines"], list)
    assert len(data["cuisines"]) > 0


def test_get_cuisines_503_when_no_data(client):
    """GET /api/cuisines should return 503 when dataset is not loaded."""
    with patch("src.api.routes._df", pd.DataFrame()):
        response = client.get("/api/cuisines")
    assert response.status_code == 503


# ===========================================================================
# Locations endpoint
# ===========================================================================

def test_get_locations_returns_list(client):
    """GET /api/locations should return a JSON object with a 'locations' list."""
    with patch("src.api.routes._df", SAMPLE_DF):
        response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert "locations" in data
    assert isinstance(data["locations"], list)
    assert "Indiranagar" in data["locations"]
    assert "Koramangala" in data["locations"]


def test_get_locations_503_when_no_data(client):
    """GET /api/locations should return 503 when dataset is not loaded."""
    with patch("src.api.routes._df", pd.DataFrame()):
        response = client.get("/api/locations")
    assert response.status_code == 503


# ===========================================================================
# Recommend endpoint — Bad Input (422 Validation)
# ===========================================================================

def test_recommend_missing_required_fields(client):
    """POST /api/recommend without required fields should return 422."""
    response = client.post("/api/recommend", json={})
    assert response.status_code == 422


def test_recommend_invalid_budget(client):
    """POST /api/recommend with an invalid budget value should return 422."""
    response = client.post("/api/recommend", json={
        "location": "Indiranagar",
        "budget": "super-cheap",  # Not in Literal["low", "medium", "high"]
        "cuisine": "Italian",
        "min_rating": 4.0,
    })
    assert response.status_code == 422


def test_recommend_rating_out_of_range_high(client):
    """POST /api/recommend with rating > 5.0 should return 422."""
    response = client.post("/api/recommend", json={
        "location": "Indiranagar",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 6.0,
    })
    assert response.status_code == 422


def test_recommend_rating_out_of_range_low(client):
    """POST /api/recommend with rating < 1.0 should return 422."""
    response = client.post("/api/recommend", json={
        "location": "Indiranagar",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 0.5,
    })
    assert response.status_code == 422


def test_recommend_extra_fields_rejected(client):
    """POST /api/recommend with extra fields should return 422 (strict schema)."""
    response = client.post("/api/recommend", json={
        "location": "Indiranagar",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0,
        "unknown_field": "should be rejected",
    })
    assert response.status_code == 422


# ===========================================================================
# Recommend endpoint — 503 when dataset not loaded
# ===========================================================================

def test_recommend_503_when_no_data(client):
    """POST /api/recommend should return 503 when dataset is not loaded."""
    with patch("src.api.routes._df", pd.DataFrame()):
        response = client.post("/api/recommend", json={
            "location": "Indiranagar",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
        })
    assert response.status_code == 503


# ===========================================================================
# Recommend endpoint — Happy Path (mocked LLM)
# ===========================================================================

MOCK_LLM_RESPONSE = '''{
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Olive Garden",
      "cuisine": "Italian",
      "rating": 4.5,
      "cost_for_two": 800,
      "explanation": "Perfect match for Italian cuisine in Indiranagar."
    }
  ],
  "summary": "Here is your top pick for Italian food in Indiranagar."
}'''


def test_recommend_happy_path(client):
    """POST /api/recommend with valid input and mocked LLM should return 200."""
    with patch("src.api.routes._df", SAMPLE_DF), \
         patch("src.engine.recommender.cached_recommendations", return_value=MOCK_LLM_RESPONSE):
        response = client.post("/api/recommend", json={
            "location": "Indiranagar",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
        })

    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "summary" in data
    assert len(data["recommendations"]) >= 1
    first = data["recommendations"][0]
    assert "restaurant_name" in first
    assert "rating" in first
    assert "explanation" in first


def test_recommend_response_structure(client):
    """Verify the full schema of the /api/recommend response."""
    with patch("src.api.routes._df", SAMPLE_DF), \
         patch("src.engine.recommender.cached_recommendations", return_value=MOCK_LLM_RESPONSE):
        response = client.post("/api/recommend", json={
            "location": "Indiranagar",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
        })

    assert response.status_code == 200
    data = response.json()
    for item in data["recommendations"]:
        assert "rank" in item
        assert "restaurant_name" in item
        assert "cuisine" in item
        assert "rating" in item
        assert "cost_for_two" in item
        assert "explanation" in item


def test_recommend_optional_preferences_accepted(client):
    """POST /api/recommend should accept optional 'preferences' field."""
    with patch("src.api.routes._df", SAMPLE_DF), \
         patch("src.engine.recommender.cached_recommendations", return_value=MOCK_LLM_RESPONSE):
        response = client.post("/api/recommend", json={
            "location": "Indiranagar",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
            "preferences": "family-friendly, outdoor seating",
        })
    assert response.status_code == 200
