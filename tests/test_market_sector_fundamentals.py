"""Tests for Market Regime, Sector Analysis, and Fundamentals."""

import numpy as np
import pandas as pd
import pytest

from src.market.regime import MarketRegimeDetector
from src.sectors.sector import SectorAnalyzer
from src.fundamentals.fundamentals import FundamentalAnalyzer


def test_market_regime_detector():
    dates = pd.date_range("2025-01-01", periods=200, freq="B")
    nifty_df = pd.DataFrame({
        "Date": dates,
        "Close": np.linspace(100, 200, 200),
        "sma_20": np.linspace(98, 198, 200),
        "sma_50": np.linspace(95, 195, 200),
        "sma_200": np.linspace(80, 180, 200),
        "return_1d": [0.001] * 200
    })

    stock_dfs = {}
    for sym in ["RELIANCE", "TCS", "HDFCBANK"]:
        stock_dfs[sym] = pd.DataFrame({
            "Date": dates,
            "Close": np.linspace(100, 200, 200),
            "sma_20": np.linspace(98, 198, 200),
            "sma_50": np.linspace(95, 195, 200),
            "sma_200": np.linspace(80, 180, 200),
            "return_1d": [0.001] * 200,
            "breakout": [False] * 199 + [True]
        })

    regime_res = MarketRegimeDetector.analyze_regime(nifty_df, stock_dfs=stock_dfs)
    assert regime_res["regime"] in ["Strong Bullish", "Bullish"]
    assert regime_res["regime_score"] >= 60.0
    assert regime_res["breadth"]["pct_above_50dma"] == 100.0


def test_sector_analyzer():
    dates = pd.date_range("2025-01-01", periods=30, freq="B")
    nifty_df = pd.DataFrame({
        "Date": dates,
        "Close": np.linspace(100, 110, 30),
        "return_1d": [0.001] * 30
    })

    sec_it = pd.DataFrame({
        "Date": dates,
        "Close": np.linspace(100, 130, 30),  # Stronger growth
        "return_1d": [0.005] * 30,
        "rsi_14": [65.0] * 30
    })

    sec_auto = pd.DataFrame({
        "Date": dates,
        "Close": np.linspace(100, 90, 30),   # Negative growth
        "return_1d": [-0.003] * 30,
        "rsi_14": [35.0] * 30
    })

    sectors = {"NIFTY IT": sec_it, "NIFTY Auto": sec_auto}
    rankings = SectorAnalyzer.analyze_sectors(sectors, nifty_df)

    assert len(rankings) == 2
    assert rankings[0]["sector"] == "NIFTY IT"
    assert rankings[0]["rank"] == 1
    assert rankings[1]["sector"] == "NIFTY Auto"


def test_fundamental_analyzer_scoring():
    sample_fund = {
        "symbol": "RELIANCE",
        "roe": 22.0,
        "debt_to_equity": 25.0,
        "profit_growth_pct": 18.0,
        "net_margin_pct": 16.0
    }
    score = FundamentalAnalyzer.calculate_fundamental_score(sample_fund)
    assert score > 70.0  # Should be high score for strong fundamentals
