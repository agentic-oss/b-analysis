import pytest
import pandas as pd
import numpy as np
from src.indicators.indicators import TechnicalIndicators

def test_technical_indicators_calculation():
    # Generate 50 days of synthetic price data
    dates = pd.date_range(start="2026-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(50))
    df = pd.DataFrame({
        'date': dates,
        'open': close_prices - 0.5,
        'high': close_prices + 1.0,
        'low': close_prices - 1.0,
        'close': close_prices,
        'volume': np.random.randint(1000, 5000, size=50)
    })

    res = TechnicalIndicators.calculate_all(df)

    assert 'sma_20' in res.columns
    assert 'ema_20' in res.columns
    assert 'rsi_14' in res.columns
    assert 'macd' in res.columns
    assert 'macd_signal' in res.columns
    assert 'atr_14' in res.columns
    assert 'bollinger_upper' in res.columns
    assert 'relative_volume' in res.columns
    assert 'obv' in res.columns
    assert 'breakout_20d' in res.columns
    assert not res['sma_20'].isna().all()
