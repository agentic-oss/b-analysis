import pytest
import pandas as pd
import numpy as np
from src.features.feature_engine import FeatureEngine
from src.modeling.prediction_engine import PredictionEngine
from src.backtesting.backtester import Backtester

def test_feature_engine():
    dates = pd.date_range(start="2024-01-01", periods=30, freq="B")
    df = pd.DataFrame({
        'symbol': 'RELIANCE',
        'date': dates.strftime('%Y-%m-%d'),
        'open': np.linspace(100, 130, 30),
        'high': np.linspace(105, 135, 30),
        'low': np.linspace(95, 125, 30),
        'close': np.linspace(102, 132, 30),
        'volume': 1000,
        'daily_return': 0.01,
        'rsi_14': 55.0
    })

    f_df = FeatureEngine.build_feature_set(df)
    assert not f_df.empty
    assert 'future_return_1d' in f_df.columns
    assert 'future_return_5d' in f_df.columns

def test_prediction_engine():
    engine = PredictionEngine()
    analogue_stats = {
        "num_matches": 15,
        "horizons": {
            "1d": {"positive_prob": 0.65, "avg_return": 0.01},
            "5d": {"positive_prob": 0.60, "avg_return": 0.02}
        }
    }
    res = engine.generate_forward_signals(analogue_stats, stock_score=75.0)
    assert "signals" in res
    assert "1d" in res["signals"]
    assert res["signals"]["1d"]["directional_bias"] in ["Bullish", "Slightly Bullish", "Neutral", "Slightly Bearish", "Bearish"]

def test_backtester():
    dates = pd.date_range(start="2024-01-01", periods=50, freq="B")
    df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'close': np.linspace(100, 150, 50)
    })
    signals = pd.Series([1 if i % 10 == 0 else 0 for i in range(50)])
    tester = Backtester(initial_capital=100000.0)
    res = tester.run_backtest(df, signals)
    assert "cumulative_return" in res
    assert "max_drawdown" in res
