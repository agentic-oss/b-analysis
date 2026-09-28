import os
import json
import pytest
import pandas as pd
from src.reporting.markdown_report import MarkdownReportGenerator
from src.reporting.json_output import JsonOutputGenerator

def test_markdown_and_json_report_generation(tmp_path):
    sample_data = {
        "date": "2026-03-27",
        "market": {
            "market_regime": "Bullish",
            "nifty_close": 22500.0,
            "nifty_trend": "Uptrend",
            "banknifty_trend": "Uptrend",
            "nifty_volatility_20d": 0.14,
            "breadth": {
                "total_tracked": 10,
                "pct_above_20dma": 80.0,
                "pct_above_50dma": 70.0,
                "pct_above_200dma": 90.0,
                "advance_decline_ratio": 2.5,
                "advances": 7,
                "declines": 3,
                "new_highs_20d": 2,
                "new_lows_20d": 0
            }
        },
        "sectors": [
            {
                "rank": 1,
                "sector": "NIFTY IT",
                "daily_return": 1.5,
                "weekly_return": 3.2,
                "relative_strength_vs_nifty": 0.8,
                "momentum_score": 78.5
            }
        ],
        "stocks": [
            {
                "symbol": "TCS",
                "technical_score": 82.0,
                "label": "Very Strong",
                "fundamental_score": 74.0,
                "signals": ["20-Day High Breakout"],
                "forward_signals": {
                    "1d": {"directional_bias": "Bullish"},
                    "5d": {"directional_bias": "Slightly Bullish"}
                }
            }
        ],
        "quality": {
            "records_processed": 10,
            "records_valid": 10,
            "warnings": [],
            "errors": []
        }
    }

    json_path = os.path.join(tmp_path, "2026-03-27.json")
    md_path = os.path.join(tmp_path, "2026-03-27.md")

    JsonOutputGenerator.generate_json_output(sample_data, json_path)
    MarkdownReportGenerator.generate_report(sample_data, md_path)

    assert os.path.exists(json_path)
    assert os.path.exists(md_path)

    with open(json_path, "r") as f:
        loaded = json.load(f)
        assert loaded["date"] == "2026-03-27"

    with open(md_path, "r") as f:
        content = f.read()
        assert "Daily Indian Stock Market Research Report" in content
        assert "TCS" in content
