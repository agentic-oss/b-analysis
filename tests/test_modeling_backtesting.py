import pytest
import pandas as pd
import numpy as np
from src.features.feature_builder import FeatureBuilder
from src.modeling.predictor import BaselinePredictor
from src.backtesting.engine import BacktestEngine

def create_sample_features():
    np.random.seed(42)
    dates = pd.date_range(end="2026-03-01", periods=120, freq="B").strftime("%Y-%m-%d").tolist()
    price = 100.0
    prices = []
    for _ in range(120):
        price += np.random.normal(0.1, 1.5)
        prices.append(price)

    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [10000] * 120,
        "ticker": ["RELIANCE.NS"] * 120
    })
    return FeatureBuilder.build_features(df)

def test_baseline_predictor():
    df_feat = create_sample_features()
    res = BaselinePredictor.train_and_evaluate_walk_forward(df_feat, target_horizon="future_return_5d")
    assert "metrics" in res
    assert "accuracy" in res["metrics"]
    assert 0.0 <= res["metrics"]["accuracy"] <= 1.0

def test_backtest_engine():
    df_feat = create_sample_features()
    # Simple dummy signal: Buy when RSI < 45, Sell when RSI > 55
    df_feat["signal"] = np.where(df_feat["rsi_14"] < 45, 1, np.where(df_feat["rsi_14"] > 55, -1, 0))

    engine = BacktestEngine(initial_capital=100000.0)
    res = engine.run_backtest(df_feat, signal_col="signal")

    assert "cumulative_return_pct" in res
    assert "max_drawdown_pct" in res
    assert res["initial_capital"] == 100000.0
