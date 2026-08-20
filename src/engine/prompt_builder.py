"""
LLM Prompt Builder.

Constructs structured prompts for the LLM from user preferences
and filtered restaurant data.
"""

from typing import List, Dict, Any
from src.api.schemas import UserPreferences
import pandas as pd


def build_system_prompt() -> str:
    """Creates the system prompt establishing the persona."""
    return (
        "You are an expert restaurant recommendation assistant. "
        "Given a list of restaurants and user preferences, rank the "
        "top 5 restaurants and explain why each is a great fit. "
        "Return a JSON object containing a 'recommendations' array with fields: "
        "rank, restaurant_name, cuisine, rating, cost_for_two, and explanation. "
        "Also include a 'summary' string summarizing the top picks."
    )


def build_user_context(preferences: UserPreferences, relaxation_note: str = None) -> str:
    """Formats the user's constraints into a prompt string."""
    context = (
        f"I'm looking for {preferences.cuisine} restaurants in {preferences.location} "
        f"with a {preferences.budget} budget. Minimum rating: {preferences.min_rating}."
    )
    if preferences.preferences:
        context += f"\nAdditional preferences: {preferences.preferences}"
    if relaxation_note:
        context += (
            f"\n\nIMPORTANT NOTE: We couldn't find a perfect match, so we relaxed some filters. "
            f"{relaxation_note} Please explicitly acknowledge this in your explanation and DO NOT "
            f"claim that a restaurant perfectly matches their original criteria if it does not."
        )
    return context


def build_restaurant_data(restaurants_df: pd.DataFrame) -> str:
    """Formats the matched restaurants into a structured string for the LLM."""
    if restaurants_df.empty:
        return "No matching restaurants found based on the strict filters."

    data_str = "Here are the matching restaurants:\n"
    for i, row in enumerate(restaurants_df.itertuples(), start=1):
        data_str += (
            f"{i}. Name: {row.restaurant_name}, Cuisine: {row.cuisine}, "
            f"Rating: {row.rating}, Cost for two: {row.cost_for_two}\n"
        )
    return data_str


def build_messages(preferences: UserPreferences, restaurants_df: pd.DataFrame, relaxation_note: str = None) -> List[Dict[str, str]]:
    """Assembles the full chat messages array compatible with Groq API."""
    system_prompt = build_system_prompt()
    user_context = build_user_context(preferences, relaxation_note)
    restaurant_data = build_restaurant_data(restaurants_df)

    user_message_content = f"{user_context}\n\n{restaurant_data}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message_content},
    ]
    return messages
