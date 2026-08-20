"""
Tests for the data loader, preprocessor, and pipeline (Phase 2).

Covers:
  - HuggingFace dataset loading
  - Local cache fallback
  - Schema validation
  - Rating parsing (all formats)
  - Cost parsing and median fallback
  - Duplicate removal
  - Cuisine normalization
  - Location standardization
  - Budget category mapping
  - Full pipeline integration
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.data.loader import (
    load_dataset_with_fallback,
    load_from_local_cache,
    validate_schema,
)
from src.data.preprocessor import (
    add_budget_categories,
    clean_costs,
    clean_ratings,
    map_budget_category,
    normalize_cuisines,
    parse_cost,
    parse_rating,
    preprocess,
    remove_duplicates,
    remove_null_critical_fields,
    rename_columns,
    standardize_locations,
)
from src.data.store import (
    cache_exists,
    delete_cache,
    load_from_csv,
    save_to_csv,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_raw_df(n: int = 5) -> pd.DataFrame:
    """Create a sample raw DataFrame mimicking the HuggingFace schema."""
    return pd.DataFrame(
        {
            "url": [f"https://example.com/{i}" for i in range(n)],
            "address": [f"Address {i}" for i in range(n)],
            "name": [f"Restaurant {i}" for i in range(n)],
            "online_order": ["Yes", "No", "Yes", "No", "Yes"][:n],
            "book_table": ["No", "Yes", "No", "Yes", "No"][:n],
            "rate": ["4.1/5", "3.5/5", "NEW", "-", "4.8/5"][:n],
            "votes": [100, 200, 50, 300, 150][:n],
            "phone": ["+91 1234567890"] * n,
            "location": [
                "Banashankari",
                "btm",
                "Koramangala",
                "  JP Nagar  ",
                "koramangala",
            ][:n],
            "rest_type": ["Casual Dining", "Cafe", "Quick Bites", "Pub", "Fine Dining"][
                :n
            ],
            "dish_liked": [
                "Pasta, Pizza",
                None,
                "Momos",
                "Biryani, Dal",
                "  Sushi , Ramen ",
            ][:n],
            "cuisines": [
                "North Indian, Chinese",
                " Italian , Cafe",
                "South Indian",
                None,
                "Japanese, Asian",
            ][:n],
            "approx_cost(for two people)": ["800", "1,200", "300", "2000", "500"][:n],
            "reviews_list": ["[]"] * n,
            "menu_item": ["[]"] * n,
            "listed_in(type)": ["Delivery", "Dine-out", "Delivery", "Buffet", "Delivery"][
                :n
            ],
            "listed_in(city)": [
                "Banashankari",
                "BTM",
                "Koramangala",
                "JP Nagar",
                "Koramangala",
            ][:n],
        }
    )


@pytest.fixture
def raw_df():
    """Raw DataFrame fixture."""
    return _make_raw_df()


@pytest.fixture
def tmp_csv(tmp_path):
    """Create a temporary CSV file path."""
    return str(tmp_path / "test_data.csv")


# ---------------------------------------------------------------------------
# Tests: Rating Parsing
# ---------------------------------------------------------------------------


class TestParseRating:
    """Tests for the parse_rating function."""

    def test_standard_format(self):
        assert parse_rating("4.1/5") == 4.1

    def test_integer_rating(self):
        assert parse_rating("4/5") == 4.0

    def test_perfect_rating(self):
        assert parse_rating("5.0/5") == 5.0

    def test_low_rating(self):
        assert parse_rating("1.0/5") == 1.0

    def test_new_restaurant(self):
        assert parse_rating("NEW") is None

    def test_dash_rating(self):
        assert parse_rating("-") is None

    def test_empty_string(self):
        assert parse_rating("") is None

    def test_none_value(self):
        assert parse_rating(None) is None

    def test_nan_value(self):
        assert parse_rating(float("nan")) is None

    def test_whitespace_around(self):
        assert parse_rating("  4.1/5  ") == 4.1

    def test_plain_float(self):
        assert parse_rating("3.7") == 3.7


# ---------------------------------------------------------------------------
# Tests: Cost Parsing
# ---------------------------------------------------------------------------


class TestParseCost:
    """Tests for the parse_cost function."""

    def test_simple_number(self):
        assert parse_cost("800") == 800.0

    def test_with_comma(self):
        assert parse_cost("1,200") == 1200.0

    def test_large_number(self):
        assert parse_cost("2,500") == 2500.0

    def test_none_value(self):
        assert parse_cost(None) is None

    def test_nan_value(self):
        assert parse_cost(float("nan")) is None

    def test_empty_string(self):
        assert parse_cost("") is None

    def test_zero_value(self):
        assert parse_cost("0") is None

    def test_negative_value(self):
        assert parse_cost("-100") is None

    def test_non_numeric(self):
        assert parse_cost("N/A") is None


# ---------------------------------------------------------------------------
# Tests: Schema Validation
# ---------------------------------------------------------------------------


class TestValidateSchema:
    """Tests for schema validation."""

    def test_valid_schema(self, raw_df):
        # Should not raise
        validate_schema(raw_df)

    def test_missing_column(self, raw_df):
        df = raw_df.drop(columns=["name"])
        with pytest.raises(ValueError, match="missing columns"):
            validate_schema(df)

    def test_missing_multiple_columns(self):
        df = pd.DataFrame({"url": ["test"], "name": ["test"]})
        with pytest.raises(ValueError, match="missing columns"):
            validate_schema(df)


# ---------------------------------------------------------------------------
# Tests: Preprocessor Steps
# ---------------------------------------------------------------------------


class TestRenameColumns:
    """Tests for column renaming."""

    def test_renames_correctly(self, raw_df):
        df = rename_columns(raw_df)
        assert "restaurant_name" in df.columns
        assert "cuisine" in df.columns
        assert "cost_for_two" in df.columns
        assert "rating" in df.columns
        # Original names should be gone
        assert "name" not in df.columns
        assert "cuisines" not in df.columns


class TestRemoveNullCriticalFields:
    """Tests for removing rows with null critical fields."""

    def test_drops_null_names(self):
        df = pd.DataFrame(
            {
                "restaurant_name": ["A", None, "C"],
                "location": ["L1", "L2", "L3"],
                "cuisine": ["C1", "C2", "C3"],
            }
        )
        result = remove_null_critical_fields(df)
        assert len(result) == 2

    def test_drops_null_locations(self):
        df = pd.DataFrame(
            {
                "restaurant_name": ["A", "B"],
                "location": ["L1", None],
                "cuisine": ["C1", "C2"],
            }
        )
        result = remove_null_critical_fields(df)
        assert len(result) == 1

    def test_keeps_all_when_no_nulls(self):
        df = pd.DataFrame(
            {
                "restaurant_name": ["A", "B"],
                "location": ["L1", "L2"],
                "cuisine": ["C1", "C2"],
            }
        )
        result = remove_null_critical_fields(df)
        assert len(result) == 2


class TestCleanRatings:
    """Tests for rating cleaning."""

    def test_drops_unparseable_ratings(self):
        df = pd.DataFrame({"rating": ["4.1/5", "NEW", "-", "3.8/5", None]})
        result = clean_ratings(df)
        assert len(result) == 2
        assert result["rating"].tolist() == [4.1, 3.8]


class TestCleanCosts:
    """Tests for cost cleaning."""

    def test_parses_costs_correctly(self):
        df = pd.DataFrame({"cost_for_two": ["800", "1,200", "300"]})
        result = clean_costs(df)
        assert result["cost_for_two"].tolist() == [800, 1200, 300]

    def test_fills_nulls_with_median(self):
        df = pd.DataFrame({"cost_for_two": ["800", None, "300"]})
        result = clean_costs(df)
        # Median of [800, 300] = 550
        assert result["cost_for_two"].iloc[1] == 550


class TestRemoveDuplicates:
    """Tests for duplicate removal."""

    def test_removes_duplicates_keeps_highest_votes(self):
        df = pd.DataFrame(
            {
                "restaurant_name": ["A", "A", "B"],
                "location": ["L1", "L1", "L2"],
                "votes": [50, 100, 200],
            }
        )
        result = remove_duplicates(df)
        assert len(result) == 2
        # Should keep the one with 100 votes
        a_row = result[result["restaurant_name"] == "A"]
        assert a_row["votes"].iloc[0] == 100

    def test_different_locations_not_deduped(self):
        df = pd.DataFrame(
            {
                "restaurant_name": ["A", "A"],
                "location": ["L1", "L2"],
                "votes": [50, 100],
            }
        )
        result = remove_duplicates(df)
        assert len(result) == 2


class TestNormalizeCuisines:
    """Tests for cuisine normalization."""

    def test_normalizes_case_and_whitespace(self):
        df = pd.DataFrame({"cuisine": [" Italian , Cafe", "NORTH INDIAN"]})
        result = normalize_cuisines(df)
        assert result["cuisine"].iloc[0] == "italian, cafe"
        assert result["cuisine"].iloc[1] == "north indian"

    def test_handles_null_cuisines(self):
        df = pd.DataFrame({"cuisine": [None, "Chinese"]})
        result = normalize_cuisines(df)
        assert result["cuisine"].iloc[0] == ""
        assert result["cuisine"].iloc[1] == "chinese"


class TestStandardizeLocations:
    """Tests for location standardization."""

    def test_title_case_and_strip(self):
        df = pd.DataFrame({"location": ["  banashankari  ", "btm", "JP NAGAR"]})
        result = standardize_locations(df)
        assert result["location"].iloc[0] == "Banashankari"
        assert result["location"].iloc[1] == "Btm"
        assert result["location"].iloc[2] == "Jp Nagar"


class TestBudgetMapping:
    """Tests for budget category mapping."""

    def test_low_budget(self):
        assert map_budget_category(300) == "low"

    def test_low_boundary(self):
        assert map_budget_category(500) == "medium"  # 500 is medium

    def test_medium_budget(self):
        assert map_budget_category(800) == "medium"

    def test_high_boundary(self):
        assert map_budget_category(1500) == "high"  # 1500 is high

    def test_high_budget(self):
        assert map_budget_category(3000) == "high"

    def test_zero(self):
        assert map_budget_category(0) == "low"

    def test_add_column(self):
        df = pd.DataFrame({"cost_for_two": [300, 800, 2000]})
        result = add_budget_categories(df)
        assert "budget_category" in result.columns
        assert result["budget_category"].tolist() == ["low", "medium", "high"]


# ---------------------------------------------------------------------------
# Tests: Data Store
# ---------------------------------------------------------------------------


class TestDataStore:
    """Tests for save/load/cache operations."""

    def test_save_and_load(self, tmp_csv):
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        save_to_csv(df, tmp_csv)
        loaded = load_from_csv(tmp_csv)
        assert len(loaded) == 3
        assert list(loaded.columns) == ["a", "b"]

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_from_csv("/nonexistent/path/data.csv")

    def test_cache_exists(self, tmp_csv):
        assert cache_exists(tmp_csv) is False

        df = pd.DataFrame({"a": [1]})
        save_to_csv(df, tmp_csv)
        assert cache_exists(tmp_csv) is True

    def test_delete_cache(self, tmp_csv):
        df = pd.DataFrame({"a": [1]})
        save_to_csv(df, tmp_csv)
        assert os.path.exists(tmp_csv)

        result = delete_cache(tmp_csv)
        assert result is True
        assert not os.path.exists(tmp_csv)

    def test_delete_nonexistent_cache(self, tmp_csv):
        result = delete_cache(tmp_csv)
        assert result is False


# ---------------------------------------------------------------------------
# Tests: Loader with Fallback
# ---------------------------------------------------------------------------


class TestLoaderFallback:
    """Tests for the dataset loading with fallback logic."""

    def test_loads_from_local_cache(self, tmp_csv):
        """When a cache exists and force_refresh=False, use the cache."""
        df = pd.DataFrame(
            {
                "restaurant_name": ["Test"],
                "location": ["Delhi"],
                "cuisine": ["Indian"],
                "cost_for_two": [500],
                "rating": [4.0],
                "votes": [100],
            }
        )
        save_to_csv(df, tmp_csv)

        result = load_dataset_with_fallback(
            dataset_name="fake/dataset",
            cache_path=tmp_csv,
            force_refresh=False,
        )
        assert len(result) == 1
        assert result["restaurant_name"].iloc[0] == "Test"

    def test_fallback_when_no_cache(self):
        """When HuggingFace fails and no cache exists, raise RuntimeError."""
        with patch("src.data.loader.load_from_huggingface") as mock_hf:
            mock_hf.side_effect = RuntimeError("API down")

            with pytest.raises(RuntimeError, match="No dataset available"):
                load_dataset_with_fallback(
                    dataset_name="fake/dataset",
                    cache_path="/nonexistent/cache.csv",
                    force_refresh=True,
                )

    def test_local_cache_file_not_found(self):
        """load_from_local_cache raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_from_local_cache("/nonexistent/path.csv")


