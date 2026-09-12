import pytest
import pandas as pd
from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator

def test_yfinance_provider_instantiation():
    provider = YFinanceProvider()
    assert provider is not None

def test_data_validator_clean_data():
    validator = DataValidator(quality_report_dir="data/quality")
    df = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "open": [100.0, 102.0],
        "high": [105.0, 106.0],
        "low": [98.0, 101.0],
        "close": [104.0, 105.0],
        "volume": [1000, 1500]
    })
    res = validator.validate(df, "TEST.NS")
    assert res["records_processed"] == 2
    assert res["records_valid"] == 2
    assert len(res["errors"]) == 0

def test_data_validator_invalid_ohlc():
    validator = DataValidator(quality_report_dir="data/quality")
    df = pd.DataFrame({
        "date": ["2026-03-01"],
        "open": [100.0],
        "high": [90.0],  # High lower than open
        "low": [98.0],
        "close": [104.0],
        "volume": [1000]
    })
    res = validator.validate(df, "TEST.NS")
    assert len(res["errors"]) > 0
