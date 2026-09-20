import pytest
import pandas as pd
from src.validation.validator import DataValidator

def test_data_validator_valid():
    validator = DataValidator()
    df = pd.DataFrame([{
        "date": "2026-03-30", "open": 100.0, "high": 105.0, "low": 98.0, "close": 102.0, "volume": 1000, "ticker": "RELIANCE.NS"
    }])
    report = validator.validate_df(df, "2026-03-30")
    assert report["records_processed"] == 1
    assert report["records_valid"] == 1
    assert len(report["errors"]) == 0

def test_data_validator_invalid_ohlc():
    validator = DataValidator()
    df = pd.DataFrame([{
        "date": "2026-03-30", "open": 100.0, "high": 90.0, "low": 98.0, "close": 102.0, "volume": 1000, "ticker": "INVALID.NS"
    }])
    report = validator.validate_df(df, "2026-03-30")
    assert report["records_valid"] == 0
    assert len(report["errors"]) > 0
