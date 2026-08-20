"""
Data Preprocessor.

Cleans, normalizes, and transforms raw Zomato restaurant data into
a structured format suitable for filtering and recommendation.

Preprocessing pipeline:
  1. Drop rows with null restaurant_name or rating
  2. Remove duplicate entries
  3. Normalize cuisine labels (lowercase, strip whitespace)
  4. Map cost_for_two to budget categories (low/medium/high)
  5. Standardize location names
  6. Convert ratings to float (parse "4.1/5" format)
  7. Extract & flatten highlights / dish_liked field

Edge cases handled:
  D-04: Large dataset → optional row limit
  D-05: Null ratings → drop + log
  D-06: Duplicate entries → deduplicate by name+location
  D-07: Non-numeric cost → coerce with median fallback
  D-08: Inconsistent cuisine format → normalize
  D-09: Unicode in names → preserve, strip control chars
"""

import logging
import re
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Column mapping: raw HuggingFace names → clean internal names
COLUMN_RENAME_MAP = {
    "name": "restaurant_name",
    "location": "location",
    "cuisines": "cuisine",
    "approx_cost(for two people)": "cost_for_two",
    "rate": "rating",
    "votes": "votes",
    "online_order": "online_order",
    "book_table": "book_table",
    "rest_type": "restaurant_type",
    "dish_liked": "highlights",
    "listed_in(type)": "listing_type",
    "listed_in(city)": "city",
    "url": "url",
    "address": "address",
    "phone": "phone",
}

# Columns to keep in the cleaned output
OUTPUT_COLUMNS = [
    "restaurant_name",
    "location",
    "cuisine",
    "cost_for_two",
    "rating",
    "votes",
    "budget_category",
    "online_order",
    "book_table",
    "restaurant_type",
    "highlights",
    "listing_type",
    "city",
]

# Budget thresholds (₹)
BUDGET_THRESHOLDS = {
    "low": (0, 500),
    "medium": (500, 1500),
    "high": (1500, float("inf")),
}


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw HuggingFace columns to clean internal names."""
    available_renames = {
        k: v for k, v in COLUMN_RENAME_MAP.items() if k in df.columns
    }
    df = df.rename(columns=available_renames)
    logger.info(
        "Renamed %d columns: %s", len(available_renames), list(available_renames.keys())
    )
    return df


def parse_rating(rate_str: object) -> Optional[float]:
    """
    Parse a rating string like "4.1/5" into a float.

    Handles special values: "NEW", "-", NaN → returns None.
    """
    if pd.isna(rate_str):
        return None

    rate_str = str(rate_str).strip()

    if rate_str in ("NEW", "-", ""):
        return None

    # Extract numeric part from "X.X/5" format
    match = re.match(r"^(\d+\.?\d*)\s*/\s*\d+", rate_str)
    if match:
        return float(match.group(1))

    # Try direct float conversion
    try:
        value = float(rate_str)
        if 0 <= value <= 5:
            return value
    except (ValueError, TypeError):
        pass

    return None


def parse_cost(cost_str: object) -> Optional[float]:
    """
    Parse a cost string into a numeric value.

    Handles commas (e.g., "1,200") and non-numeric values.
    """
    if pd.isna(cost_str):
        return None

    cost_str = str(cost_str).strip().replace(",", "")

    try:
        value = float(cost_str)
        return value if value > 0 else None
    except (ValueError, TypeError):
        return None


def clean_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the rating column from string to float. Drop rows with no rating."""
    initial_count = len(df)

    df["rating"] = df["rating"].apply(parse_rating)

    null_ratings = df["rating"].isna().sum()
    df = df.dropna(subset=["rating"])

    logger.info(
        "Ratings: parsed %d → dropped %d null → %d remaining.",
        initial_count,
        null_ratings,
        len(df),
    )
    return df


def clean_costs(df: pd.DataFrame) -> pd.DataFrame:
    """Parse cost column to numeric. Fill unparseable values with median."""
    df["cost_for_two"] = df["cost_for_two"].apply(parse_cost)

    null_costs = df["cost_for_two"].isna().sum()
    if null_costs > 0:
        median_cost = df["cost_for_two"].median()
        df["cost_for_two"] = df["cost_for_two"].fillna(median_cost)
        logger.info(
            "Costs: %d unparseable values filled with median (%.0f).",
            null_costs,
            median_cost,
        )

    # Ensure integer type after filling
    df["cost_for_two"] = df["cost_for_two"].astype(int)
    return df


def remove_null_critical_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing critical fields: restaurant_name, location, cuisine."""
    critical_fields = ["restaurant_name", "location", "cuisine"]
    initial_count = len(df)

    for field in critical_fields:
        if field in df.columns:
            df = df.dropna(subset=[field])

    dropped = initial_count - len(df)
    if dropped > 0:
        logger.info(
            "Dropped %d rows with null critical fields (name/location/cuisine).",
            dropped,
        )
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate restaurant entries.

    Deduplicates by (restaurant_name + location), keeping the entry
    with the most votes.
    """
    initial_count = len(df)

    df = df.sort_values("votes", ascending=False)
    df = df.drop_duplicates(
        subset=["restaurant_name", "location"], keep="first"
    )

    dropped = initial_count - len(df)
    if dropped > 0:
        logger.info("Removed %d duplicate entries.", dropped)
    return df


