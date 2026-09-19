import pytest
import json
from src.reporting.generator import DailyReportGenerator
from src.pipeline.daily_pipeline import DailyMarketPipeline


def test_daily_report_generator():
    generator = DailyReportGenerator()
    sample_analysis = {
        "date": "2026-03-27",
        "market": {
            "regime": "Strong Bullish",
            "regime_score": 82.5,
            "pct_above_20dma": 85.0,
            "advance_decline_ratio": 2.5,
            "advances": 10,
            "declines": 4,
            "new_highs_20d": 3,
            "new_lows_20d": 0
        },
        "sectors": [
            {
                "rank": 1,
                "sector": "NIFTY IT",
                "daily_return": 1.5,
                "weekly_return": 3.2,
                "relative_strength_1d": 0.8,
                "momentum_score": 12.0
            }
        ],
        "stocks": [
            {
                "symbol": "TCS",
                "sector": "Information Technology",
                "technical_score": 85.0,
                "score_label": "Very Strong",
                "rsi_14": 64.0,
                "volatility_regime": "Normal",
                "signals": {"breakout_20d": True, "unusual_volume": False},
                "historical_analogue_matches": 25,
                "forward_probabilities": {
                    "1d": {"avg_forward_return": 0.4, "positive_probability": 60.0},
                    "5d": {"avg_forward_return": 1.2, "positive_probability": 65.0, "directional_bias": "Bullish", "confidence": 70.0},
                    "20d": {"avg_forward_return": 3.5, "positive_probability": 70.0}
                }
            }
        ],
        "data_quality": {
            "records_processed": 100,
            "records_valid": 100,
            "warnings": [],
            "errors": []
        }
    }

    report_md = generator.generate_markdown_report(sample_analysis)
    assert "# Daily Indian Stock Market Analysis - 2026-03-27" in report_md
    assert "Strong Bullish" in report_md
    assert "NIFTY IT" in report_md
    assert "TCS" in report_md


def test_pipeline_holiday_check():
    pipeline = DailyMarketPipeline()
    # 2026-01-26 is configured in holidays.json
    res = pipeline.run("2026-01-26")
    assert res["status"] == "skipped"
    assert res["reason"] == "trading_holiday"
