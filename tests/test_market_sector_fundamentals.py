import pytest
import pandas as pd
import numpy as np
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamental_analysis import FundamentalAnalyzer

def create_mock_df(trend="bull"):
    dates = pd.date_range(end="2026-03-01", periods=100, freq="B").strftime("%Y-%m-%d").tolist()
    if trend == "bull":
        prices = np.linspace(100, 150, 100) + np.random.normal(0, 1, 100)
    else:
        prices = np.linspace(150, 100, 100) + np.random.normal(0, 1, 100)

    return pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": [10000] * 100
    })

def test_market_regime_analysis():
    nifty = create_mock_df("bull")
    stocks = {
        "STK1": create_mock_df("bull"),
        "STK2": create_mock_df("bull"),
        "STK3": create_mock_df("bear")
    }
    regime_res = MarketRegimeAnalyzer.analyze_regime(nifty, stocks)
    assert regime_res["regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert regime_res["advance_decline_ratio"] >= 0

def test_sector_analysis():
    nifty = create_mock_df("bull")
    sectors = {
        "IT": create_mock_df("bull"),
        "Auto": create_mock_df("bear")
    }
    rankings = SectorAnalyzer.analyze_sectors(sectors, nifty)
    assert len(rankings) == 2
    assert rankings[0]["rank"] == 1
    assert rankings[0]["sector"] == "IT"

def test_fundamental_analysis():
    fund_data = {
        "pe_ratio": 12.5,
        "roe": 0.22,
        "revenue_growth": 0.18,
        "debt_to_equity": 25.0,
        "source": "yfinance"
    }
    res = FundamentalAnalyzer.evaluate(fund_data)
    assert res["fundamental_score"] > 70.0
    assert res["valuation_status"] == "Undervalued"
