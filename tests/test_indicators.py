import pytest
import pandas as pd
import numpy as np
from src.indicators.indicators import TechnicalAnalysisEngine
from src.fundamentals.analyzer import FundamentalAnalyzer


def test_technical_analysis_engine():
    dates = pd.date_range("2025-01-01", periods=210, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(210))
    highs = closes + np.random.rand(210) * 2
    lows = closes - np.random.rand(210) * 2
    opens = (highs + lows) / 2
    volumes = np.random.randint(1000, 10000, size=210)

    df = pd.DataFrame({
        "date": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes
    })

    engine = TechnicalAnalysisEngine()
    ind_df = engine.calculate_indicators(df)

    # Check key columns present
    assert "sma_20" in ind_df.columns
    assert "sma_200" in ind_df.columns
    assert "ema_20" in ind_df.columns
    assert "rsi_14" in ind_df.columns
    assert "macd" in ind_df.columns
    assert "atr_14" in ind_df.columns
    assert "volatility_20d" in ind_df.columns
    assert "bb_upper" in ind_df.columns
    assert "relative_volume" in ind_df.columns

    events = engine.extract_latest_events(ind_df)
    assert "golden_cross" in events
    assert "rsi_14" in events
    assert "support_level_1" in events


def test_fundamental_analyzer():
    analyzer = FundamentalAnalyzer()

    # Case 1: Healthy fundamentals
    good_data = {
        "pe_ratio": 18.0,
        "roe": 0.22,
        "debt_to_equity": 20.0,
        "profit_growth": 0.18
    }
    good_res = analyzer.analyze(good_data)
    assert good_res["fundamental_score"] >= 70.0
    assert good_res["available"] is True

    # Case 2: Missing data
    empty_res = analyzer.analyze({})
    assert empty_res["fundamental_score"] == 50.0
    assert empty_res["available"] is False
