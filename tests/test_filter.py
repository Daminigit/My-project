"""
Tests for the filtering engine (Phase 3).

Covers:
  - Individual filters (location, budget, cuisine, rating)
  - Combined filter pipeline
  - Progressive filter relaxation / fallback
  - Case-insensitive matching
  - Multi-cuisine OR filtering
  - Fuzzy matching suggestions
  - Budget boundary values
  - Ranking and top-N capping
  - Edge cases (empty results, invalid budget, etc.)
  - UserPreferences integration
"""

import pandas as pd
import pytest

from src.engine.filter import (
    FilterResult,
    MIN_RESULTS_THRESHOLD,
    apply_filters,
    filter_by_budget,
    filter_by_cuisine,
    filter_by_location,
    filter_by_rating,
    filter_from_preferences,
    filter_restaurants,
    get_available_cuisines,
    get_available_locations,
    rank_results,
    suggest_cuisines,
    suggest_locations,
)
from src.api.schemas import UserPreferences


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_test_df() -> pd.DataFrame:
    """Create a test DataFrame with known data for deterministic testing."""
    return pd.DataFrame(
        {
            "restaurant_name": [
                "Pizza Palace",
                "Curry House",
                "Sushi Spot",
                "Burger Joint",
                "Taco Town",
                "Pasta Place",
                "Biryani Box",
                "Dosa Corner",
                "Noodle Bar",
                "Steak House",
            ],
            "location": [
                "Indiranagar",
                "Indiranagar",
                "Koramangala",
                "Koramangala",
                "Btm",
                "Indiranagar",
                "Btm",
                "Jayanagar",
                "Koramangala",
                "Whitefield",
            ],
            "cuisine": [
                "italian, pizza",
                "north indian, mughlai",
                "japanese, asian",
                "american, burger",
                "mexican",
                "italian, continental",
                "biryani, north indian",
                "south indian",
                "chinese, asian",
                "american, steak",
            ],
            "cost_for_two": [800, 400, 1200, 300, 250, 1600, 350, 150, 500, 2000],
            "rating": [4.5, 4.2, 4.7, 3.8, 3.5, 4.6, 4.0, 4.3, 3.9, 4.8],
            "votes": [5000, 3000, 8000, 1500, 800, 6000, 2000, 4000, 1000, 7000],
            "budget_category": [
                "medium",
                "low",
                "medium",
                "low",
                "low",
                "high",
                "low",
                "low",
                "medium",
                "high",
            ],
            "online_order": ["yes"] * 10,
            "book_table": ["no"] * 10,
            "restaurant_type": ["Casual Dining"] * 10,
            "highlights": [""] * 10,
            "listing_type": ["Delivery"] * 10,
            "city": [
                "Indiranagar",
                "Indiranagar",
                "Koramangala",
                "Koramangala",
                "Btm",
                "Indiranagar",
                "Btm",
                "Jayanagar",
                "Koramangala",
                "Whitefield",
            ],
        }
    )


@pytest.fixture
def test_df():
    """Test DataFrame fixture."""
    return _make_test_df()


# ---------------------------------------------------------------------------
# Tests: Location Filter
# ---------------------------------------------------------------------------


class TestFilterByLocation:
    """Tests for location filtering."""

    def test_exact_match(self, test_df):
        result = filter_by_location(test_df, "Indiranagar")
        assert len(result) == 3
        assert all(result["location"] == "Indiranagar")

    def test_case_insensitive(self, test_df):
        """U-09: Different casing should match."""
        result = filter_by_location(test_df, "indiranagar")
        assert len(result) == 3

    def test_uppercase(self, test_df):
        result = filter_by_location(test_df, "KORAMANGALA")
        assert len(result) == 3

    def test_with_whitespace(self, test_df):
        """U-09: Leading/trailing whitespace should be trimmed."""
        result = filter_by_location(test_df, "  Btm  ")
        assert len(result) == 2

    def test_nonexistent_location(self, test_df):
        result = filter_by_location(test_df, "Nonexistent City")
        assert len(result) == 0

    def test_single_result(self, test_df):
        result = filter_by_location(test_df, "Whitefield")
        assert len(result) == 1
        assert result.iloc[0]["restaurant_name"] == "Steak House"


