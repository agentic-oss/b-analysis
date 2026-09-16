import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.fundamentals.fundamental_analyzer import FundamentalAnalyzer
from src.market.market_regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer

def test_technical_indicators():
    dates = pd.date_range("2025-01-01", periods=60, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(60))
    df = pd.DataFrame({
        "Date": dates,
        "open": closes - 0.5,
        "high": closes + 1.0,
        "low": closes - 1.0,
        "close": closes,
        "volume": np.random.randint(1000, 5000, 60)
    })

    ind_df = TechnicalIndicators.calculate_all(df)
    assert "sma_20" in ind_df.columns
    assert "ema_20" in ind_df.columns
    assert "rsi_14" in ind_df.columns
    assert "macd" in ind_df.columns
    assert "atr_14" in ind_df.columns
    assert "bollinger_upper" in ind_df.columns
    assert "volatility_20d" in ind_df.columns
    assert not ind_df["rsi_14"].isna().all()

def test_market_regime():
    dates = pd.date_range("2025-01-01", periods=60, freq="B").strftime("%Y-%m-%d")
    nifty_df = pd.DataFrame({
        "Date": dates,
        "close": [100 + i for i in range(60)],
        "sma_20": [95 + i for i in range(60)],
        "sma_50": [90 + i for i in range(60)],
        "sma_200": [80 + i for i in range(60)],
        "return_1d": [0.01] * 60
    })
    stock_df1 = pd.DataFrame({
        "Date": dates,
        "close": [50 + i for i in range(60)],
        "sma_20": [48 + i for i in range(60)],
        "sma_50": [45 + i for i in range(60)],
        "sma_200": [40 + i for i in range(60)],
        "return_1d": [0.01] * 60,
        "breakout_20d": [False] * 60,
        "breakdown_20d": [False] * 60
    })
    stock_df2 = stock_df1.copy()
    stock_df2["return_1d"] = -0.005  # decline to give ad_ratio 1.0

    analyzer = MarketRegimeAnalyzer()
    res = analyzer.analyze_market_regime(nifty_df, None, {"STOCK1": stock_df1})
    assert res["regime"] in ["Strong Bullish", "Bullish"]
    assert res["market_breadth"]["pct_above_50dma"] == 100.0

def test_sector_analyzer():
    dates = pd.date_range("2025-01-01", periods=60, freq="B").strftime("%Y-%m-%d")
    df1 = pd.DataFrame({"Date": dates, "return_1d": [0.02]*60, "return_5d": [0.05]*60, "return_20d": [0.10]*60, "volatility_20d": [0.15]*60, "rsi_14": [65]*60})
    df2 = pd.DataFrame({"Date": dates, "return_1d": [-0.01]*60, "return_5d": [-0.02]*60, "return_20d": [-0.05]*60, "volatility_20d": [0.20]*60, "rsi_14": [40]*60})

    analyzer = SectorAnalyzer()
    rankings = analyzer.analyze_sectors({"IT": df1, "AUTO": df2}, df1)
    assert len(rankings) == 2
    assert rankings[0]["sector"] == "IT"
    assert rankings[0]["rank"] == 1
