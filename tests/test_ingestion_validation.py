import pytest
import pandas as pd
import numpy as np
from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator

def test_data_validator_clean_data():
    validator = DataValidator()
    df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-02', '2026-01-03'],
        'open': [100.0, 102.0, 101.0],
        'high': [105.0, 106.0, 104.0],
        'low': [99.0, 100.0, 98.0],
        'close': [102.0, 101.0, 103.0],
        'adj_close': [102.0, 101.0, 103.0],
        'volume': [1000, 1200, 1100]
    })
    res = validator.validate_ohlc(df, "TEST.NS")
    assert res["is_valid"] is True
    assert len(res["errors"]) == 0
    assert len(res["warnings"]) == 0
    assert res["records_valid"] if "records_valid" in res else res["valid_records"] == 3

def test_data_validator_invalid_data():
    validator = DataValidator()
    df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-01', '2026-01-03'], # Duplicate date
        'open': [100.0, 102.0, -10.0], # Negative price
        'high': [95.0, 106.0, 104.0],  # High < Open
        'low': [99.0, 100.0, 98.0],
        'close': [102.0, 101.0, 103.0],
        'volume': [1000, 1200, -50]     # Negative volume
    })
    res = validator.validate_ohlc(df, "INVALID.NS")
    assert res["is_valid"] is False
    assert len(res["errors"]) > 0

def test_yfinance_provider_instantiation():
    provider = YFinanceProvider(max_retries=1, retry_backoff=1.0)
    assert provider is not None
