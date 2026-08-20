"""
User Preference Filtering Engine.

Filters restaurants based on location, budget, cuisine, and rating.
Includes progressive fallback logic when too few results are found.

Edge cases handled:
  F-01: Zero matches → progressive filter relaxation
  F-02: Fewer than desired results → return available + note
  F-04: Invalid cost values → exclude cost_for_two <= 0
  F-05: Budget boundary values → inclusive ranges
  F-07: Too many results → cap by relevance score
  U-09: Case-insensitive location matching
  U-10: Misspelled cuisine → fuzzy matching suggestions
  U-11: Multiple cuisines → OR filter
"""

import logging
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import List, Optional, Tuple

import pandas as pd

from config.settings import data_config

logger = logging.getLogger(__name__)

# Budget mapping from config
BUDGET_MAP = data_config.BUDGET_MAP

# Number of candidate restaurants to send to LLM
TOP_N_CANDIDATES = data_config.TOP_N_CANDIDATES

# Minimum results before triggering fallback
MIN_RESULTS_THRESHOLD = 3


@dataclass
class FilterResult:
    """Result of a filter operation, including metadata about relaxation."""

    restaurants: pd.DataFrame
    relaxation_note: Optional[str] = None
    filters_applied: list = field(default_factory=list)
    filters_relaxed: list = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.restaurants)

    @property
    def is_relaxed(self) -> bool:
        return len(self.filters_relaxed) > 0


# ---------------------------------------------------------------------------
# Individual Filters
# ---------------------------------------------------------------------------


def filter_by_location(
    df: pd.DataFrame,
    location: str,
) -> pd.DataFrame:
    """
    Filter restaurants by location (case-insensitive).

    Normalizes both the input and dataset locations to title case
    for consistent matching (handles U-09).

    Args:
        df: Restaurant DataFrame.
        location: Target location name.

    Returns:
        Filtered DataFrame.
    """
    normalized_location = location.strip().title()
    return df[df["location"].str.strip().str.title() == normalized_location]


