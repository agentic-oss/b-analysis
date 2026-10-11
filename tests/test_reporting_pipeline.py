import pytest
import os
import json
import pandas as pd
from src.reporting.report_generator import ReportGenerator
from src.pipeline.daily_pipeline import DailyMarketPipeline


def test_report_generator():
    market_data = {
        "regime": "Bullish",
        "confidence_score": 75.0,
        "nifty_close": 22000.0,
        "nifty_return_1d": 0.005,
        "nifty_trend": "Bullish",
        "banknifty_trend": "Bullish",
        "nifty_volatility": 0.12,
        "breadth": {
            "advance_decline_ratio": 1.5,
            "advances": 15,
            "declines": 10,
            "pct_above_20dma": 60.0,
            "pct_above_50dma": 65.0,
            "pct_above_200dma": 70.0,
            "new_52w_highs": 2,
            "new_52w_lows": 0
        }
    }

    sector_data = {
        "sectors": [
            {
                "sector": "NIFTY BANK",
                "return_1d": 1.2,
                "momentum_score": 5.0,
                "leaders": ["HDFCBANK"],
                "laggards": []
            }
        ]
    }

    stock_scores = [
        {
            "symbol": "RELIANCE",
            "technical_score": 82.0,
            "composite_label": "Very Strong",
            "fundamental_score": 75.0,
            "signals": {
                "return_1d": 0.015,
                "rsi_14": 62.0,
                "events": ["20-Day High Breakout"]
            },
            "historical_analogues": {
                "matches_count": 12,
                "forward_statistics": {
                    "5d": {"positive_probability": 65.0, "average_return_pct": 1.8}
                }
            },
            "forward_probabilities": {
                "directional_bias": "Bullish",
                "confidence": 70.0
            }
        }
    ]

    quality_data = {
        "records_processed": 100,
        "records_valid": 100,
        "warnings": [],
        "errors": []
    }

    md = ReportGenerator.generate_markdown_report("2026-03-06", market_data, sector_data, stock_scores, quality_data)
    assert "# Daily Indian Stock Market Research & Deep Analysis Report" in md
    assert "RELIANCE" in md

    json_schema = ReportGenerator.build_daily_json_schema("2026-03-06", market_data, sector_data, stock_scores)
    assert json_schema["date"] == "2026-03-06"
    assert json_schema["market"]["regime"] == "Bullish"


def test_pipeline_holiday_check(tmp_path):
    pipeline = DailyMarketPipeline(base_data_dir=str(tmp_path))
    assert pipeline.is_trading_holiday("2026-01-26") is True
    assert pipeline.is_trading_holiday("2026-03-06") is False
