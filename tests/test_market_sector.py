import pandas as pd
import numpy as np
import pytest
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer

def create_sample_df(symbol, fill_val=100.0, trend=0.01):
    dates = pd.date_range('2025-01-01', periods=60).strftime('%Y-%m-%d')
    closes = [fill_val * ((1 + trend) ** i) for i in range(60)]
    df = pd.DataFrame({
        'date': dates,
        'symbol': [symbol] * 60,
        'open': closes,
        'high': [c * 1.01 for c in closes],
        'low': [c * 0.99 for c in closes],
        'close': closes,
        'volume': [100000] * 60,
        'sma_20': closes,
        'sma_50': [c * 0.98 for c in closes],
        'sma_200': [c * 0.90 for c in closes],
        'volatility_20d': [0.15] * 60,
        'return_1d': [trend] * 60,
        'relative_volume': [1.0] * 60,
        'rsi_14': [60.0] * 60
    })
    return df

def test_market_regime_analysis():
    nifty_df = create_sample_df('^NSEI', 18000, 0.002)
    bank_df = create_sample_df('^NSEBANK', 42000, 0.002)
    stocks = [create_sample_df(f'STK_{i}', 500, 0.001) for i in range(10)]

    res = MarketRegimeAnalyzer.analyze_regime(nifty_df, bank_df, stocks)
    assert res['market_regime'] in ['Strong Bullish', 'Bullish', 'Neutral', 'Bearish', 'Strong Bearish']
    assert res['breadth']['total_tracked'] == 10
    assert res['breadth']['pct_above_20dma'] == 100.0

def test_sector_analysis():
    nifty_df = create_sample_df('^NSEI', 18000, 0.002)
    sector_dfs = {
        'NIFTY IT': create_sample_df('^CNXIT', 30000, 0.005),
        'NIFTY AUTO': create_sample_df('^CNXAUTO', 12000, -0.002)
    }

    sectors = SectorAnalyzer.analyze_sectors(sector_dfs, nifty_df)
    assert len(sectors) == 2
    assert sectors[0]['rank'] == 1
    assert sectors[0]['sector'] == 'NIFTY IT'
    assert sectors[1]['rank'] == 2
