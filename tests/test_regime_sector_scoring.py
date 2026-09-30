import pytest
import pandas as pd
import numpy as np
from src.market.market_regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.fundamentals.fundamental_analyzer import FundamentalAnalyzer

def test_market_regime_analyzer():
    analyzer = MarketRegimeAnalyzer()
    dates = pd.date_range(start="2024-01-01", periods=100, freq="B")
    nifty_df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'close': np.linspace(20000, 22000, 100),
        'sma_20': np.linspace(19800, 21800, 100),
        'sma_50': np.linspace(19500, 21500, 100),
        'sma_200': np.linspace(18000, 20000, 100),
        'daily_return': 0.001,
        'volatility_20d': 0.12
    })

    bank_df = nifty_df.copy()
    stock_df = nifty_df.copy()
    stock_df['dist_52w_high'] = -0.01
    stock_df['dist_52w_low'] = 0.50

    res = analyzer.analyze_market_regime(nifty_df, bank_df, {"RELIANCE": stock_df})
    assert res['regime'] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert res['market_breadth']['total_tracked'] == 1

def test_stock_scorer():
    scorer = StockScorer()
    dates = pd.date_range(start="2024-01-01", periods=50, freq="B")
    df = pd.DataFrame({
        'close': np.linspace(100, 150, 50),
        'sma_20': np.linspace(98, 148, 50),
        'sma_50': np.linspace(95, 145, 50),
        'sma_200': np.linspace(80, 130, 50),
        'rsi_14': 60.0,
        'macd_histogram': 1.5,
        'daily_return': 0.01,
        'relative_volume': 1.5,
        'volatility_20d': 0.18
    })

    score_res = scorer.score_stock(df, market_regime_score=80.0)
    assert 0 <= score_res['composite_score'] <= 100
    assert score_res['label'] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]
