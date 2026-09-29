"""
Unit tests for Market Data Ingestion and Data Validation.
"""
import pytest
import pandas as pd
import numpy as np
from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.validator import DataValidator


def test_yfinance_symbol_mapping():
    provider = YFinanceProvider()
    assert provider._to_yf_symbol("RELIANCE", "NSE") == "RELIANCE.NS"
    assert provider._to_yf_symbol("TCS", "BSE") == "TCS.BO"
    assert provider._to_yf_symbol("^NSEI", "NSE") == "^NSEI"


def test_data_validator_clean_data(tmp_path):
    quality_dir = str(tmp_path / "quality")
    validator = DataValidator(quality_dir=quality_dir)

    df = pd.DataFrame({
        "Date": ["2026-01-01", "2026-01-02", "2026-01-02"],  # Duplicate date
        "open": [100.0, 102.0, 102.0],
        "high": [105.0, 106.0, 106.0],
        "low": [98.0, 101.0, 101.0],
        "close": [104.0, 105.0, 105.0],
        "volume": [1000, 1200, 1200]
    })

    clean_df, summary = validator.validate_dataframe(df, ticker="TEST")

    assert summary["records_processed"] == 3
    assert summary["records_valid"] == 2
    assert len(summary["warnings"]) == 1
    assert "duplicate" in summary["warnings"][0].lower()


def test_data_validator_invalid_prices(tmp_path):
    validator = DataValidator(quality_dir=str(tmp_path))

    df = pd.DataFrame({
        "Date": ["2026-01-01", "2026-01-02"],
        "open": [100.0, -10.0],  # Negative price
        "high": [105.0, 100.0],
        "low": [98.0, 105.0],    # High < Low
        "close": [104.0, 95.0],
        "volume": [1000, 1200]
    })

    clean_df, summary = validator.validate_dataframe(df, ticker="TEST_INVALID")

    assert summary["records_valid"] == 1
    assert len(summary["errors"]) > 0
