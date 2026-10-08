import pytest
import pandas as pd
import numpy as np

from src.indicators.technical import TechnicalIndicators
from src.fundamentals.fundamental import FundamentalAnalysis
from src.market.market_sector import MarketRegime, SectorAnalysis


def test_technical_indicators_computation():
    dates = pd.date_range("2024-01-01", periods=100, freq="D").strftime("%Y-%m-%d").tolist()
    np.random.seed(42)
    close_prices = np.cumsum(np.random.randn(100)) + 100
    df = pd.DataFrame({
        "date": dates,
        "open": close_prices - 0.5,
        "high": close_prices + 1.0,
        "low": close_prices - 1.0,
        "close": close_prices,
        "volume": np.random.randint(1000, 5000, size=100)
    })

    df_ind = TechnicalIndicators.compute_all(df)
    assert "sma_20" in df_ind.columns
    assert "ema_50" in df_ind.columns
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "atr_14" in df_ind.columns
    assert "bollinger_upper" in df_ind.columns
    assert "obv" in df_ind.columns
    assert "golden_cross" in df_ind.columns


def test_fundamental_analysis_structure():
    f = FundamentalAnalysis.get_fundamentals("RELIANCE.NS")
    assert isinstance(f, dict)
    assert "symbol" in f
    assert "source" in f


def test_market_regime_and_sector_analysis():
    dates = pd.date_range("2024-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
    nifty_df = pd.DataFrame({
        "date": dates,
        "close": np.linspace(100, 150, 50),
        "sma_50": np.linspace(90, 140, 50),
        "sma_200": np.linspace(80, 130, 50)
    })
    stock_df = TechnicalIndicators.compute_all(pd.DataFrame({
        "date": dates,
        "open": np.linspace(10, 20, 50),
        "high": np.linspace(11, 21, 50),
        "low": np.linspace(9, 19, 50),
        "close": np.linspace(10, 20, 50),
        "volume": [100] * 50
    }))

    regime = MarketRegime.analyze_regime(nifty_df, nifty_df, {"RELIANCE": stock_df}, dates[-1])
    assert regime["classification"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert "breadth" in regime

    sectors = SectorAnalysis.analyze_sectors({"NIFTY IT": nifty_df}, nifty_df)
    assert len(sectors) == 1
    assert sectors[0]["sector"] == "NIFTY IT"
