"""
Tests for HistoricalAnalogueEngine.
"""
import numpy as np
import pandas as pd
from src.patterns.analogue import HistoricalAnalogueEngine


def test_analogue_engine():
    dates = pd.date_range("2020-01-01", periods=200)
    # Generate mock price series with oscillating RSI
    close = 100 + np.sin(np.linspace(0, 20, 200)) * 10
    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Close": close,
        "rsi_14": 50 + np.sin(np.linspace(0, 20, 200)) * 20,
        "dist_sma_50_pct": np.sin(np.linspace(0, 20, 200)) * 0.05,
    })

    result = HistoricalAnalogueEngine.find_analogues(df)

    assert "sample_size" in result
    assert "horizons" in result
    assert "1d" in result["horizons"]
    assert "mean_return_pct" in result["horizons"]["1d"]
