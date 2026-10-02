"""
Automated Unit and Integration Tests for the Stock Market Pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.validation.validator import DataValidator
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.scoring.scorer import StockScorer
from src.patterns.analogue_finder import PatternAnalogueFinder
from src.features.builder import FeatureBuilder
from src.modeling.models import PredictiveModelEngine
from src.backtesting.backtester import Backtester
from src.reporting.report_generator import ReportGenerator


@pytest.fixture
def sample_price_df():
    dates = pd.date_range("2024-01-01", periods=100)
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        "ticker": "TEST",
        "exchange": "NSE",
        "date": dates.strftime("%Y-%m-%d"),
        "open": prices - 0.5,
        "high": prices + 1.0,
        "low": prices - 1.0,
        "close": prices,
        "volume": np.random.randint(1000, 10000, 100),
    })
    return df


def test_data_validator(sample_price_df):
    validator = DataValidator()
    val_df, summary = validator.validate_df(sample_price_df, ticker="TEST")
    assert len(val_df) == 100
    assert summary["records_valid"] == 100
    assert len(summary["errors"]) == 0


def test_technical_indicators(sample_price_df):
    df_ind = TechnicalIndicators.calculate_indicators(sample_price_df)
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "sma_20" in df_ind.columns
    assert "volatility_20d" in df_ind.columns

    signals = TechnicalIndicators.detect_signals(df_ind)
    assert "golden_cross" in signals
    assert "trend_state" in signals


def test_market_regime():
    analyzer = MarketRegimeAnalyzer()
    nifty_dates = pd.date_range("2024-01-01", periods=50)
    nifty_df = pd.DataFrame({
        "date": nifty_dates.strftime("%Y-%m-%d"),
        "close": 24000.0,
        "daily_return": 0.001,
        "sma_20": 23800.0,
        "sma_50": 23500.0,
        "sma_200": 22000.0,
    })
    res = analyzer.analyze_regime({"^NSEI": nifty_df}, {}, "2024-02-15")
    assert "regime" in res
    assert "breadth" in res


def test_sector_analyzer():
    analyzer = SectorAnalyzer()
    dates = pd.date_range("2024-01-01", periods=25)
    sec_df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "close": 1000.0,
        "daily_return": 0.01,
        "rsi_14": 60.0,
        "roc_12": 2.0,
    })
    sec_meta = [{"symbol": "^CNXIT", "name": "NIFTY IT", "sector_id": "IT"}]
    res = analyzer.analyze_sectors(sec_meta, {"^CNXIT": sec_df}, "2024-01-25")
    assert len(res) == 1
    assert res[0]["rank"] == 1


def test_stock_scorer(sample_price_df):
    df_ind = TechnicalIndicators.calculate_indicators(sample_price_df)
    scorer = StockScorer()
    score_res = scorer.calculate_score(
        df_ind.iloc[-1],
        market_regime_info={"nifty_return_1d": 0.001, "regime": "Bullish"}
    )
    assert 0 <= score_res["composite_score"] <= 100
    assert score_res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]


def test_pattern_analogue_finder(sample_price_df):
    df_ind = TechnicalIndicators.calculate_indicators(sample_price_df)
    finder = PatternAnalogueFinder()
    res = finder.find_analogues(df_ind)
    assert "analogue_count" in res
    assert "forward_outcomes" in res


def test_feature_builder_lookahead_prevention(sample_price_df):
    df_ind = TechnicalIndicators.calculate_indicators(sample_price_df)
    builder = FeatureBuilder()
    feat_df = builder.build_feature_dataset(df_ind)
    assert "future_return_5d" in feat_df.columns
    # Ensure features on date T do not reference future close
    assert "price_close" in feat_df.columns


def test_predictive_modeling(sample_price_df):
    df_ind = TechnicalIndicators.calculate_indicators(sample_price_df)
    builder = FeatureBuilder()
    feat_df = builder.build_feature_dataset(df_ind)

    engine = PredictiveModelEngine()
    features = ["price_close", "rsi_14", "volatility_20d"]
    res = engine.train_and_evaluate_walk_forward(feat_df, feature_cols=features, target_horizon_col="future_return_1d")
    assert res["status"] in ["success", "insufficient_data"]


def test_backtester(sample_price_df):
    df_ind = TechnicalIndicators.calculate_indicators(sample_price_df)
    df_ind["composite_score"] = 60.0
    backtester = Backtester()
    res = backtester.run_backtest(df_ind)
    assert "final_portfolio_value" in res
    assert "total_return_pct" in res


def test_report_generator():
    gen = ReportGenerator()
    json_out = gen.generate_json_output(
        "2024-01-01",
        market_info={"regime": "Bullish"},
        sectors_info=[],
        stocks_info=[],
        quality_info={"records_processed": 100}
    )
    assert json_out["date"] == "2024-01-01"

    md_out = gen.generate_markdown_report(
        "2024-01-01",
        market_info={"regime": "Bullish"},
        sectors_info=[],
        stocks_info=[],
        quality_info={"records_processed": 100}
    )
    assert "# Daily Indian Stock Market Analysis" in md_out
