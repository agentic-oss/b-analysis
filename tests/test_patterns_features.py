"""Tests for Historical Analogue Patterns and Point-In-Time Feature Engineering."""

import numpy as np
import pandas as pd
import pytest

from src.indicators.technical import TechnicalIndicators
from src.patterns.analogue import HistoricalAnalogueFinder
from src.features.engineer import FeatureEngineer


def test_historical_analogue_finder():
    dates = pd.date_range("2022-01-01", periods=500, freq="B")
    np.random.seed(42)
    prices = [100.0]
    for _ in range(499):
        prices.append(prices[-1] * (1 + np.random.normal(0.0002, 0.015)))

    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p * 1.01 for p in prices],
        "Low": [p * 0.99 for p in prices],
        "Close": prices,
        "Volume": [100000] * 500
    })

    calc_df = TechnicalIndicators.calculate_all(df)
    analogue_res = HistoricalAnalogueFinder.find_analogues(calc_df)

    assert "num_matches" in analogue_res
    assert "horizons" in analogue_res
    for h in ["1d", "3d", "5d", "10d", "20d"]:
        assert h in analogue_res["horizons"]
        assert "avg_forward_return" in analogue_res["horizons"][h]
        assert "win_rate_pct" in analogue_res["horizons"][h]


def test_feature_engineer_no_lookahead_bias():
    dates = pd.date_range("2025-01-01", periods=100, freq="B")
    np.random.seed(42)
    prices = np.linspace(100, 200, 100)

    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": prices * 1.01,
        "Low": prices * 0.99,
        "Close": prices,
        "Volume": [50000] * 100
    })

    calc_df = TechnicalIndicators.calculate_all(df)
    feat_df = FeatureEngineer.build_features_for_stock(calc_df)

    # Feature at index t=50 should depend ONLY on rows <= 50
    # To test: modifying row 51-100 close price should NOT alter feature_df at row t=50
    df_modified = calc_df.copy()
    df_modified.loc[51:, "Close"] = df_modified.loc[51:, "Close"] * 10.0  # Huge jump after t=50
    feat_df_mod = FeatureEngineer.build_features_for_stock(df_modified)

    # Check that return_1d, return_5d, rsi_14, etc. at row 50 are IDENTICAL
    cols_to_check = ["return_1d", "return_5d", "return_20d", "rsi_14", "volatility_20d"]
    for col in cols_to_check:
        val_orig = feat_df.iloc[50][col]
        val_mod = feat_df_mod.iloc[50][col]
        assert np.isclose(val_orig, val_mod), f"Feature {col} changed at t=50 when future data changed!"

    # Verify target future_return_1d IS shifted forward (depends on future)
    assert pd.notnull(feat_df.iloc[50]["future_return_1d"])
    # Last row target should be NaN because future is unknown
    assert pd.isna(feat_df.iloc[-1]["future_return_1d"])
