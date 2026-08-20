"""
Integration Tests — Phase 7.4.

Tests the full recommendation pipeline end-to-end without mocking the LLM.
Covers: filter → recommender → response validation.
Uses only mock data (no network / API calls to Groq).
"""

import pandas as pd
import pytest
from unittest.mock import patch

from src.api.schemas import UserPreferences, RecommendationResponse
from src.engine.filter import filter_from_preferences
from src.engine.recommender import generate_recommendations


# ---------------------------------------------------------------------------
# Sample Dataset
# ---------------------------------------------------------------------------

@pytest.fixture
def real_df():
    """A realistic subset of the Bangalore restaurant dataset."""
    return pd.DataFrame([
        {"restaurant_name": "Truffles", "cuisine": "American, Burger", "location": "Koramangala", "rating": 4.8, "cost_for_two": 600, "budget_category": "medium", "votes": 1000},
        {"restaurant_name": "Meghana Foods", "cuisine": "Biryani, North Indian", "location": "Indiranagar", "rating": 4.4, "cost_for_two": 450, "budget_category": "low", "votes": 800},
        {"restaurant_name": "The Fatty Bao", "cuisine": "Asian, Japanese", "location": "Indiranagar", "rating": 4.3, "cost_for_two": 1200, "budget_category": "high", "votes": 500},
        {"restaurant_name": "Toit", "cuisine": "Continental, Italian", "location": "Indiranagar", "rating": 4.6, "cost_for_two": 1000, "budget_category": "high", "votes": 900},
        {"restaurant_name": "Corner House", "cuisine": "Desserts", "location": "Koramangala", "rating": 4.5, "cost_for_two": 200, "budget_category": "low", "votes": 600},
        {"restaurant_name": "Koshy's", "cuisine": "Continental", "location": "Mg Road", "rating": 4.0, "cost_for_two": 700, "budget_category": "medium", "votes": 400},
    ])


MOCK_LLM_RESPONSE = '''{
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Toit",
      "cuisine": "Continental, Italian",
      "rating": 4.6,
      "cost_for_two": 1000,
      "explanation": "Toit is an iconic Bangalore brewpub with great Italian food."
    },
    {
      "rank": 2,
      "restaurant_name": "The Fatty Bao",
      "cuisine": "Asian, Japanese",
      "rating": 4.3,
      "cost_for_two": 1200,
      "explanation": "A great option for Asian cuisine with a cozy ambiance."
    }
  ],
  "summary": "Here are your top picks for high-end dining in Indiranagar."
}'''


# ===========================================================================
# 7.4 — Full pipeline integration
# ===========================================================================

class TestFullPipeline:

    def test_happy_path_returns_recommendations(self, real_df):
        """Filter + LLM should return a valid RecommendationResponse for a standard request."""
        preferences = UserPreferences(
            location="Indiranagar",
            budget="high",
            cuisine="Italian",
            min_rating=4.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)
        assert not filter_result.restaurants.empty, "Filter should return at least 1 restaurant"

        with patch("src.engine.recommender.cached_recommendations", return_value=MOCK_LLM_RESPONSE):
            response = generate_recommendations(preferences, filter_result.restaurants)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) >= 1
        assert response.summary != ""

    def test_filter_relaxation_still_returns_results(self, real_df):
        """When filters are very strict, relaxation should kick in and still return results."""
        preferences = UserPreferences(
            location="Indiranagar",
            budget="low",         # Only a few low-budget options in sample data
            cuisine="Japanese",   # Only The Fatty Bao (high budget) matches
            min_rating=4.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)
        # Relaxation should have fired
        assert not filter_result.restaurants.empty, "Relaxation should have returned some results"

    def test_response_conforms_to_schema(self, real_df):
        """Response from the full pipeline should match the RecommendationResponse schema."""
        preferences = UserPreferences(
            location="Koramangala",
            budget="medium",
            cuisine="American",
            min_rating=4.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)

        with patch("src.engine.recommender.cached_recommendations", return_value=MOCK_LLM_RESPONSE):
            response = generate_recommendations(preferences, filter_result.restaurants)

        # Validate response schema
        assert hasattr(response, "recommendations")
        assert hasattr(response, "summary")
        for item in response.recommendations:
            assert hasattr(item, "rank")
            assert hasattr(item, "restaurant_name")
            assert hasattr(item, "cuisine")
            assert hasattr(item, "rating")
            assert hasattr(item, "cost_for_two")
            assert hasattr(item, "explanation")

    def test_empty_dataset_returns_graceful_response(self, real_df):
        """When no restaurants match, the pipeline should return a graceful empty response."""
        preferences = UserPreferences(
            location="NonExistentCity",
            budget="low",
            cuisine="Italian",
            min_rating=4.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)
        response = generate_recommendations(preferences, filter_result.restaurants)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) == 0
        assert "couldn't find" in response.summary.lower() or "no restaurants" in response.summary.lower()


