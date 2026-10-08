import os
import pytest
import pandas as pd
from src.storage.storage_manager import StorageManager


@pytest.fixture
def temp_storage(tmp_path):
    storage = StorageManager(base_dir=str(tmp_path))
    return storage


def test_save_and_load_processed_prices(temp_storage):
    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-02"],
        "open": [100.0, 102.0],
        "close": [104.0, 105.0],
        "volume": [1000, 1200]
    })
    temp_storage.save_processed_prices(df, "RELIANCE", "NSE")

    loaded = temp_storage.load_processed_prices("RELIANCE")
    assert not loaded.empty
    assert len(loaded) == 2
    assert "ticker" in loaded.columns
    assert "exchange" in loaded.columns
    assert "ingestion_timestamp" in loaded.columns
    assert loaded["ticker"].iloc[0] == "RELIANCE"


def test_save_and_load_features(temp_storage):
    df = pd.DataFrame({
        "date": ["2025-01-02"],
        "ticker": ["RELIANCE"],
        "rsi_14": [65.4]
    })
    temp_storage.save_features(df, "RELIANCE")
    loaded = temp_storage.load_features("RELIANCE")
    assert not loaded.empty
    assert loaded["rsi_14"].iloc[0] == 65.4


def test_save_quality_and_daily_analysis(temp_storage):
    date_str = "2025-01-02"
    q_report = {"date": date_str, "valid_records": 100}
    temp_storage.save_quality_report(date_str, q_report)

    q_path = os.path.join(temp_storage.quality_dir, f"{date_str}.json")
    assert os.path.exists(q_path)

    analysis_report = {"date": date_str, "market": {}}
    temp_storage.save_daily_analysis(date_str, analysis_report)

    a_path = os.path.join(temp_storage.analysis_dir, "daily", f"{date_str}.json")
    assert os.path.exists(a_path)
