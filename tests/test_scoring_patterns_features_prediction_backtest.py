import pytest
import pandas as pd
import numpy as np
from src.scoring.composite_score import CompositeScorer
from src.patterns.historical_analogues import HistoricalPatternAnalyzer
from src.features.feature_engineering import FeatureEngineer
from src.modeling.prediction import DirectionalPredictor
from src.backtesting.engine import BacktestEngine


def test_composite_scorer():
    tech_signals = {
        "dist_sma_20": 0.02,
        "dist_sma_50": 0.05,
        "dist_sma_200": 0.10,
        "rsi_14": 65.0,
        "macd_hist": 1.5,
        "relative_volume": 1.5,
        "return_1d": 0.02,
        "volatility_regime": "Normal"
    }
    market_regime = {"regime": "Bullish", "nifty_return_1d": 0.005}

    res = CompositeScorer.compute_stock_score(tech_signals, market_regime, None, None)
    assert 0 <= res["composite_score"] <= 100
    assert res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]


def test_historical_analogues():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "close": prices,
        "rsi_14": 50 + np.sin(np.linspace(0, 10, 100)) * 10,
        "dist_sma_20": np.cos(np.linspace(0, 10, 100)) * 0.02,
        "relative_volume": np.ones(100)
    })

    res = HistoricalPatternAnalyzer.find_analogues(df)
    assert "matches_count" in res
    assert "forward_statistics" in res


def test_feature_engineer():
    df_stock = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "open": [100, 102],
        "high": [105, 106],
        "low": [98, 101],
        "close": [103, 105],
        "volume": [1000, 1200]
    })
    df_nifty = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "return_1d": [0.005, 0.01],
        "volatility_20d": [0.12, 0.12]
    })

    feat_df = FeatureEngineer.build_features(df_stock, df_nifty, include_targets=True)
    assert "market_return_1d" in feat_df.columns
    assert "future_return_1d" in feat_df.columns


def test_prediction_and_backtest():
    dates = pd.date_range("2024-01-01", periods=120, freq="B")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(120))
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "return_1d": np.random.randn(120) * 0.01,
        "return_5d": np.random.randn(120) * 0.02,
        "return_20d": np.random.randn(120) * 0.04,
        "rsi_14": np.random.uniform(30, 70, 120),
        "stoch_rsi_k": np.random.uniform(20, 80, 120),
        "macd_hist": np.random.randn(120),
        "atr_14": np.ones(120),
        "volatility_20d": np.ones(120) * 0.15,
        "dist_sma_20": np.random.randn(120) * 0.01,
        "dist_sma_50": np.random.randn(120) * 0.02,
        "relative_volume": np.ones(120),
        "market_return_1d": np.random.randn(120) * 0.005,
        "breakout": np.random.choice([True, False], 120, p=[0.1, 0.9]),
        "breakdown": np.random.choice([True, False], 120, p=[0.1, 0.9])
    })

    pred = DirectionalPredictor.train_and_evaluate(df, horizon_days=5)
    assert pred["status"] == "success"
    assert pred["directional_bias"] in ["Bullish", "Slightly Bullish", "Neutral", "Slightly Bearish", "Bearish"]

    bt = BacktestEngine().run_backtest(df)
    assert bt["status"] == "success"
    assert "total_return_pct" in bt
