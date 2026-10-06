import pytest
import pandas as pd
from src.validation.validator import DataValidator

def test_data_validator_clean():
    validator = DataValidator()
    df = pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'open': [100, 102, 104],
        'high': [105, 106, 108],
        'low': [99, 101, 103],
        'close': [103, 105, 107],
        'volume': [1000, 1100, 1200]
    })

    clean_df, warnings, errors = validator.validate_stock_dataframe('RELIANCE', df)
    assert len(clean_df) == 3
    assert len(errors) == 0

def test_data_validator_invalid_ohlc_and_negative():
    validator = DataValidator()
    df = pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'open': [100, -10, 104],
        'high': [95, 106, 108], # High < Open on row 0 -> Impossible OHLC
        'low': [99, 101, 103],
        'close': [103, 105, 107],
        'volume': [1000, 1100, 1200]
    })

    clean_df, warnings, errors = validator.validate_stock_dataframe('TEST', df)
    assert len(clean_df) == 1 # Only row 2 is valid
    assert len(errors) >= 1

def test_generate_quality_report():
    validator = DataValidator()
    report = validator.generate_quality_report('2025-01-03', 10, 9, [{'type': 'ANOMALY'}], [])
    assert report['records_processed'] == 10
    assert report['records_valid'] == 9
    assert report['date'] == '2025-01-03'
