"""Tests for Modeling and Backtesting Modules."""

import numpy as np
import pandas as pd
import pytest

from src.indicators.technical import TechnicalIndicators
from src.features.engineer import FeatureEngineer
from src.modeling.predictor import ProbabilisticPredictor
from src.backtesting.engine import BacktestEngine


def test_probabilistic_predictor():
    dates = pd.date_range("2023-01-01", periods=200, freq="B")
    np.random.seed(42)
    prices = [100.0]
    for _ in range(199):
        prices.append(prices[-1] * (1 + np.random.normal(0.0005, 0.015)))

    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p * 1.01 for p in prices],
        "Low": [p * 0.99 for p in prices],
        "Close": prices,
        "Volume": [50000] * 200
    })

    calc_df = TechnicalIndicators.calculate_all(df)
    feat_df = FeatureEngineer.build_features_for_stock(calc_df)

    predictor = ProbabilisticPredictor(model_type="random_forest")
    res = predictor.train_and_evaluate(feat_df, horizon_days=5)

    assert res["status"] == "success"
    assert "out_of_sample_accuracy" in res
    assert "out_of_sample_f1" in res


def test_backtest_engine():
    dates = pd.date_range("2025-01-01", periods=100, freq="B")
    np.random.seed(42)
    prices = np.linspace(100, 150, 100)  # Uptrend

    # Generate signals: Buy every 10 bars
    signals = [1 if i % 10 == 0 else 0 for i in range(100)]

    df = pd.DataFrame({
        "Date": dates,
        "Close": prices,
        "signal": signals
    })

    engine = BacktestEngine(initial_capital=100000.0)
    res = engine.run_backtest(df, signal_column="signal", holding_period=5)

    assert res["status"] == "success"
    assert res["total_trades"] > 0
    assert "net_return_pct" in res
    assert "max_drawdown_pct" in res
    assert "sharpe_ratio" in res
