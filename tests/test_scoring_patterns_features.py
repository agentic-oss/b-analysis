import pytest
import pandas as pd
import numpy as np
from src.scoring.scorer import StockScorer
from src.patterns.matcher import PatternAnalogueMatcher
from src.features.builder import FeatureEngineer
from src.modeling.pipeline import PredictiveModelPipeline
from src.backtesting.engine import BacktestEngine


def test_stock_scorer():
    scorer = StockScorer()
    stock_ind = {
        "close": 110.0,
        "sma_20": 105.0,
        "sma_50": 100.0,
        "sma_200": 90.0,
        "rsi_14": 62.0,
        "macd_hist": 1.2,
        "roc_10": 3.5,
        "relative_volume": 1.6,
        "daily_return": 0.02,
        "dist_52w_high": -2.0,
        "volatility_regime": "Normal"
    }
    mkt_info = {"regime_score": 75.0}
    sec_info = {"momentum_score": 5.0}
    fund_info = {"available": True, "fundamental_score": 80.0}

    score_res = scorer.compute_score(stock_ind, mkt_info, sec_info, fund_info)
    assert "composite_score" in score_res
    assert score_res["composite_score"] >= 70.0
    assert score_res["label"] in ["Strong", "Very Strong"]


def test_pattern_analogue_matcher():
    matcher = PatternAnalogueMatcher()
    dates = pd.date_range("2024-01-01", periods=150, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(150))

    df = pd.DataFrame({
        "date": dates,
        "close": closes,
        "rsi_14": [50.0 + np.sin(i / 5.0) * 15 for i in range(150)],
        "relative_volume": [1.0 + np.cos(i / 5.0) * 0.3 for i in range(150)],
        "dist_sma_20": [0.0 + np.sin(i / 10.0) * 2.0 for i in range(150)]
    })

    res = matcher.find_analogues_and_forward_returns(df, horizons=[1, 5, 20])
    assert "observations_count" in res
    assert "forward_probabilities" in res
    assert "5d" in res["forward_probabilities"]


def test_feature_engineer_and_ml_modeling():
    fe = FeatureEngineer()
    dates = pd.date_range("2024-01-01", periods=120, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(120) * 0.5)

    df = pd.DataFrame({
        "date": dates,
        "open": closes * 0.99,
        "high": closes * 1.01,
        "low": closes * 0.98,
        "close": closes,
        "volume": np.random.randint(1000, 5000, size=120),
        "rsi_14": 55.0,
        "stoch_rsi": 50.0,
        "macd_hist": 0.5,
        "atr_14": 1.5,
        "volatility_20d": 12.0,
        "dist_sma_20": 1.0,
        "dist_sma_50": 2.0,
        "dist_sma_200": 5.0,
        "relative_volume": 1.2,
        "dist_52w_high": -3.0,
        "dist_52w_low": 15.0
    })

    f_df = fe.build_features(df, "RELIANCE")
    assert "future_return_5d" in f_df.columns
    assert "target_direction_5d" in f_df.columns

    pipeline = PredictiveModelPipeline()
    ml_res = pipeline.evaluate_walk_forward(f_df)
    assert "logistic_regression" in ml_res
    assert "accuracy" in ml_res["logistic_regression"]


def test_backtest_engine():
    bt = BacktestEngine(initial_capital=100000.0)
    dates = pd.date_range("2025-01-01", periods=20, freq="B").strftime("%Y-%m-%d")
    closes = [100.0 + i for i in range(20)]
    opens = [99.5 + i for i in range(20)]

    df = pd.DataFrame({"date": dates, "open": opens, "close": closes})
    signals = pd.Series([1] * 10 + [0] * 10)

    res = bt.run_backtest(df, signals)
    assert "final_capital" in res
    assert "total_return_pct" in res
    assert res["total_trades"] >= 1
