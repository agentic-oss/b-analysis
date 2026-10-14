import pytest
import pandas as pd
import numpy as np
from src.validation.validator import DataValidator
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.scoring.composite import CompositeScorer
from src.patterns.analogues import HistoricalAnalogueAnalyzer, FutureSignalEngine
from src.features.pipeline import FeaturePipeline
from src.modeling.predictor import PredictionModule
from src.backtesting.engine import BacktestEngine

@pytest.fixture
def sample_price_df():
    dates = pd.date_range("2024-01-01", periods=200)
    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "open": 100 + np.arange(200),
        "high": 105 + np.arange(200),
        "low": 95 + np.arange(200),
        "close": 102 + np.arange(200),
        "volume": 10000 + np.random.randint(0, 5000, 200)
    })

def test_data_validation(sample_price_df):
    validator = DataValidator()
    valid_df, warnings, errors = validator.validate_symbol_data(sample_price_df, "TEST")
    assert not valid_df.empty
    assert len(errors) == 0

def test_invalid_ohlc_validation():
    invalid_df = pd.DataFrame({
        "Date": ["2026-03-01"],
        "open": [100],
        "high": [90],  # high < low
        "low": [95],
        "close": [105], # close > high
        "volume": [1000]
    })
    validator = DataValidator()
    _, warnings, errors = validator.validate_symbol_data(invalid_df, "TEST")
    assert len(errors) > 0

def test_technical_indicators(sample_price_df):
    res = TechnicalIndicators.compute_all(sample_price_df)
    assert "sma_20" in res.columns
    assert "rsi_14" in res.columns
    assert "macd" in res.columns
    assert "atr_14" in res.columns
    assert "volatility_20d" in res.columns
    assert not res["sma_20"].isna().all()

def test_market_regime():
    nifty = pd.DataFrame({
        "close": [100], "sma_20": [98], "sma_50": [95], "sma_200": [90], "return_1d": [0.01]
    })
    analyzer = MarketRegimeAnalyzer()
    res = analyzer.analyze(nifty, pd.DataFrame(), {})
    assert res["regime"] in ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"]
    assert "score" in res

def test_sector_analyzer():
    sector_df = pd.DataFrame({"return_1d": [0.02], "return_5d": [0.05], "return_20d": [0.10]})
    nifty = pd.DataFrame({"return_1d": [0.01], "return_5d": [0.02], "return_20d": [0.05]})
    analyzer = SectorAnalyzer()
    res = analyzer.analyze_sectors({"NIFTY IT": sector_df}, nifty)
    assert len(res) == 1
    assert res[0]["sector"] == "NIFTY IT"
    assert res[0]["rank"] == 1

def test_composite_scoring(sample_price_df):
    ind_df = TechnicalIndicators.compute_all(sample_price_df)
    scorer = CompositeScorer()
    res = scorer.compute_stock_score(ind_df, market_regime_score=70.0)
    assert 0 <= res["composite_score"] <= 100
    assert res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]

def test_historical_analogues_and_signals(sample_price_df):
    ind_df = TechnicalIndicators.compute_all(sample_price_df)
    ha = HistoricalAnalogueAnalyzer()
    se = FutureSignalEngine()
    analogues = ha.find_analogues(ind_df)
    signals = se.generate_signals(analogues, composite_score=65.0)
    assert "num_observations" in analogues
    assert "20d" in signals

def test_feature_pipeline_look_ahead_prevention(sample_price_df):
    ind_df = TechnicalIndicators.compute_all(sample_price_df)
    fp = FeaturePipeline()
    fm = fp.build_feature_matrix({"TEST": ind_df})
    assert "future_return_1d" in fm.columns

    pit = fp.get_point_in_time_features(fm, sample_price_df.iloc[10]["Date"])
    # Point in time feature set MUST NOT contain target columns
    assert not any(col.startswith("future_return_") for col in pit.columns)

def test_prediction_module(sample_price_df):
    ind_df = TechnicalIndicators.compute_all(sample_price_df)
    fp = FeaturePipeline()
    fm = fp.build_feature_matrix({"TEST": ind_df})
    pm = PredictionModule()
    res = pm.train_and_evaluate(fm)
    assert res["status"] in ["success", "insufficient_data", "insufficient_out_of_sample_data"]

def test_backtest_engine(sample_price_df):
    ind_df = TechnicalIndicators.compute_all(sample_price_df)
    engine = BacktestEngine()
    res = engine.run_strategy(ind_df)
    assert res["status"] == "success"
    assert "cumulative_return_pct" in res