def filter_by_budget(
    df: pd.DataFrame,
    budget: str,
    budget_map: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Filter restaurants by budget category.

    Uses inclusive ranges (F-05):
      - low:    ₹0 – ₹500  (0 <= cost < 500)
      - medium: ₹500 – ₹1500  (500 <= cost < 1500)
      - high:   ₹1500+  (cost >= 1500)

    Also excludes restaurants with cost_for_two <= 0 (F-04).

    Args:
        df: Restaurant DataFrame.
        budget: One of "low", "medium", "high".
        budget_map: Optional override for budget ranges.

    Returns:
        Filtered DataFrame.
    """
    bmap = budget_map or BUDGET_MAP
    budget_key = budget.lower().strip()

    if budget_key not in bmap:
        logger.warning("Unknown budget '%s'. Skipping budget filter.", budget)
        return df

    low, high = bmap[budget_key]

    # Exclude invalid costs (F-04)
    valid_cost = df["cost_for_two"] > 0

    if high == float("inf"):
        return df[valid_cost & (df["cost_for_two"] >= low)]
    else:
        return df[valid_cost & (df["cost_for_two"] >= low) & (df["cost_for_two"] < high)]


def filter_by_cuisine(
    df: pd.DataFrame,
    cuisine: str,
) -> pd.DataFrame:
    """
    Filter restaurants by cuisine (case-insensitive, supports multi-cuisine).

    Handles:
      - Single cuisine: "italian"
      - Multiple cuisines (U-11): "italian, chinese" → OR match

    Args:
        df: Restaurant DataFrame.
        cuisine: Comma-separated cuisine preference(s).

    Returns:
        Filtered DataFrame.
    """
    # Split multi-cuisine input
    cuisine_terms = [c.strip().lower() for c in cuisine.split(",")]
    cuisine_terms = [c for c in cuisine_terms if c]

    if not cuisine_terms:
        return df

    # Build OR condition: match any of the requested cuisines
    mask = pd.Series(False, index=df.index)
    for term in cuisine_terms:
        mask = mask | df["cuisine"].str.contains(term, case=False, na=False)

    return df[mask]


def filter_by_rating(
    df: pd.DataFrame,
    min_rating: float,
) -> pd.DataFrame:
    """
    Filter restaurants by minimum rating.

    Args:
        df: Restaurant DataFrame.
        min_rating: Minimum acceptable rating (1.0–5.0).

    Returns:
        Filtered DataFrame with rating >= min_rating.
    """
    return df[df["rating"] >= min_rating]


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def get_available_locations(df: pd.DataFrame) -> List[str]:
    """Get sorted list of unique locations in the dataset."""
    return sorted(df["location"].dropna().unique().tolist())


def get_available_cuisines(df: pd.DataFrame) -> List[str]:
    """
    Get list of unique individual cuisines sorted by frequency (most common first).

    Splits comma-separated cuisine strings into individual items.
    """
    cuisine_counts: dict = {}
    for cuisine_str in df["cuisine"].dropna():
        for item in str(cuisine_str).split(","):
            cleaned = item.strip().lower()
            if cleaned:
                cuisine_counts[cleaned] = cuisine_counts.get(cleaned, 0) + 1
    # Sort by count descending, then alphabetically for ties
    return [c for c, _ in sorted(cuisine_counts.items(), key=lambda x: (-x[1], x[0]))]


def suggest_locations(
    location: str,
    available: List[str],
    n: int = 5,
    cutoff: float = 0.5,
) -> List[str]:
    """
    Suggest similar locations using fuzzy matching (U-10 style).

    Args:
        location: User-provided location.
        available: List of available locations.
        n: Number of suggestions to return.
        cutoff: Minimum similarity score.

    Returns:
        List of similar location names.
    """
    return get_close_matches(
        location.strip().title(), available, n=n, cutoff=cutoff
    )


def suggest_cuisines(
    cuisine: str,
    available: List[str],
    n: int = 5,
    cutoff: float = 0.5,
) -> List[str]:
    """
    Suggest similar cuisines using fuzzy matching (U-10).

    Args:
        cuisine: User-provided cuisine.
        available: List of available cuisines.
        n: Number of suggestions to return.
        cutoff: Minimum similarity score.

    Returns:
        List of similar cuisine names.
    """
    return get_close_matches(
        cuisine.strip().lower(), available, n=n, cutoff=cutoff
    )


def rank_results(df: pd.DataFrame, top_n: int = TOP_N_CANDIDATES) -> pd.DataFrame:
    """
    Rank and limit results by a relevance score.

    Score = rating × log(votes + 1) to balance quality and popularity.
    Caps results at top_n (F-07).

    Args:
        df: Filtered DataFrame.
        top_n: Maximum number of results to return.

    Returns:
        Top-N ranked DataFrame.
    """
    import numpy as np

    if len(df) == 0:
        return df

    df = df.copy()
    df["_score"] = df["rating"] * np.log1p(df["votes"])
    df = df.sort_values("_score", ascending=False)
    df = df.drop(columns=["_score"])

    return df.head(top_n).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Combined Filter Pipeline
# ---------------------------------------------------------------------------


def apply_filters(
    df: pd.DataFrame,
    location: Optional[str] = None,
    budget: Optional[str] = None,
    cuisine: Optional[str] = None,
    min_rating: Optional[float] = None,
    skip: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Apply filters selectively, skipping any filters in the `skip` list.

    Args:
        df: Restaurant DataFrame.
        location: Location filter value.
        budget: Budget filter value.
        cuisine: Cuisine filter value.
        min_rating: Minimum rating filter value.
        skip: List of filter names to skip (e.g., ["budget", "min_rating"]).

    Returns:
        Tuple of (filtered_df, list_of_applied_filter_names).
    """
    skip = set(skip or [])
    results = df.copy()
    applied = []

    if location and "location" not in skip:
        results = filter_by_location(results, location)
        applied.append("location")

    if budget and "budget" not in skip:
        results = filter_by_budget(results, budget)
        applied.append("budget")

    if cuisine and "cuisine" not in skip:
        results = filter_by_cuisine(results, cuisine)
        applied.append("cuisine")

    if min_rating is not None and "min_rating" not in skip:
        results = filter_by_rating(results, min_rating)
        applied.append("min_rating")

    return results, applied


def filter_restaurants(
    df: pd.DataFrame,
    location: Optional[str] = None,
    budget: Optional[str] = None,
    cuisine: Optional[str] = None,
    min_rating: Optional[float] = None,
    top_n: int = TOP_N_CANDIDATES,
) -> FilterResult:
    """
    Filter restaurants by user preferences with progressive fallback.

    Implements the relaxation strategy from the edge case doc:
      1. All filters
      2. Drop budget
      3. Drop budget + rating
      4. Location + cuisine only
      5. Location only
      6. No results → return empty with message

    Args:
        df: Full restaurant DataFrame.
        location: Location filter value.
        budget: Budget category ("low", "medium", "high").
        cuisine: Cuisine preference(s).
        min_rating: Minimum acceptable rating.
        top_n: Max results to return.

    Returns:
        FilterResult with restaurants, relaxation notes, and metadata.
    """
    logger.info(
        "Filtering: location=%s, budget=%s, cuisine=%s, min_rating=%s",
        location,
        budget,
        cuisine,
        min_rating,
    )

    # Attempt 1: All filters
    results, applied = apply_filters(df, location, budget, cuisine, min_rating)
    if len(results) >= MIN_RESULTS_THRESHOLD:
        logger.info("All filters applied. %d results found.", len(results))
        return FilterResult(
            restaurants=rank_results(results, top_n),
            filters_applied=applied,
        )

    # Attempt 2: Relax budget filter
    results, applied = apply_filters(
        df, location, budget, cuisine, min_rating, skip=["budget"]
    )
    if len(results) >= MIN_RESULTS_THRESHOLD:
        logger.info(
            "Budget filter relaxed. %d results found.", len(results)
        )
        return FilterResult(
            restaurants=rank_results(results, top_n),
            relaxation_note="Budget filter relaxed for more options.",
            filters_applied=applied,
            filters_relaxed=["budget"],
        )

    # Attempt 3: Relax budget + rating
    results, applied = apply_filters(
        df, location, budget, cuisine, min_rating, skip=["budget", "min_rating"]
    )
    if len(results) >= MIN_RESULTS_THRESHOLD:
        logger.info(
            "Budget and rating filters relaxed. %d results found.",
            len(results),
        )
        return FilterResult(
            restaurants=rank_results(results, top_n),
            relaxation_note="Budget and rating filters relaxed for more options.",
            filters_applied=applied,
            filters_relaxed=["budget", "min_rating"],
        )

    # Attempt 4: Location + cuisine only
    if location and cuisine:
        results, applied = apply_filters(
            df, location, None, cuisine, None, skip=["budget", "min_rating"]
        )
        if len(results) >= 1:
            logger.info(
                "Location + cuisine only. %d results found.", len(results)
            )
            return FilterResult(
                restaurants=rank_results(results, top_n),
                relaxation_note="Showing all matching restaurants in your area.",
                filters_applied=applied,
                filters_relaxed=["budget", "min_rating"],
            )

    # Attempt 5: Location only
    if location:
        results = filter_by_location(df, location)
        if len(results) >= 1:
            logger.info(
                "Location only. %d results found.", len(results)
            )
            return FilterResult(
                restaurants=rank_results(results, top_n),
                relaxation_note="Showing popular restaurants in your location.",
                filters_applied=["location"],
                filters_relaxed=["budget", "cuisine", "min_rating"],
            )

    # Attempt 6: No results at all
    logger.warning(
        "No restaurants found for: location=%s, cuisine=%s",
        location,
        cuisine,
    )

    # Build helpful suggestions
    suggestions = []
    if location:
        available_locs = get_available_locations(df)
        similar = suggest_locations(location, available_locs)
        if similar:
            suggestions.append(f"Similar locations: {', '.join(similar)}")

    note = "No restaurants found. Try a different location."
    if suggestions:
        note += " " + " | ".join(suggestions)

    return FilterResult(
        restaurants=pd.DataFrame(),
        relaxation_note=note,
        filters_applied=[],
        filters_relaxed=["location", "budget", "cuisine", "min_rating"],
    )


def filter_from_preferences(
    df: pd.DataFrame,
    preferences,
    top_n: int = TOP_N_CANDIDATES,
) -> FilterResult:
    """
    Convenience wrapper that accepts a UserPreferences Pydantic model.

    Args:
        df: Full restaurant DataFrame.
        preferences: UserPreferences model instance.
        top_n: Max results to return.

    Returns:
        FilterResult with matched restaurants.
    """
    return filter_restaurants(
        df=df,
        location=preferences.location,
        budget=preferences.budget,
        cuisine=preferences.cuisine,
        min_rating=preferences.min_rating,
        top_n=top_n,
    )
