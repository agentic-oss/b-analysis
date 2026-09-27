"""
Tests for DataValidator.
"""
import pandas as pd
import pytest
from src.validation.validator import DataValidator


def test_validator_ohlc_check():
    validator = DataValidator()
    data = {
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "Open": [100.0, 105.0, 110.0],
        "High": [102.0, 108.0, 115.0],  # Invalid on row 0: High < Low
        "Low": [103.0, 101.0, 108.0],
        "Close": [101.0, 106.0, 112.0],
        "Volume": [1000, 1200, 1100],
    }
    df = pd.DataFrame(data)
    clean_df, warnings, errors = validator.validate_dataframe(df, "TEST")

    assert len(errors) > 0
    assert len(clean_df) < len(df)


def test_validator_duplicates():
    validator = DataValidator()
    data = {
        "Date": ["2025-01-01", "2025-01-01"],
        "Open": [100.0, 100.0],
        "High": [105.0, 105.0],
        "Low": [95.0, 95.0],
        "Close": [102.0, 102.0],
        "Volume": [1000, 1000],
    }
    df = pd.DataFrame(data)
    clean_df, warnings, errors = validator.validate_dataframe(df, "TEST")

    assert len(clean_df) == 1
    assert len(warnings) > 0
