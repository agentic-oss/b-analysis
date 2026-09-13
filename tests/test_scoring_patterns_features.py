import pytest
import pandas as pd
import numpy as np
from src.indicators.indicators import TechnicalIndicators
from src.scoring.scoring import StockScorer
from src.patterns.analogues import HistoricalPatternMatcher
from src.features.builder import FeatureBuilder

def test_stock_scorer():
    dates = pd.date_range("2026-01-01", periods=30, freq="D").strftime("%Y-%m-%d")
    df_stock = pd.DataFrame({
        'date': dates,
        'open': [100.0 + i for i in range(30)],
        'high': [105.0 + i for i in range(30)],
        'low': [99.0 + i for i in range(30)],
        'close': [102.0 + i for i in range(30)],
        'volume': [1000] * 30
    })
    df_stock = TechnicalIndicators.calculate_all(df_stock)

    df_nifty = pd.DataFrame({'date': dates, 'close': [20000] * 30, 'return_1d': [0.0] * 30})
    regime = {"regime": "Bullish"}

    score_res = StockScorer.calculate_score(df_stock, df_nifty, regime)
    assert 0.0 <= score_res["composite_score"] <= 100.0
    assert score_res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]
    assert "technical_trend" in score_res["components"]

def test_historical_pattern_matcher():
    dates = pd.date_range("2025-01-01", periods=100, freq="D").strftime("%Y-%m-%d")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        'date': dates,
        'open': prices - 0.5,
        'high': prices + 1.0,
        'low': prices - 1.0,
        'close': prices,
        'volume': [1500] * 100
    })
    df = TechnicalIndicators.calculate_all(df)

    res = HistoricalPatternMatcher.find_analogues(df, horizons=[1, 5])
    assert "observations_count" in res
    assert "1d" in res["horizons"]
    assert "5d" in res["horizons"]

def test_feature_builder_leakage_prevention():
    dates = pd.date_range("2026-01-01", periods=30, freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        'date': dates,
        'open': [100.0 + i for i in range(30)],
        'high': [105.0 + i for i in range(30)],
        'low': [99.0 + i for i in range(30)],
        'close': [102.0 + i for i in range(30)],
        'volume': [1000] * 30
    })
    df = TechnicalIndicators.calculate_all(df)

    feat_df = FeatureBuilder.build_features(df, "RELIANCE", include_targets=True)
    assert 'target_future_return_1d' in feat_df.columns
    # Check that last row target is NaN because future data is unavailable
    assert pd.isna(feat_df.iloc[-1]['target_future_return_1d'])
