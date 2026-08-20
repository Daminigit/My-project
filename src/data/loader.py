"""
HuggingFace Dataset Loader.

Loads the Zomato restaurant dataset from HuggingFace,
with fallback to a local cached CSV. Handles network
failures, schema mismatches, and empty datasets.

Edge cases handled:
  D-01: HuggingFace API down → fallback to local cache
  D-02: Schema changes → validate on load
  D-03: Empty dataset → abort with descriptive error
  D-10: Network timeout → retry with exponential backoff
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Expected columns after loading from HuggingFace (raw schema)
REQUIRED_RAW_COLUMNS = {
    "name",
    "location",
    "cuisines",
    "approx_cost(for two people)",
    "rate",
    "votes",
}

# Maximum retries for HuggingFace download
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds


def load_from_huggingface(
    dataset_name: str,
    max_retries: int = MAX_RETRIES,
) -> pd.DataFrame:
    """
    Load dataset from HuggingFace with retry and exponential backoff.

    Args:
        dataset_name: HuggingFace dataset identifier.
        max_retries: Maximum number of retry attempts.

    Returns:
        Raw DataFrame from the HuggingFace dataset.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    from datasets import load_dataset

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Loading dataset '%s' from HuggingFace (attempt %d/%d)...",
                dataset_name,
                attempt,
                max_retries,
            )
            dataset = load_dataset(dataset_name, split="train")
            df = dataset.to_pandas()
            logger.info(
                "Successfully loaded %d rows from HuggingFace.", len(df)
            )
            return df

        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                wait = RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    "HuggingFace load attempt %d failed: %s. "
                    "Retrying in %ds...",
                    attempt,
                    exc,
                    wait,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "All %d HuggingFace download attempts failed.", max_retries
                )

    raise RuntimeError(
        f"Failed to load dataset from HuggingFace after {max_retries} "
        f"attempts. Last error: {last_error}"
    )


def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains all required columns.

    Args:
        df: The DataFrame to validate.

    Raises:
        ValueError: If required columns are missing.
    """
    missing = REQUIRED_RAW_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset schema mismatch — missing columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )
    logger.info("Schema validation passed. All required columns present.")


def load_from_local_cache(cache_path: str) -> pd.DataFrame:
    """
    Load dataset from a local CSV cache file.

    Args:
        cache_path: Path to the cached CSV file.

    Returns:
        DataFrame loaded from the local CSV.

    Raises:
        FileNotFoundError: If no cache file exists.
    """
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f"No local cache found at '{cache_path}'. "
            "Cannot proceed without data."
        )

    logger.info("Loading dataset from local cache: %s", cache_path)
    df = pd.read_csv(cache_path)
    logger.info("Loaded %d rows from local cache.", len(df))
    return df


def load_dataset_with_fallback(
    dataset_name: str,
    cache_path: str,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Load the Zomato dataset with HuggingFace-first strategy and local
    cache fallback.

    Strategy:
      1. If force_refresh=False and a local cache exists, use it.
      2. Otherwise, download from HuggingFace.
      3. If HuggingFace fails, fall back to local cache (if available).

    Args:
        dataset_name: HuggingFace dataset identifier.
        cache_path: Path to local CSV cache.
        force_refresh: If True, always download fresh from HuggingFace.

    Returns:
        Raw DataFrame (not yet preprocessed).

    Raises:
        RuntimeError: If no data source is available.
        ValueError: If dataset is empty or schema is invalid.
    """
    # Try local cache first (unless forced refresh)
    if not force_refresh and os.path.exists(cache_path):
        logger.info("Using existing local cache at '%s'.", cache_path)
        df = load_from_local_cache(cache_path)
        if len(df) == 0:
            raise ValueError(
                "Local cache is empty. Delete it and re-run with "
                "force_refresh=True."
            )
        return df

    # Download from HuggingFace
    try:
        df = load_from_huggingface(dataset_name)
        validate_schema(df)

        if len(df) == 0:
            raise ValueError(
                "Dataset loaded from HuggingFace is empty (0 rows). "
                "Cannot proceed."
            )

        return df

    except Exception as exc:
        logger.warning(
            "HuggingFace unavailable: %s. Attempting local cache fallback...",
            exc,
        )

        try:
            df = load_from_local_cache(cache_path)
            if len(df) == 0:
                raise ValueError("Fallback cache is also empty.")
            return df
        except FileNotFoundError:
            raise RuntimeError(
                "No dataset available: HuggingFace download failed and "
                f"no local cache exists at '{cache_path}'. "
                f"Original error: {exc}"
            ) from exc
