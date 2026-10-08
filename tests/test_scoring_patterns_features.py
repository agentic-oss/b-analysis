import pytest
import pandas as pd
import numpy as np

from src.indicators.technical import TechnicalIndicators
from src.scoring.scorer import StockScorer
from src.patterns.pattern_engine import PatternAnalogueEngine
from src.features.feature_engineer import FeatureEngineer


def test_stock_scorer():
    stock_latest = {
        "ticker": "RELIANCE",
        "close": 2500.0,
        "sma_20": 2400.0,
        "sma_50": 2300.0,
        "sma_200": 2100.0,
        "rsi_14": 62.0,
        "macd": 15.0,
        "macd_signal": 10.0,
        "relative_volume": 1.5,
        "dist_52w_high": -3.5,
        "return_1d": 0.015
    }
    market_regime = {"classification": "Bullish"}
    sector_info = {"rank": 2}

    res = StockScorer.calculate_score(stock_latest, market_regime, sector_info)
    assert "total_score" in res
    assert 0 <= res["total_score"] <= 100
    assert res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]


def test_pattern_analogue_engine():
    dates = pd.date_range("2024-01-01", periods=100, freq="D").strftime("%Y-%m-%d").tolist()
    np.random.seed(10)
    prices = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": [1000] * 100
    })
    df = TechnicalIndicators.compute_all(df)

    engine = PatternAnalogueEngine(rsi_tolerance=10.0)
    curr_state = {"rsi_14": df.iloc[-1]["rsi_14"]}
    res = engine.find_analogues(df, curr_state)

    assert "historical_sample_count" in res
    assert "horizons" in res
    assert "5d" in res["horizons"]


def test_feature_engineer_no_lookahead_leakage():
    dates = pd.date_range("2024-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
    df = pd.DataFrame({
        "date": dates,
        "open": range(100, 150),
        "high": range(101, 151),
        "low": range(99, 149),
        "close": range(100, 150),
        "volume": [1000] * 50
    })
    df_feat = FeatureEngineer.generate_features(df, horizons=[1, 5])

    # Check that future_return_1d for index 0 matches return between index 0 and 1
    # Index 0 close = 100, Index 1 close = 101 -> return = 0.01
    assert abs(df_feat.loc[0, "future_return_1d"] - 0.01) < 1e-4
    # Check last row future return is NaN due to shift(-1)
    assert pd.isna(df_feat.loc[49, "future_return_1d"])