# ---------------------------------------------------------------------------
# Tests: Budget Filter
# ---------------------------------------------------------------------------


class TestFilterByBudget:
    """Tests for budget filtering."""

    def test_low_budget(self, test_df):
        result = filter_by_budget(test_df, "low")
        # Low = 0-500: Curry House(400), Burger Joint(300), Taco Town(250),
        #              Biryani Box(350), Dosa Corner(150)
        assert len(result) == 5
        assert all(result["cost_for_two"] < 500)

    def test_medium_budget(self, test_df):
        result = filter_by_budget(test_df, "medium")
        # Medium = 500-1500: Pizza Palace(800), Sushi Spot(1200), Noodle Bar(500)
        assert len(result) == 3
        assert all(
            (result["cost_for_two"] >= 500) & (result["cost_for_two"] < 1500)
        )

    def test_high_budget(self, test_df):
        result = filter_by_budget(test_df, "high")
        # High = 1500+: Pasta Place(1600), Steak House(2000)
        assert len(result) == 2
        assert all(result["cost_for_two"] >= 1500)

    def test_boundary_500(self, test_df):
        """F-05: ₹500 should fall in medium (500 <= x < 1500)."""
        result = filter_by_budget(test_df, "medium")
        # Noodle Bar is cost=500, should be in medium
        assert "Noodle Bar" in result["restaurant_name"].values

    def test_boundary_1500(self, test_df):
        """F-05: ₹1500 should fall in high (x >= 1500)."""
        result = filter_by_budget(test_df, "high")
        names = result["restaurant_name"].values
        assert "Pasta Place" in names  # cost=1600
        assert "Steak House" in names  # cost=2000

    def test_unknown_budget_returns_all(self, test_df):
        result = filter_by_budget(test_df, "ultra")
        assert len(result) == len(test_df)

    def test_excludes_zero_cost(self):
        """F-04: Restaurants with cost_for_two <= 0 should be excluded."""
        df = pd.DataFrame(
            {
                "cost_for_two": [0, -100, 300, 500],
                "restaurant_name": ["A", "B", "C", "D"],
            }
        )
        result = filter_by_budget(df, "low")
        assert len(result) == 1
        assert result.iloc[0]["restaurant_name"] == "C"

    def test_case_insensitive_budget(self, test_df):
        result = filter_by_budget(test_df, "LOW")
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Tests: Cuisine Filter
# ---------------------------------------------------------------------------


class TestFilterByCuisine:
    """Tests for cuisine filtering."""

    def test_single_cuisine(self, test_df):
        result = filter_by_cuisine(test_df, "italian")
        assert len(result) == 2  # Pizza Palace, Pasta Place
        names = result["restaurant_name"].values
        assert "Pizza Palace" in names
        assert "Pasta Place" in names

    def test_case_insensitive(self, test_df):
        result = filter_by_cuisine(test_df, "ITALIAN")
        assert len(result) == 2

    def test_partial_match(self, test_df):
        """Cuisine is substring-matched."""
        result = filter_by_cuisine(test_df, "indian")
        # Matches: "north indian" (Curry House, Biryani Box) and "south indian" (Dosa Corner)
        assert len(result) == 3

    def test_multi_cuisine_or(self, test_df):
        """U-11: Multiple cuisines should be OR-filtered."""
        result = filter_by_cuisine(test_df, "italian, japanese")
        assert len(result) == 3  # Pizza Palace, Pasta Place, Sushi Spot

    def test_no_match(self, test_df):
        result = filter_by_cuisine(test_df, "ethiopian")
        assert len(result) == 0

    def test_empty_cuisine(self, test_df):
        result = filter_by_cuisine(test_df, "")
        assert len(result) == len(test_df)

    def test_whitespace_in_multi(self, test_df):
        result = filter_by_cuisine(test_df, " italian , japanese ")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Tests: Rating Filter