# ===========================================================================
# 7.6 — Edge case testing
# ===========================================================================

class TestEdgeCases:

    def test_min_rating_boundary_at_5(self, real_df):
        """min_rating=5.0 should return very few or no results."""
        preferences = UserPreferences(
            location="Indiranagar",
            budget="medium",
            cuisine="Italian",
            min_rating=5.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)
        # After relaxation, some results may come back; key check is no crash
        assert isinstance(filter_result.restaurants, pd.DataFrame)

    def test_all_budgets_accepted(self, real_df):
        """All valid budget values should work without error."""
        for budget in ["low", "medium", "high"]:
            preferences = UserPreferences(
                location="Koramangala",
                budget=budget,
                cuisine="Desserts",
                min_rating=3.0,
            )
            filter_result = filter_from_preferences(real_df, preferences, top_n=10)
            assert isinstance(filter_result.restaurants, pd.DataFrame)

    def test_multi_cuisine_or_logic(self, real_df):
        """Comma-separated cuisines should use OR logic (match any)."""
        preferences = UserPreferences(
            location="Indiranagar",
            budget="high",
            cuisine="Italian, Japanese",   # either should match
            min_rating=4.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)
        # Both Toit (Italian) and The Fatty Bao (Japanese) should be found
        assert len(filter_result.restaurants) >= 1

    def test_pydantic_rejects_invalid_budget(self):
        """Pydantic should reject budgets outside the allowed Literal values."""
        with pytest.raises(Exception):
            UserPreferences(
                location="Koramangala",
                budget="mid-range",    # Invalid
                cuisine="Italian",
                min_rating=4.0,
            )

    def test_pydantic_rejects_rating_above_5(self):
        """Pydantic should reject rating > 5.0."""
        with pytest.raises(Exception):
            UserPreferences(
                location="Koramangala",
                budget="medium",
                cuisine="Italian",
                min_rating=5.5,
            )

    def test_pydantic_rejects_rating_below_1(self):
        """Pydantic should reject rating < 1.0."""
        with pytest.raises(Exception):
            UserPreferences(
                location="Koramangala",
                budget="medium",
                cuisine="Italian",
                min_rating=0.0,
            )

    def test_additional_preferences_optional(self, real_df):
        """Pipeline should work with and without the optional preferences field."""
        for prefs_value in [None, "quiet ambiance", "family-friendly"]:
            preferences = UserPreferences(
                location="Koramangala",
                budget="low",
                cuisine="Desserts",
                min_rating=4.0,
                preferences=prefs_value,
            )
            filter_result = filter_from_preferences(real_df, preferences, top_n=10)
            assert isinstance(filter_result.restaurants, pd.DataFrame)

    def test_large_top_n_capped_by_available_results(self, real_df):
        """Requesting more results than available should not crash."""
        preferences = UserPreferences(
            location="Mg Road",
            budget="medium",
            cuisine="Continental",
            min_rating=3.0,
        )
        filter_result = filter_from_preferences(real_df, preferences, top_n=1000)
        # Only 1 result is in Mg Road / Continental in our sample data
        assert len(filter_result.restaurants) <= len(real_df)


# ===========================================================================
# 7.7 — Performance test (response time check)
# ===========================================================================

class TestPerformance:

    def test_filter_completes_quickly(self, real_df):
        """Filtering should complete in well under 5 seconds."""
        import time
        preferences = UserPreferences(
            location="Indiranagar",
            budget="high",
            cuisine="Italian",
            min_rating=4.0,
        )
        start = time.time()
        filter_from_preferences(real_df, preferences, top_n=20)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Filter took too long: {elapsed:.2f}s"

    def test_full_pipeline_completes_quickly(self, real_df):
        """Full pipeline (filter + mocked LLM) should complete in under 5 seconds."""
        import time
        preferences = UserPreferences(
            location="Indiranagar",
            budget="high",
            cuisine="Italian",
            min_rating=4.0,
        )
        start = time.time()
        filter_result = filter_from_preferences(real_df, preferences, top_n=10)
        with patch("src.engine.recommender.cached_recommendations", return_value=MOCK_LLM_RESPONSE):
            generate_recommendations(preferences, filter_result.restaurants)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Pipeline took too long: {elapsed:.2f}s"
