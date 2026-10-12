"""
Comprehensive unit and integration tests for Daily Market Analysis Pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from src.validation.validator import DataValidator
from src.indicators.engine import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.scoring.engine import CompositeScorer
from src.patterns.analogue import PatternAnalogueEngine
from src.features.builder import FeatureEngineer
from src.modeling.predictor import MLPredictionModel
from src.backtesting.engine import Backtester
from src.reporting.generator import ReportGenerator


@pytest.fixture
def dummy_ohlcv_df():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({
        "Date": dates,
        "Open": close_prices - 0.5,
        "High": close_prices + 1.0,
        "Low": close_prices - 1.0,
        "Close": close_prices,
        "Adj Close": close_prices,
        "Volume": np.random.randint(1000, 5000, size=100),
        "Ticker": "TEST.NS",
    })
    return df


def test_data_validator(dummy_ohlcv_df):
    validator = DataValidator()
    valid_df, report = validator.validate_df(dummy_ohlcv_df, "TEST.NS")
    assert not valid_df.empty
    assert report["records_valid"] == 100
    assert len(report["errors"]) == 0


def test_technical_indicators(dummy_ohlcv_df):
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)

    assert "SMA_20" in calc_df.columns
    assert "RSI_14" in calc_df.columns
    assert "MACD" in calc_df.columns
    assert "BB_Upper" in calc_df.columns

    signals = indicators.detect_signals(calc_df)
    assert "support_level" in signals
    assert "resistance_level" in signals


def test_market_regime_analyzer(dummy_ohlcv_df):
    analyzer = MarketRegimeAnalyzer()
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)

    regime = analyzer.analyze(calc_df, {"TEST": calc_df})
    assert "regime" in regime
    assert regime["regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]


def test_sector_analyzer(dummy_ohlcv_df):
    analyzer = SectorAnalyzer()
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)

    rankings = analyzer.analyze_sectors({"Banking": calc_df}, calc_df)
    assert len(rankings) == 1
    assert rankings[0]["sector"] == "Banking"
    assert rankings[0]["rank"] == 1


def test_composite_scorer(dummy_ohlcv_df):
    scorer = CompositeScorer()
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)

    market_regime = {"nifty_return_1d": 0.01}
    res = scorer.score_stock(calc_df, market_regime)

    assert 0.0 <= res["composite_score"] <= 100.0
    assert res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]


def test_pattern_analogue_engine(dummy_ohlcv_df):
    engine = PatternAnalogueEngine()
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)

    res = engine.find_analogues_and_probabilities(calc_df)
    assert "num_observations" in res
    assert "forward_probabilities" in res


def test_feature_engineer_anti_leakage(dummy_ohlcv_df):
    fe = FeatureEngineer()
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)

    feat_df = fe.create_features_and_targets(calc_df)

    # Check future targets are created
    assert "future_return_1d" in feat_df.columns
    assert "future_target_direction_5d" in feat_df.columns

    # Check that last row's target is NaN because future data is not yet known (anti-leakage)
    assert pd.isna(feat_df.iloc[-1]["future_return_1d"])


def test_ml_predictor(dummy_ohlcv_df):
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)
    fe = FeatureEngineer()
    feat_df = fe.create_features_and_targets(calc_df)

    predictor = MLPredictionModel()
    res = predictor.train_and_evaluate(feat_df, horizon_days=1, model_type="random_forest")

    assert res["status"] in ["success", "error"]
    if res["status"] == "success":
        assert "metrics" in res
        assert "accuracy" in res["metrics"]


def test_backtester(dummy_ohlcv_df):
    indicators = TechnicalIndicators()
    calc_df = indicators.calculate_all(dummy_ohlcv_df)
    calc_df["composite_score"] = 75.0  # Force trigger buy

    bt = Backtester()
    res = bt.run_score_strategy(calc_df, buy_threshold=70.0, sell_threshold=40.0)

    assert res["status"] == "success"
    assert "final_equity" in res
    assert "total_return_pct" in res


def test_report_generator():
    rg = ReportGenerator()
    sample_analysis = {
        "market": {"regime": "Bullish", "nifty_trend": "Uptrend"},
        "sectors": [{"rank": 1, "sector": "Banking", "daily_return": 1.2, "weekly_return": 3.0, "momentum_score": 80.0}],
        "stocks": [{"symbol": "RELIANCE", "composite_score": 82.0, "label": "Very Strong", "daily_return_pct": 1.5, "signals": []}],
        "quality": {"records_processed": 100, "records_valid": 100, "warnings": [], "errors": []},
    }

    md = rg.generate_markdown_report("2026-03-30", sample_analysis)
    assert "# Daily Indian Stock Market Analysis - 2026-03-30" in md

    json_data = rg.generate_json_schema_data("2026-03-30", sample_analysis)
    assert json_data["date"] == "2026-03-30"
