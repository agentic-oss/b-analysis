"""
Tests for TechnicalIndicators and PatternDetector.
"""
import numpy as np
import pandas as pd
from src.indicators.technical import TechnicalIndicators
from src.indicators.patterns import PatternDetector


def test_technical_indicators_calculation():
    dates = pd.date_range("2024-01-01", periods=60)
    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": np.linspace(100, 200, 60),
        "High": np.linspace(102, 202, 60),
        "Low": np.linspace(98, 198, 60),
        "Close": np.linspace(101, 201, 60),
        "Volume": [10000] * 60,
    })

    enriched = TechnicalIndicators.calculate_all(df)

    assert "sma_20" in enriched.columns
    assert "rsi_14" in enriched.columns
    assert "macd" in enriched.columns
    assert "atr_14" in enriched.columns
    assert "volatility_20d" in enriched.columns
    assert "bollinger_upper" in enriched.columns
    assert not enriched["rsi_14"].isna().all()


def test_pattern_detector():
    df = pd.DataFrame({
        "ticker": ["TEST"] * 5,
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"],
        "Open": [100, 100, 100, 100, 100],
        "High": [105, 105, 105, 105, 120],  # Breakout on last day
        "Low": [95, 95, 95, 95, 95],
        "Close": [100, 100, 100, 100, 118],
        "Volume": [1000, 1000, 1000, 1000, 5000],
        "relative_volume": [1.0, 1.0, 1.0, 1.0, 3.0],
        "rsi_14": [50, 50, 50, 50, 75],
    })

    events = PatternDetector.detect_events(df)
    assert len(events) > 0
    event_types = [e["type"] for e in events]
    assert "20-Day High Breakout" in event_types or "Unusual Volume Surge" in event_types
