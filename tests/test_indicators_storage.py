"""
Unit tests for Technical Indicators and Storage Manager.
"""
import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.storage.manager import StorageManager


def test_technical_indicators_calculation():
    dates = pd.date_range("2026-01-01", periods=60)
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.randn(60))

    df = pd.DataFrame({
        "Date": dates,
        "open": prices,
        "high": prices + 2.0,
        "low": prices - 2.0,
        "close": prices,
        "volume": 50000 + np.random.randint(0, 10000, 60)
    })

    enriched = TechnicalIndicators.compute_all(df)

    assert "sma_20" in enriched.columns
    assert "rsi_14" in enriched.columns
    assert "macd" in enriched.columns
    assert "atr_14" in enriched.columns
    assert "volatility_20d" in enriched.columns
    assert "obv" in enriched.columns

    # RSI bounded 0-100
    valid_rsi = enriched["rsi_14"].dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


def test_storage_manager(tmp_path):
    base_dir = str(tmp_path / "data")
    storage = StorageManager(base_dir=base_dir)

    df = pd.DataFrame({
        "Date": ["2026-09-28", "2026-09-29"],
        "close": [100.0, 102.0],
        "volume": [1000, 2000]
    })

    p_path = storage.save_processed_prices(df, "TEST_TICKER")
    assert p_path != ""

    retrieved_df = storage.get_processed_prices("TEST_TICKER")
    assert len(retrieved_df) == 2
    assert retrieved_df.iloc[-1]["close"] == 102.0
