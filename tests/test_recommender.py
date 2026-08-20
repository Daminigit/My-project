import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.api.schemas import UserPreferences, RecommendationResponse
from src.engine.prompt_builder import build_messages, build_system_prompt
from src.engine.recommender import generate_recommendations, parse_llm_response


@pytest.fixture
def sample_preferences():
    return UserPreferences(
        location="Delhi",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        preferences="family-friendly"
    )


@pytest.fixture
def sample_restaurants():
    return pd.DataFrame([
        {
            "restaurant_name": "Olive Bar & Kitchen",
            "cuisine": "Italian, Mediterranean",
            "rating": 4.6,
            "cost_for_two": 1200
        },
        {
            "restaurant_name": "Tonino",
            "cuisine": "Italian",
            "rating": 4.4,
            "cost_for_two": 1100
        }
    ])


def test_build_system_prompt():
    prompt = build_system_prompt()
    assert "expert restaurant recommendation assistant" in prompt
    assert "JSON object" in prompt


def test_build_messages(sample_preferences, sample_restaurants):
    messages = build_messages(sample_preferences, sample_restaurants)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    
    user_content = messages[1]["content"]
    assert "Italian" in user_content
    assert "Delhi" in user_content
    assert "Olive Bar & Kitchen" in user_content


def test_parse_llm_response_valid():
    valid_json = '''
    {
      "recommendations": [
        {
          "rank": 1,
          "restaurant_name": "Olive Bar & Kitchen",
          "cuisine": "Italian, Mediterranean",
          "rating": 4.6,
          "cost_for_two": 1200,
          "explanation": "Great family place."
        }
      ],
      "summary": "Here are your top picks!"
    }
    '''
    response = parse_llm_response(valid_json)
    assert isinstance(response, RecommendationResponse)
    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant_name == "Olive Bar & Kitchen"


def test_parse_llm_response_invalid():
    invalid_json = '{"bad_key": "value"}'
    response = parse_llm_response(invalid_json)
    # The parser currently falls back to returning a RecommendationResponse with empty list on ValidationError
    assert isinstance(response, RecommendationResponse)
    assert len(response.recommendations) == 0
    assert "Failed to generate recommendations" in response.summary


@patch('src.engine.recommender.cached_recommendations')
def test_generate_recommendations_empty_df(mock_cache, sample_preferences):
    empty_df = pd.DataFrame()
    response = generate_recommendations(sample_preferences, empty_df)
    
    assert len(response.recommendations) == 0
    assert "couldn't find any restaurants" in response.summary
    mock_cache.assert_not_called()


@patch('src.engine.recommender.cached_recommendations')
def test_generate_recommendations_success(mock_cache, sample_preferences, sample_restaurants):
    valid_json = '''
    {
      "recommendations": [
        {
          "rank": 1,
          "restaurant_name": "Olive Bar & Kitchen",
          "cuisine": "Italian, Mediterranean",
          "rating": 4.6,
          "cost_for_two": 1200,
          "explanation": "Great family place."
        }
      ],
      "summary": "Here are your top picks!"
    }
    '''
    mock_cache.return_value = valid_json
    
    response = generate_recommendations(sample_preferences, sample_restaurants)
    assert len(response.recommendations) == 1
    assert response.summary == "Here are your top picks!"
    mock_cache.assert_called_once()
