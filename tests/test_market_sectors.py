import pytest
import pandas as pd
import numpy as np
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer


def test_market_regime_analyzer():
    dates = pd.date_range("2025-01-01", periods=50, freq="B").strftime("%Y-%m-%d")

    # NIFTY dataframe
    index_df = pd.DataFrame({
        "date": dates,
        "close": np.linspace(100, 150, 50),
        "sma_20": np.linspace(95, 140, 50),
        "sma_50": np.linspace(90, 130, 50),
        "sma_200": np.linspace(80, 110, 50),
    })

    # Sample stock dataframes
    stocks = {}
    for symbol in ["STOCK1", "STOCK2", "STOCK3"]:
        stocks[symbol] = pd.DataFrame({
            "date": dates,
            "close": np.linspace(50, 100, 50),
            "sma_20": np.linspace(45, 90, 50),
            "sma_50": np.linspace(40, 80, 50),
            "sma_200": np.linspace(30, 70, 50),
            "daily_return": [0.01] * 50,
            "breakout_20d": [False] * 49 + [True],
            "breakdown_20d": [False] * 50
        })

    analyzer = MarketRegimeAnalyzer()
    res = analyzer.analyze_regime(index_df, stocks)

    assert res["regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert res["pct_above_20dma"] == 100.0
    assert res["advances"] == 3
    assert res["total_tracked_stocks"] == 3


def test_sector_analyzer():
    dates = pd.date_range("2025-01-01", periods=30, freq="B").strftime("%Y-%m-%d")

    bm_df = pd.DataFrame({
        "date": dates,
        "close": np.linspace(100, 110, 30)
    })

    sectors_dfs = {
        "NIFTY IT": pd.DataFrame({"date": dates, "close": np.linspace(100, 130, 30)}),
        "NIFTY Bank": pd.DataFrame({"date": dates, "close": np.linspace(100, 90, 30)}),
    }

    sec_analyzer = SectorAnalyzer()
    rankings = sec_analyzer.analyze_sectors(sectors_dfs, bm_df)

    assert len(rankings) == 2
    assert rankings[0]["sector"] == "NIFTY IT"
    assert rankings[0]["rank"] == 1
    assert rankings[1]["sector"] == "NIFTY Bank"
    assert rankings[1]["rank"] == 2
