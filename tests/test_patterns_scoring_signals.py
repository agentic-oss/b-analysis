import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.patterns.analogue_finder import AnalogueFinder
from src.scoring.stock_scorer import StockScorer
from src.scoring.signals import SignalGenerator

def create_mock_history():
    np.random.seed(42)
    dates = pd.date_range(end="2026-03-01", periods=150, freq="B").strftime("%Y-%m-%d").tolist()
    price = 100.0
    prices = []
    for _ in range(150):
        price += np.random.normal(0.2, 1.2)
        prices.append(price)

    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [50000] * 150
    })
    return TechnicalIndicators.calculate_all(df)

def test_analogue_finder():
    df = create_mock_history()
    res = AnalogueFinder.find_analogues(df)
    assert "num_analogues" in res
    assert "horizons" in res
    assert "5d" in res["horizons"]
    assert res["horizons"]["5d"]["positive_return_probability"] >= 0

def test_stock_scorer_and_signals():
    df = create_mock_history()
    regime = {"regime": "Bullish"}
    sector = {"momentum_score": 70.0}

    score = StockScorer.calculate_score(df, regime, sector, fundamental_score=75.0)
    assert score["composite_score"] > 0
    assert score["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]

    analogues = AnalogueFinder.find_analogues(df)
    signals = SignalGenerator.generate_signals(score, analogues)
    assert "5d" in signals
    assert signals["5d"]["directional_bias"] in ["Bullish", "Slightly Bullish", "Neutral", "Slightly Bearish", "Bearish"]
    assert 0 <= signals["5d"]["confidence"] <= 100
