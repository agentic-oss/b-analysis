import os
import json
import pytest
import pandas as pd
import numpy as np
from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.store import DataStore
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamental_analysis import FundamentalAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.patterns.historical_analogues import HistoricalAnalogueAnalyzer
from src.features.feature_builder import FeatureBuilder
from src.modeling.predictor import MarketPredictor
from src.backtesting.backtest import Backtester
from src.reporting.generator import DailyReportGenerator

@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": np.random.uniform(100, 110, 100),
        "high": np.random.uniform(110, 120, 100),
        "low": np.random.uniform(90, 100, 100),
        "close": np.random.uniform(100, 110, 100),
        "volume": np.random.randint(1000, 5000, 100)
    })
    df["high"] = df[["open", "close", "high"]].max(axis=1) + 1.0
    df["low"] = df[["open", "close", "low"]].min(axis=1) - 1.0
    return df

def test_data_validator(sample_ohlcv):
    validator = DataValidator()
    df_clean, report = validator.validate_ohlcv(sample_ohlcv, ticker="TEST")
    assert not df_clean.empty
    assert report["records_processed"] == 100
    assert report["records_valid"] == 100

def test_technical_indicators(sample_ohlcv):
    df_calc = TechnicalIndicators.compute_all(sample_ohlcv)
    assert "sma_20" in df_calc.columns
    assert "rsi_14" in df_calc.columns
    assert "macd" in df_calc.columns
    assert "atr_14" in df_calc.columns

    signals = TechnicalIndicators.detect_signals(df_calc)
    assert isinstance(signals, dict)
    assert "breakout" in signals

def test_market_regime(sample_ohlcv):
    nifty_df = TechnicalIndicators.compute_all(sample_ohlcv)
    stock_dfs = {"TEST1": nifty_df, "TEST2": nifty_df}
    regime = MarketRegimeAnalyzer.analyze_regime(nifty_df, nifty_df, stock_dfs)
    assert "regime" in regime
    assert "score" in regime

def test_stock_scorer(sample_ohlcv):
    df_calc = TechnicalIndicators.compute_all(sample_ohlcv)
    res = StockScorer.calculate_score(df_calc)
    assert 0 <= res["composite_score"] <= 100
    assert res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]

def test_feature_builder_no_leakage(sample_ohlcv):
    df_calc = TechnicalIndicators.compute_all(sample_ohlcv)
    feat_df = FeatureBuilder.build_features(df_calc, ticker="TEST")
    assert "future_return_1d" in feat_df.columns
    assert "rsi_14" in feat_df.columns
    # Verify future targets are NA at the very tail end (future unavailable)
    assert pd.isna(feat_df.iloc[-1]["future_return_1d"])

def test_historical_analogues(sample_ohlcv):
    df_calc = TechnicalIndicators.compute_all(sample_ohlcv)
    analogues = HistoricalAnalogueAnalyzer.find_analogues(df_calc)
    assert "observations" in analogues
    assert "forward_stats" in analogues

def test_backtesting(sample_ohlcv):
    df_calc = TechnicalIndicators.compute_all(sample_ohlcv)
    backtester = Backtester()
    res = backtester.run_sma_crossover_strategy(df_calc)
    assert "total_return_pct" in res
    assert "max_drawdown_pct" in res

def test_report_generator():
    data = {
        "market": {"regime": "Bullish", "score": 75},
        "sectors": [{"rank": 1, "sector": "IT", "daily_return": 1.5, "weekly_return": 2.0, "relative_strength": 0.5, "momentum_score": 80}],
        "stocks": [{"symbol": "TEST", "composite_score": 82, "score_label": "Very Strong", "signals": {}, "score_components": {}}],
        "data_quality": {"records_processed": 100, "records_valid": 100}
    }
    report = DailyReportGenerator.generate_markdown_report("2026-09-30", data)
    assert "# Daily Indian Stock Market Deep Analysis" in report
    assert "Bullish" in report
