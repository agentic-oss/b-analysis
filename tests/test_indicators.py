import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators

def test_calculate_indicators_reproducibility():
    dates = pd.date_range(start='2025-01-01', periods=60)
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(60))

    df = pd.DataFrame({
        'date': dates,
        'open': closes - 0.5,
        'high': closes + 1.0,
        'low': closes - 1.0,
        'close': closes,
        'volume': np.random.randint(1000, 5000, size=60)
    })

    df_ind = TechnicalIndicators.calculate_indicators(df)

    assert 'sma_20' in df_ind.columns
    assert 'ema_20' in df_ind.columns
    assert 'rsi_14' in df_ind.columns
    assert 'macd' in df_ind.columns
    assert 'atr_14' in df_ind.columns
    assert 'relative_volume' in df_ind.columns
    assert 'dist_52w_high' in df_ind.columns

    # Verify deterministic output
    df_ind_2 = TechnicalIndicators.calculate_indicators(df)
    pd.testing.assert_frame_equal(df_ind, df_ind_2)

def test_identify_signals():
    dates = pd.date_range(start='2025-01-01', periods=25)
    df = pd.DataFrame({
        'date': dates,
        'open': [100]*25,
        'high': [105]*24 + [120], # Breakout on last bar
        'low': [95]*25,
        'close': [100]*24 + [118],
        'volume': [1000]*24 + [5000], # Unusual volume on last bar
        'sma_50': [100]*25,
        'sma_200': [100]*25,
        'relative_volume': [1.0]*24 + [5.0],
        'rsi_14': [50]*25
    })

    signals = TechnicalIndicators.identify_signals(df)
    assert signals['unusual_volume'] is True
    assert any("Breakout" in e for e in signals['events'])
