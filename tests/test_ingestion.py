import pytest
import pandas as pd
from src.ingestion.mock_provider import MockMarketDataProvider
from src.ingestion.yfinance_provider import YahooFinanceProvider

def test_mock_provider():
    provider = MockMarketDataProvider()
    df = provider.get_historical_prices("RELIANCE.NS", "2026-01-01", "2026-01-10")
    assert not df.empty
    assert "open" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns
    assert len(df) > 0

def test_yfinance_provider_fallback():
    provider = YahooFinanceProvider(fallback_to_mock=True)
    df = provider.get_historical_prices("INVALID_SYMBOL_12345.NS", "2026-01-01", "2026-01-10")
    assert not df.empty