# ---------------------------------------------------------------------------


class TestFilterByRating:
    """Tests for rating filtering."""

    def test_min_rating_4(self, test_df):
        result = filter_by_rating(test_df, 4.0)
        assert all(result["rating"] >= 4.0)
        assert len(result) == 7  # All rated 4.0+

    def test_min_rating_4_5(self, test_df):
        result = filter_by_rating(test_df, 4.5)
        assert len(result) == 4  # 4.5, 4.6, 4.7, 4.8

    def test_exact_boundary(self, test_df):
        result = filter_by_rating(test_df, 4.8)
        assert len(result) == 1  # Only Steak House
        assert result.iloc[0]["restaurant_name"] == "Steak House"

    def test_min_rating_1(self, test_df):
        result = filter_by_rating(test_df, 1.0)
        assert len(result) == len(test_df)  # All should pass

    def test_impossible_rating(self, test_df):
        result = filter_by_rating(test_df, 5.0)
        assert len(result) == 0  # No restaurants rated exactly 5.0


# ---------------------------------------------------------------------------
# Tests: Combined Filter Pipeline
# ---------------------------------------------------------------------------


class TestApplyFilters:
    """Tests for the combined filter application."""

    def test_all_filters(self, test_df):
        results, applied = apply_filters(
            test_df,
            location="Indiranagar",
            budget="medium",
            cuisine="italian",
            min_rating=4.0,
        )
        assert len(results) == 1  # Only Pizza Palace
        assert "Pizza Palace" in results["restaurant_name"].values
        assert applied == ["location", "budget", "cuisine", "min_rating"]

    def test_skip_budget(self, test_df):
        results, applied = apply_filters(
            test_df,
            location="Indiranagar",
            budget="medium",
            cuisine="italian",
            min_rating=4.0,
            skip=["budget"],
        )
        # Without budget: Pizza Palace(800,med) + Pasta Place(1600,high)
        assert len(results) == 2
        assert "budget" not in applied

    def test_skip_multiple(self, test_df):
        results, applied = apply_filters(
            test_df,
            location="Indiranagar",
            budget="low",
            cuisine="italian",
            min_rating=4.5,
            skip=["budget", "min_rating"],
        )
        # Indiranagar + Italian = Pizza Palace, Pasta Place
        assert len(results) == 2
        assert "budget" not in applied
        assert "min_rating" not in applied

    def test_no_filters(self, test_df):
        results, applied = apply_filters(test_df)
        assert len(results) == len(test_df)
        assert applied == []

    def test_location_only(self, test_df):
        results, applied = apply_filters(test_df, location="Btm")
        assert len(results) == 2
        assert applied == ["location"]


# ---------------------------------------------------------------------------
# Tests: Progressive Relaxation
# ---------------------------------------------------------------------------


