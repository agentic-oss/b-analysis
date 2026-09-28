import pandas as pd
import numpy as np
import pytest
from src.indicators.technical import TechnicalAnalysisEngine

def test_technical_indicators_calculation():
    dates = pd.date_range('2025-01-01', periods=60).strftime('%Y-%m-%d')
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(60))

    df = pd.DataFrame({
        'date': dates,
        'symbol': ['RELIANCE'] * 60,
        'open': close_prices - 1,
        'high': close_prices + 2,
        'low': close_prices - 2,
        'close': close_prices,
        'volume': np.random.randint(1000, 50000, 60)
    })

    df_calc = TechnicalAnalysisEngine.calculate_indicators(df)

    # Check expected indicator columns
    expected_cols = [
        'sma_20', 'sma_50', 'ema_20', 'rsi_14', 'stoch_rsi',
        'macd', 'macd_signal', 'atr_14', 'volatility_20d',
        'bollinger_upper', 'bollinger_lower', 'relative_volume', 'obv', 'ad_line'
    ]
    for col in expected_cols:
        assert col in df_calc.columns
        assert not df_calc[col].isnull().all()

def test_pattern_identification():
    dates = pd.date_range('2025-01-01', periods=30).strftime('%Y-%m-%d')
    closes = [100 + i for i in range(29)] + [140] # Strong jump on last day
    vols = [1000] * 29 + [10000] # Unusual high volume on last day

    df = pd.DataFrame({
        'date': dates,
        'symbol': ['TCS'] * 30,
        'open': closes,
        'high': [c + 1 for c in closes],
        'low': [c - 1 for c in closes],
        'close': closes,
        'volume': vols
    })

    df_calc = TechnicalAnalysisEngine.calculate_indicators(df)
    patterns = TechnicalAnalysisEngine.identify_patterns(df_calc)

    assert patterns['symbol'] == 'TCS'
    assert '20-Day High Breakout' in patterns['signals']
    assert any('Unusual Volume' in s for s in patterns['signals'])
    assert patterns['support_1'] < patterns['close']
    assert patterns['resistance_1'] > patterns['close']
