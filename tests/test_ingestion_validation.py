import pytest
import pandas as pd
import numpy as np
from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.validator import DataValidator

def test_data_validator():
    validator = DataValidator()

    # Valid dataframe
    valid_df = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "open": [100.0, 102.0, 101.0],
        "high": [105.0, 104.0, 103.0],
        "low": [99.0, 100.0, 98.0],
        "close": [102.0, 101.0, 102.5],
        "volume": [10000, 12000, 11000]
    })

    res = validator.validate_ohlcv(valid_df, "TEST")
    assert res["is_valid"] is True
    assert len(res["errors"]) == 0

    # Invalid OHLC (High < Low)
    invalid_df = valid_df.copy()
    invalid_df.loc[0, "high"] = 90.0
    res_inv = validator.validate_ohlcv(invalid_df, "TEST")
    assert res_inv["is_valid"] is False
    assert len(res_inv["errors"]) > 0

def test_quality_report():
    validator = DataValidator()
    results = {
        "RELIANCE": {"total_records": 100, "valid_records": 100, "warnings": [], "errors": []},
        "TCS": {"total_records": 100, "valid_records": 90, "warnings": ["Spike"], "errors": ["Zero price"]}
    }
    report = validator.generate_quality_report("2025-01-03", results)
    assert report["symbols_processed"] == 2
    assert report["records_processed"] == 200
    assert report["records_valid"] == 190
    assert report["errors_count"] == 1
    assert report["warnings_count"] == 1
