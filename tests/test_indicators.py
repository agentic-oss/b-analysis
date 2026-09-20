import pytest
import pandas as pd
from src.ingestion.mock_provider import MockMarketDataProvider
from src.indicators.technical import TechnicalIndicators

def test_technical_indicators():
    provider = MockMarketDataProvider()
    df = provider.get_historical_prices("RELIANCE.NS", "2025-01-01", "2026-03-30")
    df_ind = TechnicalIndicators.calculate_indicators(df)

    assert "sma_20" in df_ind.columns
    assert "sma_200" in df_ind.columns
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "atr_14" in df_ind.columns
    assert "dist_52w_high_pct" in df_ind.columns
    assert not df_ind["rsi_14"].isna().any()
