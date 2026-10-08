import pytest
import pandas as pd
from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.validator import DataValidator


def test_yfinance_provider_historical():
    provider = YFinanceProvider(max_retries=2, retry_backoff=0.5)
    df = provider.get_historical_prices("RELIANCE.NS", period="1 mo")
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "date" in df.columns
        assert "close" in df.columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "volume" in df.columns


def test_data_validator_valid_df():
    validator = DataValidator()
    data = {
        "date": ["2025-01-01", "2025-01-02"],
        "open": [100.0, 102.0],
        "high": [105.0, 106.0],
        "low": [99.0, 101.0],
        "close": [104.0, 105.0],
        "volume": [1000, 1200],
    }
    df = pd.DataFrame(data)
    clean_df, report = validator.validate("TEST", df, "2025-01-02")
    assert report["is_valid"] is True
    assert len(report["errors"]) == 0


def test_data_validator_invalid_ohlc():
    validator = DataValidator()
    data = {
        "date": ["2025-01-01"],
        "open": [100.0],
        "high": [90.0],  # Invalid high < open
        "low": [99.0],
        "close": [104.0],
        "volume": [1000],
    }
    df = pd.DataFrame(data)
    clean_df, report = validator.validate("TEST", df, "2025-01-01")
    assert report["is_valid"] is False
    assert len(report["errors"]) > 0
