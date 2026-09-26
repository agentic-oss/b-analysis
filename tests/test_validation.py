import pytest
import pandas as pd
import numpy as np
from src.validation.quality import DataValidator, QualityReportGenerator

def test_data_validator_clean():
    df = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02"],
        "Open": [100.0, 102.0],
        "High": [105.0, 106.0],
        "Low": [98.0, 101.0],
        "Close": [103.0, 104.0],
        "Volume": [1000, 1200]
    })
    validator = DataValidator()
    df_val, warnings, errors = validator.validate_stock_dataframe("TEST", df)

    assert len(errors) == 0
    assert len(warnings) == 0

def test_data_validator_impossible_ohlc():
    df = pd.DataFrame({
        "Date": ["2025-01-01"],
        "Open": [100.0],
        "High": [90.0],  # High lower than Open/Close!
        "Low": [80.0],
        "Close": [95.0],
        "Volume": [1000]
    })
    validator = DataValidator()
    _, warnings, errors = validator.validate_stock_dataframe("TEST", df)

    assert len(errors) >= 1
    assert errors[0]["type"] == "IMPOSSIBLE_HIGH"

def test_quality_report_generator():
    report_gen = QualityReportGenerator("2025-01-01")
    report_gen.add_validation_result("TEST", pd.DataFrame({"Date": ["2025-01-01"]}), [], [])
    d = report_gen.to_dict()

    assert d["date"] == "2025-01-01"
    assert d["records_processed"] == 1
    assert d["records_valid"] == 1
