"""
Data Pipeline — Orchestrates the full load → clean → save workflow.

This module ties together the loader, preprocessor, and store to
provide a single entry point for the data ingestion pipeline.

Usage:
    from src.data.pipeline import run_pipeline

    df = run_pipeline()                    # Uses defaults from settings
    df = run_pipeline(force_refresh=True)  # Force re-download from HuggingFace
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from src.data.loader import load_dataset_with_fallback
from src.data.preprocessor import preprocess
from src.data.store import cache_exists, get_cache_info, load_from_csv, save_to_csv

logger = logging.getLogger(__name__)


def run_pipeline(
    dataset_name: Optional[str] = None,
    cache_path: Optional[str] = None,
    force_refresh: bool = False,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Execute the full data pipeline: load → preprocess → save.

    Args:
        dataset_name: HuggingFace dataset name.
            Defaults to value from config/settings.py.
        cache_path: Path to save the cleaned CSV.
            Defaults to value from config/settings.py.
        force_refresh: If True, re-download from HuggingFace even if
            a local cache exists.
        max_rows: Optional limit on number of rows to process.

    Returns:
        The cleaned, preprocessed DataFrame.
    """
    # Import settings lazily to avoid circular imports
    from config.settings import data_config

    dataset_name = dataset_name or data_config.DATASET_NAME
    cache_path = cache_path or data_config.CACHE_PATH

    logger.info("=" * 60)
    logger.info("STARTING DATA PIPELINE")
    logger.info("=" * 60)
    logger.info("Dataset: %s", dataset_name)
    logger.info("Cache path: %s", cache_path)
    logger.info("Force refresh: %s", force_refresh)

    # If not refreshing and we have a clean cache, just load it
    if not force_refresh and cache_exists(cache_path):
        info = get_cache_info(cache_path)
        logger.info(
            "Clean cache found: %d rows, %.2f MB (modified: %s).",
            info["row_count"],
            info["size_mb"],
            info["modified_time"],
        )
        df = load_from_csv(cache_path)
        logger.info("Pipeline complete (from cache). %d rows ready.", len(df))
        return df

    # Step 1: Load raw data
    logger.info("Step 1/3: Loading raw dataset...")
    raw_df = load_dataset_with_fallback(
        dataset_name=dataset_name,
        cache_path=cache_path,
        force_refresh=force_refresh,
    )
    logger.info("Raw dataset: %d rows × %d columns.", len(raw_df), len(raw_df.columns))

    # Step 2: Preprocess
    logger.info("Step 2/3: Preprocessing...")
    clean_df = preprocess(raw_df, max_rows=max_rows)

    # Step 3: Save to cache
    logger.info("Step 3/3: Saving to cache...")
    saved_path = save_to_csv(clean_df, cache_path)

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("  Rows: %d (from %d raw)", len(clean_df), len(raw_df))
    logger.info("  Columns: %s", list(clean_df.columns))
    logger.info("  Saved to: %s", saved_path)
    logger.info("=" * 60)

    return clean_df


def main():
    """CLI entry point for running the data pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Zomato data ingestion & preprocessing pipeline."
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-download from HuggingFace (ignore local cache).",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Limit the number of rows to process.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Override the HuggingFace dataset name.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override the output CSV path.",
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        df = run_pipeline(
            dataset_name=args.dataset,
            cache_path=args.output,
            force_refresh=args.force_refresh,
            max_rows=args.max_rows,
        )
        print(f"\n✅ Pipeline successful! {len(df)} restaurants ready.")
        print(f"\nSample data:")
        print(df.head(3).to_string(index=False))
        print(f"\nBudget distribution:")
        print(df["budget_category"].value_counts().to_string())
        print(f"\nTop 5 locations:")
        print(df["location"].value_counts().head(5).to_string())

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
