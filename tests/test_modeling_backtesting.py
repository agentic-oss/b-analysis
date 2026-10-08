import pytest
import pandas as pd
import numpy as np

from src.indicators.technical import TechnicalIndicators
from src.features.feature_engineer import FeatureEngineer
from src.modeling.prediction import PredictionResearchLayer
from src.backtesting.backtest import Backtester


def test_prediction_research_layer():
    dates = pd.date_range("2023-01-01", periods=350, freq="D").strftime("%Y-%m-%d").tolist()
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(350))
    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": [1000] * 350
    })

    df_ind = TechnicalIndicators.compute_all(df)
    df_feat = FeatureEngineer.generate_features(df_ind, horizons=[5])

    pred_layer = PredictionResearchLayer(target_horizon=5)
    metrics = pred_layer.train_and_evaluate_walk_forward(df_feat, train_window=200, test_window=50)

    assert "logistic_regression" in metrics
    assert "random_forest" in metrics
    assert "accuracy" in metrics["logistic_regression"]
    assert "accuracy" in metrics["random_forest"]


def test_backtesting_engine():
    dates = pd.date_range("2024-01-01", periods=100, freq="D").strftime("%Y-%m-%d").tolist()
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": [1000] * 100,
        "signal": [1 if i % 10 == 0 else 0 for i in range(100)]
    })

    backtester = Backtester(initial_capital=100000.0)
    res = backtester.run_signal_backtest(df, signal_col="signal", holding_period_days=3)

    assert "total_return_pct" in res
    assert "max_drawdown_pct" in res
    assert "sharpe_ratio" in res
    assert "total_trades" in res
