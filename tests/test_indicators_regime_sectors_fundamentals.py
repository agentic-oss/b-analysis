import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamentals import FundamentalAnalyzer


def test_technical_indicators():
    dates = pd.date_range("2025-01-01", periods=250, freq="B")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(250))
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": prices,
        "high": prices + 2,
        "low": prices - 2,
        "close": prices + 0.5,
        "volume": np.random.randint(10000, 50000, 250)
    })

    df_ind = TechnicalIndicators.calculate_indicators(df)
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "atr_14" in df_ind.columns
    assert "sma_200" in df_ind.columns

    signals = TechnicalIndicators.get_latest_signals(df_ind)
    assert "rsi_14" in signals
    assert isinstance(signals["events"], list)


def test_market_regime():
    dates = pd.date_range("2025-01-01", periods=50, freq="B")
    nifty_df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "close": [20000 + i * 10 for i in range(50)],
        "sma_20": [20000 + i * 8 for i in range(50)],
        "sma_50": [19500 + i * 5 for i in range(50)],
        "sma_200": [18000 + i * 2 for i in range(50)],
        "return_1d": [0.001] * 50,
        "volatility_20d": [0.12] * 50
    })

    stock_df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "close": [100 + i for i in range(50)],
        "sma_20": [98 + i for i in range(50)],
        "sma_50": [95 + i for i in range(50)],
        "sma_200": [80 + i for i in range(50)],
        "return_1d": [0.01] * 50,
        "dist_52w_high": [0.0] * 50,
        "dist_52w_low": [0.5] * 50
    })

    regime = MarketRegimeAnalyzer.analyze_regime(nifty_df, nifty_df, {"RELIANCE": stock_df})
    assert regime["regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert regime["breadth"]["total_stocks"] == 1


def test_sector_analysis():
    nifty_df = pd.DataFrame({"return_1d": [0.01] * 5})
    sector_df = pd.DataFrame({
        "return_1d": [0.02] * 5,
        "return_5d": [0.05] * 5,
        "return_20d": [0.10] * 5,
        "rsi_14": [60.0] * 5,
        "volatility_20d": [0.15] * 5
    })
    stock_df = pd.DataFrame({"return_1d": [0.02] * 5, "close": [100.0] * 5})

    res = SectorAnalyzer.analyze_sectors(
        {"NIFTY BANK": sector_df},
        nifty_df,
        {"HDFCBANK": stock_df},
        {"HDFCBANK": "NIFTY BANK"}
    )
    assert len(res["sectors"]) == 1
    assert res["sectors"][0]["sector"] == "NIFTY BANK"


def test_fundamental_analysis():
    fund_data = {
        "available": True,
        "pe_ratio": 20.0,
        "pb_ratio": 2.5,
        "roe": 0.18,
        "profit_margins": 0.12,
        "debt_to_equity": 40.0,
        "revenue_growth": 0.12,
        "provider": "yfinance"
    }
    res = FundamentalAnalyzer.analyze_fundamentals(fund_data)
    assert res["available"] is True
    assert 0 <= res["fundamental_score"] <= 100
