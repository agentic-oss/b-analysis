import pytest
import pandas as pd
from src.validation.data_validator import DataValidator

def test_data_validator_valid():
    validator = DataValidator()
    df = pd.DataFrame([
        {'symbol': 'RELIANCE', 'date': '2025-01-10', 'open': 1200.0, 'high': 1220.0, 'low': 1190.0, 'close': 1210.0, 'volume': 1000000},
        {'symbol': 'TCS', 'date': '2025-01-10', 'open': 4000.0, 'high': 4050.0, 'low': 3980.0, 'close': 4020.0, 'volume': 500000}
    ])
    is_valid, warnings, errors = validator.validate_price_data(df, '2025-01-10')
    assert is_valid is True
    assert len(errors) == 0

def test_data_validator_invalid_ohlc():
    validator = DataValidator()
    df = pd.DataFrame([
        {'symbol': 'RELIANCE', 'date': '2025-01-10', 'open': 1200.0, 'high': 1100.0, 'low': 1190.0, 'close': 1210.0, 'volume': 1000000}
    ])
    is_valid, warnings, errors = validator.validate_price_data(df, '2025-01-10')
    assert is_valid is False
    assert any("Impossible High" in e for e in errors)