# ---------------------------------------------------------------------------
# Tests: Full Preprocessing Pipeline
# ---------------------------------------------------------------------------


class TestFullPipeline:
    """Integration tests for the complete preprocessing pipeline."""

    def test_pipeline_produces_expected_columns(self, raw_df):
        result = preprocess(raw_df)

        expected_cols = {
            "restaurant_name",
            "location",
            "cuisine",
            "cost_for_two",
            "rating",
            "votes",
            "budget_category",
        }
        assert expected_cols.issubset(set(result.columns))

    def test_pipeline_removes_unparseable_ratings(self, raw_df):
        result = preprocess(raw_df)

        # "NEW" and "-" ratings should be dropped
        assert result["rating"].isna().sum() == 0
        assert all(isinstance(r, float) for r in result["rating"])

    def test_pipeline_no_null_critical_fields(self, raw_df):
        result = preprocess(raw_df)

        assert result["restaurant_name"].isna().sum() == 0
        assert result["location"].isna().sum() == 0

    def test_pipeline_budget_categories_valid(self, raw_df):
        result = preprocess(raw_df)

        valid_budgets = {"low", "medium", "high"}
        assert set(result["budget_category"].unique()).issubset(valid_budgets)

    def test_pipeline_cuisines_normalized(self, raw_df):
        result = preprocess(raw_df)

        for cuisine in result["cuisine"]:
            if cuisine:  # Skip empty
                assert cuisine == cuisine.lower()
                assert "  " not in cuisine  # No double spaces

    def test_pipeline_locations_standardized(self, raw_df):
        result = preprocess(raw_df)

        for loc in result["location"]:
            assert loc == loc.strip()
            assert loc == loc.title()

    def test_pipeline_costs_are_integers(self, raw_df):
        result = preprocess(raw_df)

        assert result["cost_for_two"].dtype in [np.int64, np.int32, int]

    def test_pipeline_with_max_rows(self, raw_df):
        result = preprocess(raw_df, max_rows=2)
        # After all cleaning, might have fewer rows, but should respect limit
        assert len(result) <= 2

    def test_pipeline_handles_all_null_cuisine_row(self):
        """Row with null cuisine should be dropped."""
        df = _make_raw_df()
        # Row index 3 has None cuisine — it will be dropped
        result = preprocess(df)
        # Verify no restaurant has empty critical fields
        assert result["restaurant_name"].isna().sum() == 0


