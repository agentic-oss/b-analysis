"""
Tests for StockScorer.
"""
import pandas as pd
from src.scoring.evaluator import StockScorer


def test_stock_scorer_output():
    stock_df = pd.DataFrame({
        "Close": [100, 102, 105, 108, 110],
        "sma_20": [95, 96, 97, 98, 99],
        "sma_50": [90, 91, 92, 93, 94],
        "sma_200": [80, 81, 82, 83, 84],
        "rsi_14": [55, 58, 60, 62, 64],
        "macd_histogram": [0.5, 0.6, 0.7, 0.8, 0.9],
        "relative_volume": [1.5, 1.4, 1.3, 1.6, 1.8],
        "return_20d": [0.05, 0.06, 0.07, 0.08, 0.10],
        "volatility_20d": [0.20, 0.20, 0.20, 0.20, 0.20],
    })

    mkt_data = {"score": 75.0, "regime": "Bullish"}
    sec_data = {"momentum_score": 20.0}
    fund_data = {"score": 80.0}

    result = StockScorer.score_stock(stock_df, mkt_data, sec_data, fund_data)

    assert "composite_score" in result
    assert "label" in result
    assert result["composite_score"] >= 0 and result["composite_score"] <= 100
    assert result["label"] in ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"]
