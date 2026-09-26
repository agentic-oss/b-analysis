import pytest
import pandas as pd
from src.ingestion.provider import MockDataProvider, YFinanceProvider

def test_mock_data_provider_prices():
    provider = MockDataProvider(seed=42)
    df = provider.get_historical_prices("RELIANCE", "2025-01-01", "2025-01-15")

    assert not df.empty
    expected_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "VWAP", "ticker", "exchange"]
    for col in expected_cols:
        assert col in df.columns

    assert (df["High"] >= df["Low"]).all()
    assert (df["Volume"] > 0).all()

def test_mock_data_provider_corporate_actions():
    provider = MockDataProvider()
    actions = provider.get_corporate_actions("TCS")
    assert actions["symbol"] == "TCS"
    assert "dividends" in actions

def test_yfinance_symbol_resolution():
    yf_prov = YFinanceProvider()
    assert yf_prov._resolve_yahoo_symbol("RELIANCE") == "RELIANCE.NS"
    assert yf_prov._resolve_yahoo_symbol("^NSEI") == "^NSEI"
    assert yf_prov._resolve_yahoo_symbol("TCS.NS") == "TCS.NS"
