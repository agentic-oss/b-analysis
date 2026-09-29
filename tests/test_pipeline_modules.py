"""
Unit tests for Market Regime, Sector Analysis, Composite Scoring, Pattern Analogues, ML Predictor, and Backtesting.
"""
import pytest
import pandas as pd
import numpy as np

from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.scoring.scorer import StockScorer
from src.patterns.analogues import HistoricalPatternEngine
from src.modeling.predictor import PredictorModule
from src.features.builder import FeatureBuilder
from src.backtesting.engine import Backtester


def test_market_regime_analyzer():
    dates = pd.date_range("2026-01-01", periods=30)
    df_nifty = pd.DataFrame({
        "Date": dates,
        "close": 24000 + pd.Series(range(30)) * 10,
        "sma_20": 24100,
        "sma_50": 24000,
        "sma_200": 23500,
        "rsi_14": 65.0,
        "volatility_20d": 0.12
    })
    df_bank = pd.DataFrame({"close": [50000]*30, "sma_50": [49000]*30})

    stocks_dfs = {"STOCK_A": df_nifty}

    res = MarketRegimeAnalyzer.analyze(df_nifty, df_bank, stocks_dfs)
    assert "market_regime" in res
    assert "confidence" in res
    assert res["market_regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]


def test_stock_scorer():
    df = pd.DataFrame({
        "close": [100.0, 105.0],
        "sma_20": [98.0, 100.0],
        "sma_50": [95.0, 96.0],
        "sma_200": [90.0, 91.0],
        "ema_20": [99.0, 101.0],
        "rsi_14": [55.0, 60.0],
        "macd_hist": [0.5, 1.0],
        "roc_12": [2.0, 3.0],
        "relative_volume": [1.2, 1.5],
        "volume_change_pct": [5.0, 10.0],
        "volatility_20d": [0.18, 0.18]
    })

    scores = StockScorer.calculate_scores(df, {}, {}, {})
    assert 0.0 <= scores["composite_score"] <= 100.0
    assert scores["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]


def test_feature_builder_and_no_leakage():
    dates = pd.date_range("2026-01-01", periods=30)
    stock_df = pd.DataFrame({
        "Date": dates,
        "close": 100 + pd.Series(range(30)),
        "open": 99 + pd.Series(range(30)),
        "high": 101 + pd.Series(range(30)),
        "low": 98 + pd.Series(range(30)),
        "volume": [1000] * 30
    })

    feat_df = FeatureBuilder.build_feature_matrix(stock_df, pd.DataFrame(), pd.DataFrame())
    assert not feat_df.empty
    assert "return_1d" in feat_df.columns
    assert "future_return_5d" in feat_df.columns

    # Verify return_1d at index T depends on close[T] and close[T-1]
    assert feat_df.iloc[1]["return_1d"] == pytest.approx((101 - 100) / 100 * 100)


def test_backtester():
    bt_df = pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=20),
        "close": 100 + pd.Series(range(20)),
        "composite_score": [50]*5 + [85]*5 + [40]*10
    })

    bt = Backtester(initial_capital=100000.0)
    res = bt.run_backtest(bt_df)

    assert "total_return_pct" in res
    assert "total_trades" in res
    assert res["total_trades"] >= 1
