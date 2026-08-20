"""
API Route Definitions.

Defines all REST API endpoints for the recommendation system.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import pandas as pd

from src.api.schemas import UserPreferences, RecommendationResponse
from src.engine.filter import get_available_cuisines, get_available_locations, filter_from_preferences
from src.engine.recommender import generate_recommendations
from config.settings import data_config

logger = logging.getLogger(__name__)

router = APIRouter()

# Global variable to hold our dataset
_df: pd.DataFrame = pd.DataFrame()


@router.on_event("startup")
async def load_dataset():
    """Load the dataset into memory on application startup."""
    global _df
    try:
        _df = pd.read_csv(data_config.CACHE_PATH)
        logger.info(f"Successfully loaded dataset with {len(_df)} rows.")
    except Exception as e:
        logger.error(f"Failed to load dataset from {data_config.CACHE_PATH}: {e}")
        # Not raising an exception here to let the app start (e.g. for /health checks)
        # Endpoints will handle the empty df gracefully


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/cuisines")
async def get_cuisines() -> Dict[str, list]:
    """List all available individual cuisines."""
    if _df.empty:
        raise HTTPException(status_code=503, detail="Dataset not loaded.")
    return {"cuisines": get_available_cuisines(_df)}


@router.get("/locations")
async def get_locations() -> Dict[str, list]:
    """List all available locations."""
    if _df.empty:
        raise HTTPException(status_code=503, detail="Dataset not loaded.")
    return {"locations": get_available_locations(_df)}


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(preferences: UserPreferences) -> RecommendationResponse:
    """Get AI-powered restaurant recommendations based on preferences."""
    if _df.empty:
        raise HTTPException(status_code=503, detail="Dataset not loaded.")
        
    # 1. Filter the dataset based on preferences
    filter_result = filter_from_preferences(_df, preferences, top_n=data_config.TOP_N_CANDIDATES)
    
    # 2. Generate LLM recommendations from the filtered candidates
    response = generate_recommendations(
        preferences, 
        filter_result.restaurants, 
        relaxation_note=filter_result.relaxation_note if filter_result.is_relaxed else None
    )
    
    # Optional: Append the filter relaxation note if any (to inform UI)
    if filter_result.is_relaxed and filter_result.relaxation_note:
        response.summary += f" (Note: {filter_result.relaxation_note})"
        
    return response
