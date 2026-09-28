import pandas as pd
import pytest
from src.validation.validator import DataValidator

def test_data_validator_valid_data():
    validator = DataValidator()
    df_valid = pd.DataFrame([
        {
            'symbol': 'RELIANCE',
            'date': '2026-03-27',
            'open': 2500.0,
            'high': 2550.0,
            'low': 2480.0,
            'close': 2530.0,
            'volume': 1000000
        }
    ])

    valid_df, report = validator.validate_daily_prices(df_valid, '2026-03-27')
    assert len(valid_df) == 1
    assert report['records_processed'] == 1
    assert report['records_valid'] == 1
    assert len(report['errors']) == 0

def test_data_validator_invalid_ohlc():
    validator = DataValidator()
    df_invalid = pd.DataFrame([
        {
            'symbol': 'TCS',
            'date': '2026-03-27',
            'open': 3500.0,
            'high': 3400.0, # high < open
            'low': 3600.0,  # low > open
            'close': 3550.0,
            'volume': 500000
        }
    ])

    valid_df, report = validator.validate_daily_prices(df_invalid, '2026-03-27')
    assert len(valid_df) == 0
    assert report['records_processed'] == 1
    assert report['records_valid'] == 0
    assert len(report['errors']) > 0

def test_historical_anomalies():
    validator = DataValidator(price_change_threshold=0.20)
    dates = pd.date_range('2026-01-01', periods=10).strftime('%Y-%m-%d')
    closes = [100.0, 101.0, 102.0, 101.5, 150.0, 151.0, 152.0, 150.0, 151.0, 152.0] # 101.5 -> 150 is ~48% jump
    vols = [1000] * 10
    vols[4] = 20000 # 20x volume anomaly

    df_hist = pd.DataFrame({
        'symbol': ['INFY'] * 10,
        'date': dates,
        'open': closes,
        'high': [c + 1 for c in closes],
        'low': [c - 1 for c in closes],
        'close': closes,
        'volume': vols
    })

    warnings = validator.check_historical_gaps_and_anomalies(df_hist)
    assert len(warnings) >= 2
