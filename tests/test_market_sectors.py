import pytest
import pandas as pd
import numpy as np
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer

def test_market_regime_analyzer():
    dates = pd.date_range('2025-01-01', periods=60)
    nifty_df = pd.DataFrame({
        'date': dates,
        'close': np.linspace(20000, 22000, 60),
        'sma_20': np.linspace(19800, 21800, 60),
        'sma_50': np.linspace(19500, 21500, 60),
        'sma_200': np.linspace(19000, 21000, 60),
        'volatility_20d': [0.12]*60
    })

    stock_df = pd.DataFrame({
        'date': dates,
        'high': np.linspace(100, 150, 60),
        'low': np.linspace(90, 140, 60),
        'close': np.linspace(95, 145, 60),
        'sma_20': np.linspace(90, 140, 60),
        'sma_50': np.linspace(85, 135, 60),
        'sma_200': np.linspace(80, 130, 60)
    })

    analyzer = MarketRegimeAnalyzer()
    res = analyzer.analyze_regime(nifty_df, stocks_dfs={'RELIANCE': stock_df})

    assert 'regime' in res
    assert res['regime'] in ['Strong Bullish', 'Bullish', 'Neutral', 'Bearish', 'Strong Bearish']
    assert res['breadth']['pct_above_50dma'] == 100.0

def test_sector_analyzer():
    dates = pd.date_range('2025-01-01', periods=30)
    nifty = pd.DataFrame({'date': dates, 'close': np.linspace(20000, 21000, 30)})
    it_df = pd.DataFrame({'date': dates, 'close': np.linspace(35000, 38000, 30)}) # Outperforming Nifty
    bank_df = pd.DataFrame({'date': dates, 'close': np.linspace(45000, 45500, 30)}) # Underperforming Nifty

    sa = SectorAnalyzer()
    sectors = sa.analyze_sectors({'NIFTY IT': it_df, 'NIFTY BANK': bank_df}, nifty)

    assert len(sectors) == 2
    assert sectors[0]['sector'] == 'NIFTY IT' # Highest momentum
    assert sectors[0]['rank'] == 1

def test_fundamental_analyzer():
    data = {
        "pe_ratio": 18.5,
        "roe": 0.22,
        "revenue_growth": 0.18,
        "debt_to_equity": 20.0
    }
    res = FundamentalAnalyzer.analyze_fundamentals(data)
    assert res['available'] is True
    assert res['score'] >= 70
