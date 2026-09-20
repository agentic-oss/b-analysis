import pytest
import pandas as pd
from src.ingestion.mock_provider import MockMarketDataProvider
from src.indicators.technical import TechnicalIndicators
from src.features.engineer import FeatureEngineer
from src.scoring.scorer import StockScorer
from src.patterns.analogues import HistoricalAnalogueAnalyzer
from src.modeling.predictor import PredictionModule
from src.backtesting.engine import BacktestEngine

def test_feature_engineering_no_leakage():
    provider = MockMarketDataProvider()
    df = provider.get_historical_prices("RELIANCE.NS", "2024-01-01", "2026-03-30")
    df_ind = TechnicalIndicators.calculate_indicators(df)
    df_feat = FeatureEngineer.build_features_and_targets(df_ind)

    assert "future_return_1d" in df_feat.columns
    # Last row target must be NaN because future return for last day requires future price
    assert pd.isna(df_feat["future_return_1d"].iloc[-1])

def test_stock_scorer():
    scorer = StockScorer()
    stock_row = pd.Series({
        "close": 100, "sma_20": 90, "sma_50": 85, "sma_200": 70,
        "rsi_14": 55, "stoch_rsi": 60, "macd_hist": 2.5, "relative_volume": 1.5,
        "dist_52w_high_pct": -2.0, "daily_return": 0.015
    })
    regime_info = {"regime": "Bullish"}
    score = scorer.score_stock(stock_row, regime_info)
    assert 0 <= score["composite_score"] <= 100
    assert score["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]

def test_analogues_and_prediction():
    provider = MockMarketDataProvider()
    df = provider.get_historical_prices("RELIANCE.NS", "2024-01-01", "2026-03-30")
    df_ind = TechnicalIndicators.calculate_indicators(df)
    df_feat = FeatureEngineer.build_features_and_targets(df_ind)

    analogue_analyzer = HistoricalAnalogueAnalyzer()
    analogues = analogue_analyzer.find_analogues(df_feat)
    assert "observations_count" in analogues

    predictor = PredictionModule()
    preds = predictor.train_and_predict(df_feat)
    assert "signals" in preds
    assert "1d" in preds["signals"]

def test_backtesting():
    provider = MockMarketDataProvider()
    df = provider.get_historical_prices("RELIANCE.NS", "2024-01-01", "2026-03-30")
    df_ind = TechnicalIndicators.calculate_indicators(df)

    engine = BacktestEngine()
    signals = (df_ind["close"] > df_ind["sma_20"]).astype(int)
    res = engine.backtest_signals(df_ind, signals)
    assert "total_return_pct" in res
    assert "sharpe_ratio" in res
