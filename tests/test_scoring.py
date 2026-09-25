"""Unit tests for Stock Scoring Engine."""

import numpy as np
import pandas as pd
import pytest

from src.indicators.technical import TechnicalIndicators
from src.scoring.scorer import StockScorer


def test_stock_scorer_boundaries():
    dates = pd.date_range("2025-01-01", periods=200, freq="B")

    # Strong stock dataset
    strong_df = pd.DataFrame({
        "Date": dates,
        "Open": np.linspace(100, 200, 200),
        "High": np.linspace(102, 202, 200),
        "Low": np.linspace(98, 198, 200),
        "Close": np.linspace(100, 200, 200),
        "Volume": [50000] * 199 + [150000]  # Volume spike at end
    })
    calc_strong = TechnicalIndicators.calculate_all(strong_df)

    res_strong = StockScorer.calculate_stock_score(
        calc_strong,
        market_regime_data={"regime_score": 85.0},
        sector_data={"rank": 1}
    )

    assert res_strong["composite_score"] >= 65.0
    assert res_strong["label"] in ["Strong", "Very Strong"]
    assert "technical_trend" in res_strong["components"]
    assert "momentum" in res_strong["components"]

    # Weak stock dataset
    weak_df = pd.DataFrame({
        "Date": dates,
        "Open": np.linspace(200, 100, 200),
        "High": np.linspace(202, 102, 200),
        "Low": np.linspace(198, 98, 200),
        "Close": np.linspace(200, 100, 200),
        "Volume": [10000] * 200
    })
    calc_weak = TechnicalIndicators.calculate_all(weak_df)

    res_weak = StockScorer.calculate_stock_score(
        calc_weak,
        market_regime_data={"regime_score": 20.0},
        sector_data={"rank": 10}
    )

    assert res_weak["composite_score"] < 50.0
    assert res_weak["label"] in ["Weak", "Very Weak"]
