"""
Engine package — filtering, prompt building, and LLM recommendation logic.

Modules:
  - filter: Restaurant filtering by user preferences with fallback
  - prompt_builder: LLM prompt construction (Phase 4)
  - recommender: LLM-powered recommendation engine (Phase 4)
"""

from src.engine.filter import (
    FilterResult,
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

__all__ = [
    "FilterResult",
    "filter_by_budget",
    "filter_by_cuisine",
    "filter_by_location",
    "filter_by_rating",
    "filter_from_preferences",
    "filter_restaurants",
    "get_available_cuisines",
    "get_available_locations",
    "rank_results",
    "suggest_cuisines",
    "suggest_locations",
]
