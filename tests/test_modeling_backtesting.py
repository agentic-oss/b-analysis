import pandas as pd
import numpy as np
import pytest
from src.indicators.technical import TechnicalAnalysisEngine
from src.features.engineer import FeatureEngineer
from src.modeling.predictions import PredictionEngine
from src.backtesting.engine import BacktestEngine

def test_prediction_engine():
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=80).strftime('%Y-%m-%d')
    closes = 100 + np.cumsum(np.random.randn(80))

    df = pd.DataFrame({
        'date': dates,
        'symbol': ['RELIANCE'] * 80,
        'open': closes,
        'high': closes + 1,
        'low': closes - 1,
        'close': closes,
        'volume': [10000] * 80
    })

    df_calc = TechnicalAnalysisEngine.calculate_indicators(df)
    df_feat = FeatureEngineer.create_feature_dataset(df_calc)

    signals = PredictionEngine.generate_directional_signals(df_feat)

    assert '1d' in signals
    assert signals['1d']['directional_bias'] in ['Bullish', 'Slightly Bullish', 'Neutral', 'Slightly Bearish', 'Bearish']
    assert 0 <= signals['1d']['probability_up'] <= 1.0

def test_backtest_engine():
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100).strftime('%Y-%m-%d')
    closes = 100 + np.cumsum(np.random.randn(100))

    df = pd.DataFrame({
        'date': dates,
        'symbol': ['INFY'] * 100,
        'open': closes,
        'high': closes + 1,
        'low': closes - 1,
        'close': closes,
        'volume': [20000] * 100
    })

    df_calc = TechnicalAnalysisEngine.calculate_indicators(df)
    engine = BacktestEngine(initial_capital=500000)
    res = engine.run_backtest(df_calc)

    assert res['initial_capital'] == 500000
    assert 'total_return_pct' in res
    assert 'max_drawdown_pct' in res
