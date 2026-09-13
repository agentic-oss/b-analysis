import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from src.modeling.baselines import PredictionResearchLayer
from src.backtesting.backtest import Backtester
from src.reporting.report import DailyReportGenerator

def test_prediction_research_layer():
    # Synthetic feature dataset
    dates = pd.date_range("2025-01-01", periods=100, freq="D").strftime("%Y-%m-%d")
    np.random.seed(42)
    df_feat = pd.DataFrame({
        'date': dates,
        'ticker': ['RELIANCE'] * 100,
        'open': [100.0] * 100,
        'high': [105.0] * 100,
        'low': [95.0] * 100,
        'close': [102.0 + np.random.randn() for _ in range(100)],
        'volume': [1000] * 100,
        'rsi_14': np.random.uniform(30, 70, 100),
        'target_direction_5d': np.random.choice([0, 1], size=100)
    })

    res = PredictionResearchLayer.train_evaluate_walk_forward(df_feat, target_col='target_direction_5d', n_splits=2)
    assert "accuracy" in res
    assert "model" in res

def test_backtesting_framework():
    dates = pd.date_range("2025-01-01", periods=50, freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        'date': dates,
        'open': [100.0 + i for i in range(50)],
        'close': [101.0 + i for i in range(50)],
        'breakout_20d': [False] * 10 + [True] + [False] * 39
    })

    backtester = Backtester(initial_capital=100000.0)
    res = backtester.run_backtest(df, signal_col='breakout_20d', holding_period=5)
    assert res["initial_capital"] == 100000.0
    assert "total_return_pct" in res
    assert "sharpe_ratio" in res

def test_daily_report_generator():
    analysis_data = {
        "date": "2026-01-02",
        "market": {
            "regime": "Bullish",
            "nifty_close": 24000.0,
            "nifty_return_1d": 0.005,
            "nifty_trend": "Bullish",
            "banknifty_trend": "Bullish",
            "advance_decline_ratio": 1.5,
            "advances": 15,
            "declines": 10,
            "breadth_pct_above_50dma": 65.0,
            "explanation": "Test market explanation"
        },
        "sectors": [
            {"rank": 1, "sector": "NIFTY IT", "daily_return": 1.2, "weekly_return": 3.4, "relative_strength": 0.7, "momentum_score": 75.0}
        ],
        "stocks": [
            {
                "symbol": "RELIANCE.NS",
                "composite_score": 82.5,
                "label": "Very Strong",
                "relative_volume": 1.5,
                "score_components": {"technical_trend": 80.0, "momentum": 85.0},
                "breakout_20d": True,
                "breakdown_20d": False,
                "historical_analogues": {"observations_count": 12},
                "signals": {
                    "5d": {"directional_bias": "Bullish", "confidence_score": 78.0, "historical_win_rate_pct": 70.0}
                }
            }
        ],
        "quality": {
            "records_processed": 14,
            "records_valid": 14,
            "warnings": [],
            "errors": []
        }
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, "2026-01-02.md")
        content = DailyReportGenerator.generate_markdown(analysis_data, out_path)
        assert os.path.exists(out_path)
        assert "# Daily Indian Stock Market Research & Analysis Report" in content
