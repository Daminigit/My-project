"""
Data package — dataset loading, preprocessing, and storage.

This package provides the complete data pipeline for the Zomato
restaurant recommendation system:

  - loader: Download from HuggingFace with fallback to local cache
  - preprocessor: Clean, normalize, and transform raw data
  - store: Save/load processed data to/from CSV
  - pipeline: Orchestrate the full load → clean → save workflow
"""

from src.data.loader import (
    load_dataset_with_fallback,
    load_from_huggingface,
    load_from_local_cache,
    validate_schema,
)
from src.data.preprocessor import preprocess
from src.data.store import (
    cache_exists,
    delete_cache,
    get_cache_info,
    load_from_csv,
    save_to_csv,
)
from src.data.pipeline import run_pipeline

__all__ = [
    "load_dataset_with_fallback",
    "load_from_huggingface",
    "load_from_local_cache",
    "validate_schema",
    "preprocess",
    "cache_exists",
    "delete_cache",
    "get_cache_info",
    "load_from_csv",
    "save_to_csv",
    "run_pipeline",
]