class TestFilterRestaurants:
    """Tests for the full filter_restaurants pipeline with relaxation."""

    def test_no_relaxation_needed(self, test_df):
        """Plenty of results with all filters → no relaxation."""
        result = filter_restaurants(
            test_df,
            location="Indiranagar",
            min_rating=3.0,
        )
        assert result.count >= MIN_RESULTS_THRESHOLD
        assert not result.is_relaxed
        assert result.relaxation_note is None

    def test_budget_relaxation(self, test_df):
        """Not enough results with budget → budget relaxed."""
        result = filter_restaurants(
            test_df,
            location="Koramangala",
            budget="high",
            cuisine="asian",
            min_rating=4.0,
        )
        # High+asian+Koramangala+4.0 → 0 results, relax budget
        # Then: Koramangala+asian+4.0 → Sushi Spot(4.7) only → still < 3
        # Then: Koramangala+asian → Sushi Spot+Noodle Bar → < 3
        # Then: location+cuisine → 2 results → < 3
        # Then: location only → 3 results
        assert result.count >= 1
        assert result.is_relaxed

    def test_zero_results_nonexistent_location(self, test_df):
        """F-01: Unknown location → empty results with suggestion."""
        result = filter_restaurants(
            test_df,
            location="Narnia",
            cuisine="italian",
        )
        assert result.count == 0
        assert result.relaxation_note is not None
        assert "No restaurants found" in result.relaxation_note

    def test_returns_filter_result_type(self, test_df):
        result = filter_restaurants(test_df, location="Indiranagar")
        assert isinstance(result, FilterResult)
        assert isinstance(result.restaurants, pd.DataFrame)

    def test_top_n_cap(self, test_df):
        """F-07: Results capped at top_n."""
        result = filter_restaurants(test_df, top_n=3)
        assert result.count <= 3

    def test_location_only_fallback(self, test_df):
        """When cuisine doesn't match, falls back to location only."""
        result = filter_restaurants(
            test_df,
            location="Whitefield",
            cuisine="ethiopian",
            budget="low",
            min_rating=4.0,
        )
        # Only Steak House in Whitefield, no ethiopian
        # Falls through to location-only
        assert result.count == 1
        assert "Steak House" in result.restaurants["restaurant_name"].values


# ---------------------------------------------------------------------------
# Tests: Ranking
# ---------------------------------------------------------------------------


class TestRankResults:
    """Tests for the ranking function."""

    def test_ranked_by_score(self, test_df):
        ranked = rank_results(test_df)
        # Higher rating × log(votes) should come first
        scores = ranked["rating"].values
        # Not strictly decreasing because score involves votes too,
        # but first entry should be a high scorer
        assert ranked.iloc[0]["rating"] >= 4.5

    def test_respects_top_n(self, test_df):
        ranked = rank_results(test_df, top_n=3)
        assert len(ranked) == 3

    def test_empty_df(self):
        empty = pd.DataFrame(columns=["rating", "votes"])
        ranked = rank_results(empty)
        assert len(ranked) == 0

    def test_top_n_larger_than_df(self, test_df):
        ranked = rank_results(test_df, top_n=100)
        assert len(ranked) == len(test_df)


# ---------------------------------------------------------------------------
# Tests: Utility Functions
# ---------------------------------------------------------------------------


class TestUtilityFunctions:
    """Tests for helper/utility functions."""

    def test_get_available_locations(self, test_df):
        locations = get_available_locations(test_df)
        assert isinstance(locations, list)
        assert len(locations) == 5
        assert locations == sorted(locations)

    def test_get_available_cuisines(self, test_df):
        cuisines = get_available_cuisines(test_df)
        assert isinstance(cuisines, list)
        assert "italian" in cuisines
        assert "pizza" in cuisines
        assert "north indian" in cuisines
        assert cuisines == sorted(cuisines)

    def test_suggest_locations(self, test_df):
        available = get_available_locations(test_df)
        suggestions = suggest_locations("Indranagar", available)  # typo
        assert "Indiranagar" in suggestions

    def test_suggest_cuisines(self, test_df):
        available = get_available_cuisines(test_df)
        suggestions = suggest_cuisines("italain", available)  # typo
        assert "italian" in suggestions

    def test_suggest_no_match(self, test_df):
        available = get_available_locations(test_df)
        suggestions = suggest_locations("xyzabc123", available)
        assert len(suggestions) == 0


# ---------------------------------------------------------------------------
# Tests: UserPreferences Integration
# ---------------------------------------------------------------------------


