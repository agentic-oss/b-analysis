"""
Tests for FeatureEngine and Look-Ahead Bias Prevention.
"""
import pandas as pd
import numpy as np
from src.features.builder import FeatureEngine


def test_no_lookahead_bias_in_features():
    dates = pd.date_range("2024-01-01", periods=30)
    prices = np.linspace(100, 130, 30)

    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": prices,
        "High": prices + 2,
        "Low": prices - 2,
        "Close": prices,
        "Volume": [1000] * 30,
        "sma_20": prices,
        "rsi_14": [50] * 30,
    })

    feature_df = FeatureEngine.build_feature_set(df)

    # Check future return targets
    # For date T, future_return_1d should match (Close[T+1] - Close[T])/Close[T]
    close = df["Close"].values
    t_idx = 10
    expected_fwd_1d = (close[t_idx + 1] - close[t_idx]) / close[t_idx]
    actual_fwd_1d = feature_df.iloc[t_idx]["future_return_1d"]

    assert abs(actual_fwd_1d - expected_fwd_1d) < 1e-6
    # The last row should have NaN for future_return_1d because future data does not exist
    assert pd.isna(feature_df.iloc[-1]["future_return_1d"])
