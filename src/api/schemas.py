"""
Pydantic Request/Response Schemas.

Defines data validation models for API inputs and outputs.
Will be fully implemented in Phase 3 (schemas) and Phase 5 (responses).
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User preference input for restaurant recommendations."""

    location: str = Field(..., description="City or area name", max_length=100)
    budget: Literal["low", "medium", "high"] = Field(
        ..., description="Budget category"
    )
    cuisine: str = Field(..., description="Preferred cuisine type", max_length=100)
    min_rating: float = Field(
        default=3.0, ge=1.0, le=5.0, description="Minimum acceptable rating"
    )
    preferences: Optional[str] = Field(
        default=None,
        description="Additional preferences (e.g., family-friendly)",
        max_length=500,
    )

    model_config = {"extra": "forbid"}


class RecommendationItem(BaseModel):
    """A single restaurant recommendation."""

    rank: int
    restaurant_name: str
    cuisine: str
    rating: float
    cost_for_two: int
    explanation: str


class RecommendationResponse(BaseModel):
    """Full recommendation response from the API."""

    recommendations: List[RecommendationItem]
    summary: str
