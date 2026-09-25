"""Tests for Ingestion, Validation, and Storage Infrastructure."""

import os
import shutil
import tempfile
import numpy as np
import pandas as pd
import pytest

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage import DataStorage


def test_yfinance_provider_formatting():
    provider = YFinanceProvider()
    assert provider._format_ticker("RELIANCE", "NSE") == "RELIANCE.NS"
    assert provider._format_ticker("TCS", "BSE") == "TCS.BO"
    assert provider._format_ticker("^NSEI", "NSE") == "^NSEI"


def test_data_validator():
    validator = DataValidator()

    # Valid DataFrame
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    valid_data = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 102.0, 101.0, 105.0, 104.0],
        "High": [105.0, 106.0, 104.0, 108.0, 107.0],
        "Low": [99.0, 100.0, 98.0, 103.0, 102.0],
        "Close": [102.0, 101.0, 104.0, 106.0, 105.0],
        "Volume": [1000, 1200, 1100, 1300, 1250]
    })

    clean_df, summary = validator.validate_df(valid_data, ticker="TEST")
    assert summary["records_processed"] == 5
    assert summary["records_valid"] == 5
    assert len(summary["errors"]) == 0

    # Invalid DataFrame with high < low and negative volume
    invalid_data = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 102.0, 101.0, 105.0, 104.0],
        "High": [90.0, 106.0, 104.0, 108.0, 107.0],  # High < Low row 0
        "Low": [99.0, 100.0, 98.0, 103.0, 102.0],
        "Close": [102.0, 101.0, 104.0, 106.0, 105.0],
        "Volume": [-100, 1200, 1100, 1300, 1250]     # Negative volume row 0
    })

    _, invalid_summary = validator.validate_df(invalid_data, ticker="BAD")
    assert len(invalid_summary["errors"]) > 0


def test_data_storage():
    temp_dir = tempfile.mkdtemp()
    try:
        storage = DataStorage(base_dir=temp_dir)
        dates = pd.date_range("2026-01-01", periods=3, freq="D")
        df = pd.DataFrame({
            "Date": dates,
            "Open": [100, 101, 102],
            "High": [105, 106, 107],
            "Low": [99, 100, 101],
            "Close": [104, 105, 106],
            "Volume": [1000, 1100, 1200]
        })

        # Save processed prices
        p_path = storage.update_processed_prices(df, "RELIANCE")
        assert os.path.exists(p_path)

        loaded_df = storage.load_processed_prices("RELIANCE")
        assert len(loaded_df) == 3
        assert list(loaded_df["Close"]) == [104, 105, 106]

        # Append new date record
        new_dates = pd.date_range("2026-01-04", periods=1, freq="D")
        new_df = pd.DataFrame({
            "Date": new_dates,
            "Open": [103],
            "High": [108],
            "Low": [102],
            "Close": [107],
            "Volume": [1300]
        })
        storage.update_processed_prices(new_df, "RELIANCE")
        updated_df = storage.load_processed_prices("RELIANCE")
        assert len(updated_df) == 4

    finally:
        shutil.rmtree(temp_dir)
