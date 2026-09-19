import os
import json
import pytest
import pandas as pd
from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage import StorageManager


def test_configs_exist():
    assert os.path.exists("config/stocks.json")
    assert os.path.exists("config/config.json")
    assert os.path.exists("config/holidays.json")

    with open("config/stocks.json") as f:
        stocks = json.load(f)
        assert "stocks" in stocks
        assert "indices" in stocks

    with open("config/config.json") as f:
        cfg = json.load(f)
        assert "pipeline" in cfg
        assert "indicator_params" in cfg

    with open("config/holidays.json") as f:
        holidays = json.load(f)
        assert "holidays" in holidays


def test_data_validator():
    validator = DataValidator()
    raw_data = pd.DataFrame([
        {"date": "2026-03-25", "open": 100.0, "high": 105.0, "low": 98.0, "close": 102.0, "volume": 1000},
        {"date": "2026-03-26", "open": 102.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1200}, # invalid: open > high
        {"date": "2026-03-27", "open": 100.0, "high": 108.0, "low": 99.0, "close": 107.0, "volume": 1500},
    ])

    cleaned_df, report = validator.validate_ohlcv(raw_data, "TEST")
    assert len(cleaned_df) == 2
    assert report["records_processed"] == 3
    assert report["records_valid"] == 2
    assert len(report["errors"]) == 1


def test_storage_manager(tmp_path):
    storage = StorageManager(base_dir=str(tmp_path / "data"), reports_dir=str(tmp_path / "reports"))
    sample_df = pd.DataFrame([
        {"date": "2026-03-27", "open": 100.0, "high": 108.0, "low": 99.0, "close": 107.0, "volume": 1500}
    ])

    saved_raw = storage.save_raw_data(sample_df, "TEST", "2026-03-27")
    assert saved_raw.exists()

    saved_proc = storage.save_processed_prices(sample_df, "TEST", "prices")
    assert saved_proc.exists()

    loaded = storage.load_processed_prices("TEST", "prices")
    assert len(loaded) == 1
    assert loaded.iloc[0]["close"] == 107.0
