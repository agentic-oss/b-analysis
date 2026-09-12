import pytest
import os
import json
from src.reporting.report_generator import ReportGenerator

def test_report_generator(tmp_path):
    reports_dir = tmp_path / "reports"
    analysis_dir = tmp_path / "analysis"
    rg = ReportGenerator(reports_dir=str(reports_dir), data_analysis_dir=str(analysis_dir))

    mock_output = {
        "date": "2026-03-01",
        "market": {"regime": "Bullish", "nifty_close": 22000.0, "advance_decline_ratio": 1.5},
        "sectors": [{"rank": 1, "sector": "IT", "daily_return": 1.2, "momentum_score": 80.0}],
        "stocks": [{
            "symbol": "RELIANCE",
            "score": {"composite_score": 82.5, "label": "Very Strong", "components": {}},
            "technical_events": {"breakout_20d": True},
            "signals": {"5d": {"directional_bias": "Bullish", "confidence": 75.0}}
        }],
        "data_quality": {"records_processed": 10, "records_valid": 10}
    }

    json_p = rg.generate_json_output("2026-03-01", mock_output)
    md_p = rg.generate_markdown_report("2026-03-01", mock_output)

    assert os.path.exists(json_p)
    assert os.path.exists(md_p)

    with open(json_p) as f:
        data = json.load(f)
        assert data["date"] == "2026-03-01"
