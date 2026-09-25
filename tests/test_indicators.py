"""Unit tests for Technical Indicators Module."""

import numpy as np
import pandas as pd
import pytest
from src.indicators.technical import TechnicalIndicators


def test_technical_indicators_calculation():
    dates = pd.date_range("2025-01-01", periods=250, freq="B")
    np.random.seed(42)
    price = 100.0
    prices = []
    highs = []
    lows = []
    volumes = []

    for _ in range(250):
        ret = np.random.normal(0.0005, 0.015)
        price *= (1 + ret)
        high = price * (1 + abs(np.random.normal(0, 0.005)))
        low = price * (1 - abs(np.random.normal(0, 0.005)))
        vol = np.random.randint(10000, 50000)
        prices.append(price)
        highs.append(high)
        lows.append(low)
        volumes.append(vol)

    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": highs,
        "Low": lows,
        "Close": prices,
        "Volume": volumes
    })

    calc_df = TechnicalIndicators.calculate_all(df)

    # Check key indicator columns exist
    expected_cols = [
        "return_1d", "sma_5", "sma_20", "sma_50", "sma_200",
        "ema_9", "ema_20", "ema_50", "ema_200",
        "rsi_14", "stoch_rsi", "macd", "macd_signal", "macd_hist",
        "atr_14", "volatility_20d", "bb_upper", "bb_lower", "bb_width",
        "relative_volume", "obv", "dist_52w_high_pct", "golden_cross", "breakout"
    ]
    for col in expected_cols:
        assert col in calc_df.columns, f"Column {col} missing from output"

    # Verify RSI range [0, 100]
    assert (calc_df["rsi_14"] >= 0).all() and (calc_df["rsi_14"] <= 100).all()

    # Verify summary extraction
    summary = TechnicalIndicators.get_latest_summary(calc_df)
    assert summary["date"] == str(dates[-1].date())
    assert "rsi_14" in summary
    assert "volatility_20d" in summary
