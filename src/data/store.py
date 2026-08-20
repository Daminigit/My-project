"""
Data Persistence Layer.

Handles saving and loading the processed Zomato dataset to/from
local CSV storage. Provides cache-aware operations to avoid
redundant re-processing.
"""

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def save_to_csv(
    df: pd.DataFrame,
    path: str,
    create_dirs: bool = True,
) -> str:
    """
    Save a DataFrame to CSV.

    Args:
        df: The DataFrame to save.
        path: Target file path (e.g., "data/zomato_cleaned.csv").
        create_dirs: If True, create parent directories if they don't exist.

    Returns:
        The absolute path where the file was saved.
    """
    abs_path = os.path.abspath(path)

    if create_dirs:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    df.to_csv(abs_path, index=False)
    file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)

    logger.info(
        "Saved %d rows to '%s' (%.2f MB).",
        len(df),
        abs_path,
        file_size_mb,
    )
    return abs_path


def load_from_csv(path: str) -> pd.DataFrame:
    """
    Load a DataFrame from a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        The loaded DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the loaded file is empty.
    """
    abs_path = os.path.abspath(path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Data file not found: '{abs_path}'")

    df = pd.read_csv(abs_path)

    if len(df) == 0:
        raise ValueError(f"Data file is empty: '{abs_path}'")

    logger.info("Loaded %d rows from '%s'.", len(df), abs_path)
    return df


def cache_exists(path: str) -> bool:
    """Check whether a cached data file exists and is non-empty."""
    abs_path = os.path.abspath(path)

    if not os.path.exists(abs_path):
        return False

    # Check file is not empty (at least has a header row)
    file_size = os.path.getsize(abs_path)
    if file_size == 0:
        logger.warning("Cache file exists but is empty: '%s'", abs_path)
        return False

    return True


def get_cache_info(path: str) -> Optional[dict]:
    """
    Get metadata about a cached data file.

    Returns:
        Dict with keys: path, size_mb, row_count, modified_time.
        None if cache doesn't exist.
    """
    abs_path = os.path.abspath(path)

    if not cache_exists(path):
        return None

    import time

    file_stat = os.stat(abs_path)

    try:
        df = pd.read_csv(abs_path, nrows=0)  # Read header only
        col_count = len(df.columns)

        # Count rows without loading full file
        with open(abs_path, "r") as f:
            row_count = sum(1 for _ in f) - 1  # Subtract header
    except Exception:
        col_count = 0
        row_count = 0

    return {
        "path": abs_path,
        "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
        "row_count": row_count,
        "column_count": col_count,
        "modified_time": time.ctime(file_stat.st_mtime),
    }


def delete_cache(path: str) -> bool:
    """
    Delete a cached data file.

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    abs_path = os.path.abspath(path)

    if os.path.exists(abs_path):
        os.remove(abs_path)
        logger.info("Deleted cache file: '%s'", abs_path)
        return True

    return False
