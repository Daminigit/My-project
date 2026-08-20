"""
Application Configuration & Environment Variable Management.

Loads settings from .env file and provides typed access
to all configuration values used across the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class LLMConfig:
    """LLM API configuration."""

    PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    MODEL: str = os.getenv("LLM_MODEL", "llama3-8b-8192")
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    @classmethod
    def validate(cls) -> None:
        """Validate that the required API key is set for the chosen provider."""
        if cls.PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is required when LLM_PROVIDER is 'groq'. "
                "Set it in your .env file."
            )


class AppConfig:
    """Application server configuration."""

    NAME: str = os.getenv("APP_NAME", "Zomato AI Recommender")
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


class DataConfig:
    """Dataset and data pipeline configuration."""

    DATASET_NAME: str = os.getenv(
        "DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation"
    )
    CACHE_PATH: str = os.getenv("DATA_CACHE_PATH", "data/zomato_cleaned.csv")
    TOP_N_CANDIDATES: int = int(os.getenv("TOP_N_CANDIDATES", "20"))
    TOP_N_RECOMMENDATIONS: int = int(os.getenv("TOP_N_RECOMMENDATIONS", "5"))

    # Budget mapping (cost_for_two in ₹)
    BUDGET_MAP: dict = {
        "low": (0, 500),
        "medium": (500, 1500),
        "high": (1500, float("inf")),
    }


class CacheConfig:
    """Caching configuration."""

    ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    MAX_ENTRIES: int = int(os.getenv("CACHE_MAX_ENTRIES", "1000"))


class RateLimitConfig:
    """Rate limiting configuration."""

    LIMIT: str = os.getenv("RATE_LIMIT", "10/minute")


# --- Convenience access ---

llm_config = LLMConfig()
app_config = AppConfig()
data_config = DataConfig()
cache_config = CacheConfig()
rate_limit_config = RateLimitConfig()