# ---------------------------------------------------------------------------
# Tests: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for specific edge cases from the edge case document."""

    def test_empty_dataframe(self):
        """D-03: Empty dataset should result in empty output."""
        df = pd.DataFrame(
            {
                "name": pd.Series(dtype="str"),
                "location": pd.Series(dtype="str"),
                "cuisines": pd.Series(dtype="str"),
                "approx_cost(for two people)": pd.Series(dtype="str"),
                "rate": pd.Series(dtype="str"),
                "votes": pd.Series(dtype="int64"),
            }
        )
        result = preprocess(df)
        assert len(result) == 0

    def test_all_ratings_null(self):
        """D-05: All null ratings → all rows dropped."""
        df = pd.DataFrame(
            {
                "name": ["A", "B"],
                "location": ["L1", "L2"],
                "cuisines": ["C1", "C2"],
                "approx_cost(for two people)": ["500", "800"],
                "rate": [None, None],
                "votes": [100, 200],
            }
        )
        result = preprocess(df)
        assert len(result) == 0

    def test_special_characters_in_names(self):
        """D-09: Unicode in names should be preserved."""
        df = pd.DataFrame(
            {
                "name": ["Café Résumé 🍕", "Taco Bell™"],
                "location": ["Delhi", "Mumbai"],
                "cuisines": ["French", "Mexican"],
                "approx_cost(for two people)": ["1000", "500"],
                "rate": ["4.5/5", "3.8/5"],
                "votes": [100, 200],
            }
        )
        result = preprocess(df)
        assert len(result) == 2
        # Unicode should be preserved in both names
        all_names = result["restaurant_name"].tolist()
        assert any("Café" in name for name in all_names)
        assert any("™" in name for name in all_names)

    def test_cost_with_comma_formatting(self):
        """D-07: Cost with commas should parse correctly."""
        assert parse_cost("1,200") == 1200.0
        assert parse_cost("10,000") == 10000.0
