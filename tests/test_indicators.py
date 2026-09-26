import pytest
import pandas as pd
import numpy as np
from src.ingestion.provider import MockDataProvider
from src.indicators.technical import calculate_technical_indicators, detect_technical_signals

def test_calculate_technical_indicators():
    provider = MockDataProvider(seed=42)
    df = provider.get_historical_prices("RELIANCE", "2024-01-01", "2025-01-01")

    df_ind = calculate_technical_indicators(df)

    assert "sma_20" in df_ind.columns
    assert "ema_20" in df_ind.columns
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "atr_14" in df_ind.columns
    assert "volatility_20d" in df_ind.columns
    assert "bollinger_upper" in df_ind.columns
    assert "relative_volume" in df_ind.columns

    # Check RSI range
    assert (df_ind["rsi_14"] >= 0).all() and (df_ind["rsi_14"] <= 100).all()

def test_detect_technical_signals():
    provider = MockDataProvider(seed=42)
    df = provider.get_historical_prices("RELIANCE", "2024-01-01", "2025-01-01")
    df_ind = calculate_technical_indicators(df)

    signals = detect_technical_signals(df_ind)
    assert "golden_cross" in signals
    assert "death_cross" in signals
    assert "breakout" in signals
    assert "trend" in signals
    assert "support_level" in signals
