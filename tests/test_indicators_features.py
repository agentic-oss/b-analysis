import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.indicators.events import TechnicalEvents
from src.features.feature_builder import FeatureBuilder

def create_sample_price_data(n=250):
    np.random.seed(42)
    dates = pd.date_range(end="2026-03-01", periods=n, freq="B").strftime("%Y-%m-%d").tolist()
    price = 100.0
    prices = []
    for _ in range(n):
        price += np.random.normal(0.1, 1.5)
        prices.append(max(price, 10.0))

    df = pd.DataFrame({
        "date": dates,
        "open": [p - 0.5 for p in prices],
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": np.random.randint(1000, 50000, size=n),
        "ticker": ["RELIANCE.NS"] * n
    })
    return df

def test_technical_indicators_calculation():
    df = create_sample_price_data(250)
    df_ind = TechnicalIndicators.calculate_all(df)

    assert "sma_20" in df_ind.columns
    assert "ema_50" in df_ind.columns
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "atr_14" in df_ind.columns
    assert "volatility_20d" in df_ind.columns
    assert not df_ind["sma_20"].isna().all()

def test_technical_events_detection():
    df = create_sample_price_data(250)
    df_ind = TechnicalIndicators.calculate_all(df)
    events = TechnicalEvents.identify_events(df_ind)

    assert "golden_cross" in events
    assert "trend_state" in events
    assert "support_level" in events
    assert events["support_level"] > 0

def test_feature_builder_no_lookahead_bias():
    df = create_sample_price_data(100)
    feats = FeatureBuilder.build_features(df)

    # Check that feature columns at index i do NOT change if future rows are appended or modified
    sub_df = df.iloc[:50].copy()
    feats_sub = FeatureBuilder.build_features(sub_df)

    # Feature values at index 40 should be identical
    feat_cols = FeatureBuilder.get_feature_column_names()
    for col in feat_cols:
        val_full = feats.iloc[40][col]
        val_sub = feats_sub.iloc[40][col]
        if pd.isna(val_full) and pd.isna(val_sub):
            continue
        assert np.isclose(val_full, val_sub, rtol=1e-5), f"Mismatch in {col} at index 40: {val_full} vs {val_sub}"
