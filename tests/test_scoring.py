import pandas as pd
import pytest
from src.fundamentals.fundamental_analysis import FundamentalAnalyzer
from src.scoring.composite_score import CompositeScorer

def test_fundamental_analysis_evaluation():
    sample_data = {
        "symbol": "RELIANCE",
        "pe_ratio": 22.5,
        "pb_ratio": 2.1,
        "roe": 0.18,
        "profit_margins": 0.12,
        "revenue_growth": 0.10,
        "debt_to_equity": 45.0,
        "provider": "yfinance"
    }

    result = FundamentalAnalyzer.evaluate_fundamentals(sample_data)
    assert result['available'] is True
    assert result['fundamental_score'] > 50.0
    assert result['label'] in ["Strong", "Very Strong"]

def test_composite_scorer():
    dates = pd.date_range('2025-01-01', periods=10).strftime('%Y-%m-%d')
    df_stock = pd.DataFrame({
        'date': dates,
        'symbol': ['TCS'] * 10,
        'close': [3500 + i*10 for i in range(10)],
        'sma_20': [3400] * 10,
        'sma_50': [3300] * 10,
        'sma_200': [3000] * 10,
        'ema_20': [3450] * 10,
        'rsi_14': [65.0] * 10,
        'macd': [15.0] * 10,
        'macd_signal': [10.0] * 10,
        'roc_10': [5.0] * 10,
        'relative_volume': [1.5] * 10,
        'dist_52w_high': [-0.02] * 10,
        'return_1d': [0.01] * 10,
        'volatility_20d': [0.18] * 10
    })

    market_info = {"market_regime": "Bullish", "nifty_volatility_20d": 0.14}
    fund_info = {"fundamental_score": 75.0}

    score_res = CompositeScorer.calculate_stock_score(df_stock, market_info, None, fund_info)
    assert score_res['symbol'] == 'TCS'
    assert score_res['total_score'] >= 65.0
    assert score_res['label'] in ['Strong', 'Very Strong']
    assert 'technical_trend' in score_res['components']
