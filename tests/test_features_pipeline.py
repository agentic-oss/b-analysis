import os
import shutil
import tempfile
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from src.features.builder import FeatureBuilder
from src.modeling.baseline import BaselineMLModels
from src.backtesting.engine import SimpleBacktester
from src.reporting.generator import ReportGenerator
from src.pipeline.daily_pipeline import DailyPipeline


def test_feature_builder_lookahead_bias_prevention():
    dates = pd.date_range('2025-01-01', periods=30)
    stock_df = pd.DataFrame({
        'date': dates,
        'open': np.linspace(100, 130, 30),
        'high': np.linspace(105, 135, 30),
        'low': np.linspace(95, 125, 30),
        'close': np.linspace(102, 132, 30),
        'volume': [1000]*30,
        'rsi_14': [55]*30
    })
    nifty_df = pd.DataFrame({'date': dates, 'close': np.linspace(20000, 21000, 30)})

    features = FeatureBuilder.build_stock_features('RELIANCE', stock_df, nifty_df)

    assert not features.empty
    assert 'future_return_5d' in features.columns
    # Check that feature_return_5d at row 0 equals return from close[0] to close[5]
    expected_ret_5d = (stock_df['close'].iloc[5] - stock_df['close'].iloc[0]) / stock_df['close'].iloc[0]
    assert np.isclose(features['future_return_5d'].iloc[0], expected_ret_5d)


def test_baseline_ml_models_walk_forward():
    np.random.seed(42)
    n = 150
    df = pd.DataFrame({
        'feature_1': np.random.randn(n),
        'feature_2': np.random.randn(n),
        'future_return_5d': np.random.randn(n)
    })

    model = BaselineMLModels(model_type='random_forest')
    metrics = model.train_walk_forward(df, feature_cols=['feature_1', 'feature_2'], min_train_size=100, test_size=20)

    assert 'accuracy' in metrics
    assert metrics['samples_evaluated'] > 0


def test_simple_backtester():
    dates = pd.date_range('2025-01-01', periods=50)
    price_df = pd.DataFrame({'date': dates, 'close': np.linspace(100, 150, 50)})
    signals = pd.Series([1 if i % 10 < 5 else 0 for i in range(50)])

    backtester = SimpleBacktester(initial_capital=100000.0)
    res = backtester.run_backtest(price_df, signals)

    assert res['initial_capital'] == 100000.0
    assert 'cumulative_return_pct' in res
    assert 'sharpe_ratio' in res


def test_report_generator():
    market = {'regime': 'Bullish', 'regime_score': 30, 'nifty_close': 22000, 'breadth': {}}
    sectors = [{'rank': 1, 'sector': 'NIFTY IT', 'daily_return': 1.5, 'weekly_return': 3.0, 'momentum_score': 80}]
    stocks = [{
        'symbol': 'RELIANCE',
        'composite_score': 82,
        'score_label': 'Very Strong',
        'technical_score': 85,
        'fundamental_score': 70,
        'signals': {'events': ['Bullish Breakout']},
        'forward_probabilities': {'forward_horizons': {'5d': {'directional_bias': 'Bullish', 'confidence': 75, 'historical_win_rate': 0.7, 'expected_return_pct': 1.5}}}
    }]
    quality = {'records_processed': 1, 'records_valid': 1, 'warnings': [], 'errors': []}

    daily_json = ReportGenerator.generate_daily_json('2025-01-03', market, sectors, stocks)
    assert daily_json['date'] == '2025-01-03'

    daily_md = ReportGenerator.generate_daily_markdown('2025-01-03', market, sectors, stocks, quality)
    assert '# Daily Indian Stock Market Analysis' in daily_md
