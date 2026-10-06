import pytest
import pandas as pd
import numpy as np
from src.scoring.composite import StockScorer
from src.patterns.analogue import PatternAnalogueFinder
from src.modeling.signals import ProbabilisticSignalGenerator

def test_stock_scorer():
    dates = pd.date_range('2025-01-01', periods=30)
    stock_df = pd.DataFrame({
        'date': dates,
        'close': np.linspace(100, 120, 30),
        'sma_20': np.linspace(95, 115, 30),
        'sma_50': np.linspace(90, 110, 30),
        'sma_200': np.linspace(80, 100, 30),
        'rsi_14': [60]*30,
        'macd_hist': [1.5]*30,
        'relative_volume': [1.5]*30,
        'volatility_regime': ['Normal']*30
    })
    nifty_df = pd.DataFrame({'date': dates, 'close': np.linspace(20000, 20500, 30)})

    scorer = StockScorer()
    res = scorer.calculate_stock_score(stock_df, nifty_df, {'regime': 'Bullish'}, {'score': 70})

    assert 0 <= res['composite_score'] <= 100
    assert res['label'] in ['Very Strong', 'Strong', 'Neutral', 'Weak', 'Very Weak']
    assert 'components' in res

def test_pattern_analogue_finder():
    dates = pd.date_range('2024-01-01', periods=120)
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(120))
    df = pd.DataFrame({
        'date': dates,
        'close': closes,
        'rsi_14': np.random.uniform(30, 70, 120),
        'dist_sma_20': np.random.uniform(-0.05, 0.05, 120),
        'relative_volume': np.random.uniform(0.8, 2.0, 120),
        'volatility_20d': [0.15]*120
    })

    finder = PatternAnalogueFinder(top_k=10)
    analogues = finder.find_analogues(df)

    assert analogues['observations'] > 0
    assert '5d' in analogues['horizons']
    assert 'win_rate' in analogues['horizons']['5d']

def test_probabilistic_signal_generator():
    generator = ProbabilisticSignalGenerator()
    analogue_stats = {
        "observations": 20,
        "horizons": {
            "1d": {"win_rate": 0.65, "avg_return": 0.5},
            "5d": {"win_rate": 0.70, "avg_return": 1.2}
        }
    }
    signals = generator.generate_signals(composite_score=75, analogue_stats=analogue_stats)
    assert 'forward_horizons' in signals
    assert signals['forward_horizons']['5d']['directional_bias'] in ['Bullish', 'Slightly Bullish']
    assert signals['forward_horizons']['5d']['confidence'] > 50
    assert 'DISCLAIMER' in signals['disclaimer']
