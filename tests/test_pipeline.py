"""
Integration test for DailyPipeline execution in sample mode.
"""
from pathlib import Path
from src.pipeline.daily_pipeline import DailyPipeline


def test_pipeline_sample_run(tmp_path):
    pipeline = DailyPipeline(config_dir="config", base_dir=str(tmp_path))
    date_str = "2025-02-28"

    result = pipeline.run(date_str=date_str, sample_mode=True)

    assert result["date"] == date_str
    assert "market" in result
    assert "stocks" in result
    assert len(result["stocks"]) > 0

    # Verify output files were created in tmp_path
    quality_file = tmp_path / "data" / "quality" / f"{date_str}.json"
    analysis_file = tmp_path / "data" / "analysis" / "daily" / f"{date_str}.json"
    report_file = tmp_path / "reports" / "daily" / f"{date_str}.md"

    assert quality_file.exists()
    assert analysis_file.exists()
    assert report_file.exists()