class TestFilterFromPreferences:
    """Tests for the UserPreferences → filter pipeline."""

    def test_with_preferences_model(self, test_df):
        prefs = UserPreferences(
            location="Indiranagar",
            budget="medium",
            cuisine="italian",
            min_rating=4.0,
        )
        result = filter_from_preferences(test_df, prefs)
        assert isinstance(result, FilterResult)
        assert result.count >= 1

    def test_pydantic_validates_budget(self):
        """U-05: Invalid budget rejected by Pydantic."""
        with pytest.raises(Exception):  # ValidationError
            UserPreferences(
                location="Delhi",
                budget="super high",
                cuisine="Italian",
            )

    def test_pydantic_validates_rating_range(self):
        """U-03: Rating out of range rejected."""
        with pytest.raises(Exception):
            UserPreferences(
                location="Delhi",
                budget="low",
                cuisine="Italian",
                min_rating=6.0,
            )

    def test_pydantic_validates_negative_rating(self):
        """U-03: Negative rating rejected."""
        with pytest.raises(Exception):
            UserPreferences(
                location="Delhi",
                budget="low",
                cuisine="Italian",
                min_rating=-1.0,
            )

    def test_pydantic_rejects_extra_fields(self):
        """A-04: Extra/unknown fields rejected."""
        with pytest.raises(Exception):
            UserPreferences(
                location="Delhi",
                budget="low",
                cuisine="Italian",
                unknown_field="value",
            )

    def test_pydantic_default_rating(self):
        prefs = UserPreferences(
            location="Delhi",
            budget="low",
            cuisine="Italian",
        )
        assert prefs.min_rating == 3.0

    def test_pydantic_optional_preferences(self):
        prefs = UserPreferences(
            location="Delhi",
            budget="low",
            cuisine="Italian",
            preferences="family-friendly, outdoor seating",
        )
        assert prefs.preferences == "family-friendly, outdoor seating"


# ---------------------------------------------------------------------------
# Tests: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases from the Edge-cases.md document."""

    def test_empty_dataframe(self):
        """Empty dataset → empty results."""
        df = pd.DataFrame(
            columns=[
                "restaurant_name", "location", "cuisine",
                "cost_for_two", "rating", "votes",
                "budget_category",
            ]
        )
        result = filter_restaurants(df, location="Delhi", cuisine="Italian")
        assert result.count == 0

    def test_all_identical_ratings(self):
        """F-03: All same rating → still returns results."""
        df = pd.DataFrame(
            {
                "restaurant_name": ["A", "B", "C", "D"],
                "location": ["Delhi", "Delhi", "Delhi", "Delhi"],
                "cuisine": ["italian", "italian", "chinese", "italian"],
                "cost_for_two": [500, 800, 600, 1000],
                "rating": [4.0, 4.0, 4.0, 4.0],
                "votes": [100, 200, 150, 300],
                "budget_category": ["medium", "medium", "medium", "medium"],
            }
        )
        result = filter_restaurants(df, location="Delhi", cuisine="italian")
        assert result.count == 3

    def test_contradictory_preferences(self, test_df):
        """U-12: Impossible combo → relaxation with note."""
        result = filter_restaurants(
            test_df,
            location="Btm",
            budget="high",
            cuisine="ethiopian",
            min_rating=5.0,
        )
        # No high+ethiopian+5.0 in BTM → will relax
        assert result.is_relaxed or result.count == 0

    def test_many_results_capped(self):
        """F-07: Large result set capped at top_n."""
        df = pd.DataFrame(
            {
                "restaurant_name": [f"R{i}" for i in range(100)],
                "location": ["Delhi"] * 100,
                "cuisine": ["italian"] * 100,
                "cost_for_two": [500] * 100,
                "rating": [4.0 + (i % 10) * 0.1 for i in range(100)],
                "votes": [1000 + i * 10 for i in range(100)],
                "budget_category": ["medium"] * 100,
            }
        )
        result = filter_restaurants(df, location="Delhi", top_n=20)
        assert result.count <= 20

    def test_filter_result_properties(self):
        """Verify FilterResult dataclass properties."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        fr = FilterResult(
            restaurants=df,
            relaxation_note="test",
            filters_applied=["location"],
            filters_relaxed=["budget"],
        )
        assert fr.count == 3
        assert fr.is_relaxed is True

        fr2 = FilterResult(restaurants=df)
        assert fr2.is_relaxed is False
        assert fr2.relaxation_note is None
