"""
LLM Recommendation Engine.

Interacts with the Groq API to generate ranked restaurant
recommendations with explanations.
"""

import json
from typing import Dict, Any, List
from functools import lru_cache
import pandas as pd
from groq import Groq
from pydantic import ValidationError

from src.api.schemas import UserPreferences, RecommendationResponse
from config.settings import llm_config
from src.engine.prompt_builder import build_messages

# Initialize the Groq client lazily
_client = None

def get_llm_client() -> Groq:
    """Returns a singleton instance of the Groq client."""
    global _client
    if _client is None:
        llm_config.validate()
        _client = Groq(api_key=llm_config.GROQ_API_KEY)
    return _client


@lru_cache(maxsize=100)
def cached_recommendations(preferences_json: str, restaurants_json: str) -> str:
    """
    Cached wrapper for calling the LLM. 
    Uses JSON strings for hashability.
    """
    preferences = UserPreferences.model_validate_json(preferences_json)
    restaurants_df = pd.read_json(restaurants_json, orient="records")
    
    messages = build_messages(preferences, restaurants_df)
    client = get_llm_client()

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=llm_config.MODEL,
            temperature=llm_config.TEMPERATURE,
            max_tokens=llm_config.MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        # If API call fails, return a JSON error
        return json.dumps({"error": str(e)})


def parse_llm_response(response_str: str) -> RecommendationResponse:
    """Parses the raw JSON string from Groq into a RecommendationResponse model."""
    try:
        data = json.loads(response_str)
        if "error" in data:
            raise ValueError(f"LLM API Error: {data['error']}")
        
        # Validate against schema
        return RecommendationResponse(**data)
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        # Fallback or error propagation
        # For simplicity, returning a mock fallback response
        return RecommendationResponse(
            recommendations=[],
            summary=f"Failed to generate recommendations: {str(e)}"
        )


def generate_recommendations(preferences: UserPreferences, restaurants_df: pd.DataFrame) -> RecommendationResponse:
    """Main entry point to generate recommendations."""
    if restaurants_df.empty:
        return RecommendationResponse(
            recommendations=[],
            summary="I'm sorry, I couldn't find any restaurants matching your strict preferences. Try relaxing some criteria."
        )

    # Convert to JSON for caching
    pref_json = preferences.model_dump_json()
    # Serialize only necessary columns for caching
    cols_to_serialize = ["restaurant_name", "cuisine", "rating", "cost_for_two"]
    # Check if df has these columns, else serialize all
    if all(col in restaurants_df.columns for col in cols_to_serialize):
        df_json = restaurants_df[cols_to_serialize].to_json(orient="records")
    else:
        df_json = restaurants_df.to_json(orient="records")

    raw_response = cached_recommendations(pref_json, df_json)
    return parse_llm_response(raw_response)
