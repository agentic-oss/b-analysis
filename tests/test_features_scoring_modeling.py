import pytest
import pandas as pd
from src.ingestion.provider import MockDataProvider
from src.indicators.technical import calculate_technical_indicators
from src.fundamentals.analysis import analyze_fundamentals
from src.scoring.composite import calculate_composite_score
from src.patterns.analogues import find_historical_analogues
from src.features.engineering import generate_ml_features_and_targets
from src.modeling.prediction import ProbabilisticForecastModel
from src.backtesting.engine import BacktestEngine

def test_fundamentals_and_scoring():
    raw_info = {
        "marketCap": 1000000000,
        "trailingPE": 20.0,
        "returnOnEquity": 0.18,
        "debtToEquity": 30.0,
        "revenueGrowth": 0.15
    }
    fund = analyze_fundamentals("TCS", raw_info)
    assert fund["available"] is True
    assert fund["fundamental_score"] > 50.0

    prov = MockDataProvider()
    df = calculate_technical_indicators(prov.get_historical_prices("TCS", "2024-01-01", "2025-01-01"))
    market_regime = {"composite_score": 60.0, "nifty_1d_return": 0.2}

    score_res = calculate_composite_score(df, market_regime, fundamental_info=fund)
    assert 0.0 <= score_res["composite_score"] <= 100.0
    assert score_res["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]

def test_feature_engineering_lookahead_leakage_prevention():
    prov = MockDataProvider()
    df = calculate_technical_indicators(prov.get_historical_prices("INFY", "2024-01-01", "2025-01-01"))

    feat_df = generate_ml_features_and_targets(df, "INFY")
    assert "return_1d" in feat_df.columns
    assert "future_return_1d" in feat_df.columns

    # Verify latest row's future_return_1d is NaN (since future is unknown on date T)
    assert pd.isna(feat_df["future_return_1d"].iloc[-1])

def test_prediction_model_and_backtester():
    prov = MockDataProvider()
    df = calculate_technical_indicators(prov.get_historical_prices("HDFCBANK", "2023-01-01", "2025-01-01"))

    analogues = find_historical_analogues(df)
    model = ProbabilisticForecastModel()
    forecast = model.generate_directional_signals(df, analogues, {"composite_score": 65.0})

    assert "5d" in forecast
    assert forecast["5d"]["directional_bias"] in ["Bullish", "Slightly Bullish", "Neutral", "Slightly Bearish", "Bearish"]

    backtester = BacktestEngine()
    bt_res = backtester.run_composite_score_backtest({"HDFCBANK": df})
    assert "total_return_pct" in bt_res
    assert "win_rate_pct" in bt_res
