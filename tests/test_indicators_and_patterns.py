import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.patterns.pattern_engine import PatternEngine
from src.patterns.analogue_finder import AnalogueFinder

def test_technical_indicators_calculation():
    dates = pd.date_range(start="2024-01-01", periods=220, freq="B")
    df = pd.DataFrame({
        "symbol": "RELIANCE",
        "date": dates.strftime("%Y-%m-%d"),
        "open": np.linspace(100, 200, 220),
        "high": np.linspace(105, 205, 220),
        "low": np.linspace(95, 195, 220),
        "close": np.linspace(102, 202, 220),
        "volume": np.random.randint(1000, 5000, 220)
    })

    calc_df = TechnicalIndicators.calculate_all(df)
    assert "sma_20" in calc_df.columns
    assert "rsi_14" in calc_df.columns
    assert "macd" in calc_df.columns
    assert "atr_14" in calc_df.columns
    assert "volatility_20d" in calc_df.columns
    assert len(calc_df) == 220

def test_pattern_engine_detection():
    dates = pd.date_range(start="2024-01-01", periods=50, freq="B")
    df = pd.DataFrame({
        "symbol": "TCS",
        "date": dates.strftime("%Y-%m-%d"),
        "open": 100.0,
        "high": 105.0,
        "low": 95.0,
        "close": 102.0,
        "volume": 1000
    })
    calc_df = TechnicalIndicators.calculate_all(df)
    # Force a volume spike and overbought RSI on last row
    calc_df.loc[calc_df.index[-1], 'relative_volume'] = 3.5
    calc_df.loc[calc_df.index[-1], 'rsi_14'] = 75.0

    res = PatternEngine.detect_events(calc_df)
    assert any("Unusual Volume" in e for e in res["events"])
    assert any("Overbought" in e for e in res["events"])

def test_analogue_finder():
    dates = pd.date_range(start="2023-01-01", periods=300, freq="B")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(300))
    df = pd.DataFrame({
        "symbol": "INFY",
        "date": dates.strftime("%Y-%m-%d"),
        "open": prices,
        "high": prices + 1.0,
        "low": prices - 1.0,
        "close": prices,
        "volume": np.random.randint(1000, 5000, 300)
    })
    calc_df = TechnicalIndicators.calculate_all(df)
    finder = AnalogueFinder()
    res = finder.find_analogues(calc_df)
    assert "num_matches" in res
    assert "horizons" in res
    assert "1d" in res["horizons"]
