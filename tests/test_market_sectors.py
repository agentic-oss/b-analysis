import pytest
import pandas as pd
import numpy as np
from src.fundamentals.fundamentals import FundamentalsCollector
from src.market.regime import MarketRegimeDetector
from src.sectors.sectors import SectorAnalyzer

def test_fundamentals_collector():
    f = FundamentalsCollector.get_fundamentals("RELIANCE.NS")
    assert "symbol" in f
    assert f["symbol"] == "RELIANCE.NS"
    assert "source" in f

def test_market_regime_detector():
    dates = pd.date_range("2026-01-01", periods=60, freq="D").strftime("%Y-%m-%d")
    df_nifty = pd.DataFrame({
        'date': dates,
        'close': [20000 + i * 10 for i in range(60)],
        'return_1d': [0.001] * 60,
        'sma_20': [20000 + i * 8 for i in range(60)],
        'sma_50': [20000 + i * 5 for i in range(60)],
        'sma_200': [20000] * 60,
    })

    stock_df = pd.DataFrame({
        'date': dates,
        'close': [100 + i for i in range(60)],
        'return_1d': [0.005] * 60,
        'sma_20': [100 + i * 0.8 for i in range(60)],
        'sma_50': [100 + i * 0.5 for i in range(60)],
        'sma_200': [100] * 60,
        'breakout_20d': [False] * 59 + [True],
        'breakdown_20d': [False] * 60
    })

    regime = MarketRegimeDetector.detect_regime(df_nifty, df_nifty, {"STOCK1": stock_df, "STOCK2": stock_df})
    assert regime["regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert regime["breadth_pct_above_50dma"] == 100.0

def test_sector_analyzer():
    dates = pd.date_range("2026-01-01", periods=30, freq="D").strftime("%Y-%m-%d")
    df_sec = pd.DataFrame({
        'date': dates,
        'close': [1000 + i * 5 for i in range(30)],
        'return_1d': [0.005] * 30,
        'volatility_20d': [0.15] * 30,
        'rsi_14': [65.0] * 30,
        'macd': [2.5] * 30
    })
    df_nifty = pd.DataFrame({
        'date': dates,
        'close': [20000 + i * 10 for i in range(30)],
        'return_1d': [0.001] * 30
    })

    sec_res = SectorAnalyzer.analyze_sectors({"NIFTY IT": df_sec}, df_nifty)
    assert len(sec_res) == 1
    assert sec_res[0]["sector"] == "NIFTY IT"
    assert sec_res[0]["rank"] == 1