def normalize_cuisines(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize cuisine labels: lowercase, strip whitespace, clean separators."""
    def _normalize(cuisine_str: object) -> str:
        if pd.isna(cuisine_str):
            return ""
        # Split by comma, strip each, lowercase, rejoin
        cuisines = [c.strip().lower() for c in str(cuisine_str).split(",")]
        # Remove empty strings
        cuisines = [c for c in cuisines if c]
        return ", ".join(cuisines)

    df["cuisine"] = df["cuisine"].apply(_normalize)
    logger.info("Normalized cuisine labels.")
    return df


def standardize_locations(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize location names: title case, strip whitespace."""
    df["location"] = (
        df["location"]
        .astype(str)
        .str.strip()
        .str.title()
    )
    logger.info(
        "Standardized %d unique locations.", df["location"].nunique()
    )
    return df


def map_budget_category(cost: float) -> str:
    """Map a cost_for_two value to a budget category."""
    for category, (low, high) in BUDGET_THRESHOLDS.items():
        if low <= cost < high:
            return category
    return "high"  # Fallback for very high values


def add_budget_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Add a budget_category column based on cost_for_two."""
    df["budget_category"] = df["cost_for_two"].apply(map_budget_category)

    distribution = df["budget_category"].value_counts().to_dict()
    logger.info("Budget distribution: %s", distribution)
    return df


def clean_highlights(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize the highlights / dish_liked field."""
    if "highlights" not in df.columns:
        df["highlights"] = ""
        return df

    def _clean(text: object) -> str:
        if pd.isna(text):
            return ""
        # Strip whitespace, normalize commas
        text = str(text).strip()
        items = [item.strip() for item in text.split(",")]
        items = [item for item in items if item]
        return ", ".join(items)

    df["highlights"] = df["highlights"].apply(_clean)
    logger.info("Cleaned highlights field.")
    return df


def clean_boolean_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Yes/No string fields to boolean-friendly lowercase."""
    for col in ["online_order", "book_table"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .replace({"yes": "yes", "no": "no"})
            )
    return df


def sanitize_text(df: pd.DataFrame) -> pd.DataFrame:
    """Remove control characters from text fields, preserving unicode."""
    text_cols = ["restaurant_name", "cuisine", "highlights", "restaurant_type"]

    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .apply(lambda x: re.sub(r"[\x00-\x1f\x7f-\x9f]", "", x))
            )

    return df


def select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select and order the final output columns."""
    available = [col for col in OUTPUT_COLUMNS if col in df.columns]
    return df[available].reset_index(drop=True)


def preprocess(
    df: pd.DataFrame,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline on raw Zomato data.

    Pipeline steps:
      1. Rename columns
      2. Remove nulls in critical fields
      3. Clean ratings (parse string → float)
      4. Clean costs (parse string → int, median fill)
      5. Remove duplicates (by name + location)
      6. Normalize cuisines
      7. Standardize locations
      8. Add budget categories
      9. Clean highlights
     10. Clean boolean fields
     11. Sanitize text
     12. Select output columns

    Args:
        df: Raw DataFrame from HuggingFace or local cache.
        max_rows: Optional row limit (for large datasets).

    Returns:
        Cleaned, normalized DataFrame ready for querying.
    """
    logger.info("Starting preprocessing pipeline on %d rows...", len(df))

    # Optionally limit rows (D-04: extremely large datasets)
    if max_rows and len(df) > max_rows:
        logger.info("Limiting to top %d rows by votes.", max_rows)
        df = df.nlargest(max_rows, "votes")

    # Step 1: Rename columns
    df = rename_columns(df)

    # Step 2: Remove null critical fields
    df = remove_null_critical_fields(df)

    # Step 3: Clean ratings
    df = clean_ratings(df)

    # Step 4: Clean costs
    df = clean_costs(df)

    # Step 5: Remove duplicates
    df = remove_duplicates(df)

    # Step 6: Normalize cuisines
    df = normalize_cuisines(df)

    # Step 7: Standardize locations
    df = standardize_locations(df)

    # Step 8: Add budget categories
    df = add_budget_categories(df)

    # Step 9: Clean highlights
    df = clean_highlights(df)

    # Step 10: Clean boolean fields
    df = clean_boolean_fields(df)

    # Step 11: Sanitize text
    df = sanitize_text(df)

    # Step 12: Select output columns
    df = select_output_columns(df)

    logger.info(
        "Preprocessing complete. Final dataset: %d rows × %d columns.",
        len(df),
        len(df.columns),
    )

    return df
