import pytest
import pandas as pd
import numpy as np
from src.scoring.stock_scorer import StockScorer
from src.patterns.historical_analogue import HistoricalAnalogueEngine
from src.features.feature_engineer import FeatureEngineer
from src.modeling.predictive_model import PredictiveModelManager
from src.backtesting.backtest_engine import BacktestingEngine

def test_stock_scorer():
    df = pd.DataFrame({
        "close": [100.0, 105.0, 110.0],
        "sma_20": [95.0, 96.0, 97.0],
        "sma_50": [90.0, 91.0, 92.0],
        "sma_200": [80.0, 81.0, 82.0],
        "rsi_14": [60.0, 65.0, 70.0],
        "relative_volume": [1.5, 1.8, 2.1],
        "return_1d": [0.01, 0.02, 0.03],
        "return_5d": [0.02, 0.04, 0.06],
        "volatility_20d": [0.15, 0.16, 0.15]
    })
    scorer = StockScorer()
    res = scorer.calculate_score(df)
    assert 0 <= res["composite_score"] <= 100
    assert res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]

def test_historical_analogue():
    dates = pd.date_range("2024-01-01", periods=100, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        "Date": dates,
        "close": closes,
        "rsi_14": 50 + np.sin(np.linspace(0, 10, 100)) * 15,
        "volatility_20d": [0.15] * 100,
        "relative_volume": [1.0] * 100
    })
    engine = HistoricalAnalogueEngine()
    res = engine.find_analogues_and_forward_stats(df)
    assert "matches_found" in res
    assert "forward_probabilities" in res
    assert "directional_bias" in res

def test_feature_engineer_leakage_free():
    dates = pd.date_range("2025-01-01", periods=10, freq="B").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "Date": dates,
        "open": [100 + i for i in range(10)],
        "high": [101 + i for i in range(10)],
        "low": [99 + i for i in range(10)],
        "close": [100 + i for i in range(10)],
        "volume": [1000] * 10
    })
    fe = FeatureEngineer()
    f_df = fe.build_feature_set(df, "TEST")
    assert "future_return_1d" in f_df.columns
    # Verify target at row 0 matches (close[1] - close[0]) / close[0]
    expected_ret_1d = (df.iloc[1]["close"] - df.iloc[0]["close"]) / df.iloc[0]["close"]
    assert pytest.approx(f_df.iloc[0]["future_return_1d"], 0.001) == expected_ret_1d

def test_predictive_model():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "rsi_14": np.random.uniform(30, 70, n),
        "stoch_rsi": np.random.uniform(0, 1, n),
        "macd": np.random.randn(n),
        "macd_signal": np.random.randn(n),
        "atr_14": np.random.uniform(1, 5, n),
        "volatility_20d": np.random.uniform(0.1, 0.3, n),
        "relative_volume": np.random.uniform(0.5, 2.0, n),
        "dist_sma_20": np.random.uniform(-0.05, 0.05, n),
        "dist_sma_50": np.random.uniform(-0.1, 0.1, n),
        "dist_sma_200": np.random.uniform(-0.2, 0.2, n),
        "dist_52w_high": np.random.uniform(-0.2, 0, n),
        "dist_52w_low": np.random.uniform(0, 0.5, n),
        "return_1d": np.random.randn(n) * 0.01,
        "return_5d": np.random.randn(n) * 0.02,
        "future_return_5d": np.random.randn(n) * 0.03
    })
    model_mgr = PredictiveModelManager()
    metrics = model_mgr.train_and_evaluate(df, target_col="future_return_5d")
    assert "accuracy" in metrics
    assert "f1_score" in metrics

def test_backtesting_engine():
    dates = pd.date_range("2024-01-01", periods=60, freq="B").strftime("%Y-%m-%d")
    closes = [100 + i for i in range(60)]
    df = pd.DataFrame({
        "Date": dates,
        "close": closes,
        "composite_score": [75.0] * 60
    })
    bt = BacktestingEngine()
    results = bt.run_backtest({"TEST": df})
    assert results["total_trades"] > 0
    assert "cumulative_return_pct" in results
