"""
Automated Pytest Unit and Integration Suite for Daily Market Analysis Pipeline.
"""

import os
import json
import pytest
import pandas as pd
import numpy as np

from src.ingestion.provider import YFinanceProvider
from src.validation.data_validator import DataValidator
from src.storage.storage_manager import StorageManager
from src.indicators.technical import TechnicalAnalyzer
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.patterns.analogue_finder import HistoricalAnalogueFinder
from src.features.feature_builder import FeatureBuilder
from src.modeling.predictor import DirectionalPredictor
from src.backtesting.backtester import BacktestingEngine
from src.reporting.report_generator import ReportGenerator


@pytest.fixture
def sample_ohlcv_df():
    dates = pd.date_range("2024-01-01", periods=120)
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(120))
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": close_prices - 0.5,
        "high": close_prices + 1.0,
        "low": close_prices - 1.0,
        "close": close_prices,
        "volume": np.random.randint(5000, 20000, size=120)
    })
    return df


def test_data_validator_duplicate_and_ohlc(sample_ohlcv_df):
    validator = DataValidator()
    # Introduce duplicate row
    dup_df = pd.concat([sample_ohlcv_df, sample_ohlcv_df.iloc[-1:]], ignore_index=True)
    valid_df, warnings, errors = validator.validate_df(dup_df, "TEST.NS")
    assert len(valid_df) == len(sample_ohlcv_df)
    assert any("duplicate" in w["type"] for w in warnings)


def test_technical_analyzer_indicators(sample_ohlcv_df):
    ind_df = TechnicalAnalyzer.calculate_indicators(sample_ohlcv_df)
    assert "rsi_14" in ind_df.columns
    assert "macd" in ind_df.columns
    assert "volatility_20d" in ind_df.columns
    assert "sma_20" in ind_df.columns

    signals = TechnicalAnalyzer.identify_signals(ind_df)
    assert "support_resistance" in signals


def test_no_look_ahead_leakage(sample_ohlcv_df):
    ind_df = TechnicalAnalyzer.calculate_indicators(sample_ohlcv_df)
    feat_df = FeatureBuilder.build_feature_set(ind_df, "TEST.NS")

    # Verify features on date T do not use future close prices
    # Close price on T is feature 'close', while 'future_return_1d' is derived from T+1
    row_t = feat_df.iloc[10]
    next_close = feat_df.iloc[11]["close"]
    expected_fwd_ret = (next_close - row_t["close"]) / row_t["close"]
    assert np.isclose(row_t["future_return_1d"], expected_fwd_ret)


def test_stock_scorer(sample_ohlcv_df):
    ind_df = TechnicalAnalyzer.calculate_indicators(sample_ohlcv_df)
    score_dict = StockScorer.score_stock(ind_df, market_regime_score=30)
    assert 0 <= score_dict["composite_score"] <= 100
    assert score_dict["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]


def test_pattern_analogues(sample_ohlcv_df):
    ind_df = TechnicalAnalyzer.calculate_indicators(sample_ohlcv_df)
    analogues = HistoricalAnalogueFinder.find_analogues(ind_df)
    assert "observations_count" in analogues
    assert "horizons" in analogues


def test_backtester(sample_ohlcv_df):
    ind_df = TechnicalAnalyzer.calculate_indicators(sample_ohlcv_df)
    bt = BacktestingEngine()
    res = bt.run_sma_crossover_backtest(ind_df)
    assert "total_return_pct" in res
    assert "max_drawdown_pct" in res
    assert "sharpe_ratio" in res


def test_report_generator():
    market = {"regime": "Bullish", "confidence": 75, "breadth": {"advances": 10, "declines": 5}}
    sectors = [{"rank": 1, "sector": "IT", "daily_return_pct": 1.2, "relative_strength_1d": 0.5, "momentum_score": 15}]
    stocks = [{"symbol": "TCS", "score": {"composite_score": 82, "label": "Very Strong"}, "market_regime": "Bullish"}]
    quality = {"records_processed": 10, "records_valid": 10, "warnings_count": 0, "errors_count": 0}

    json_out = ReportGenerator.generate_json_output("2025-01-10", market, sectors, stocks, quality)
    assert json_out["date"] == "2025-01-10"
    assert len(json_out["stocks"]) == 1

    md_out = ReportGenerator.generate_markdown_report("2025-01-10", market, sectors, stocks, quality)
    assert "# Daily Indian Stock Market Deep Analysis Report" in md_out
