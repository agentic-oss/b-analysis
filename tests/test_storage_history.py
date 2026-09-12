import pytest
import os
import shutil
import pandas as pd
from src.storage.storage_manager import StorageManager
from src.storage.history_manager import HistoryManager

@pytest.fixture
def temp_storage(tmp_path):
    storage_dir = tmp_path / "data"
    sm = StorageManager(base_dir=str(storage_dir))
    hm = HistoryManager(storage_manager=sm)
    return sm, hm

def test_storage_raw_save(temp_storage):
    sm, _ = temp_storage
    df = pd.DataFrame({
        "date": ["2026-03-01"],
        "open": [100.0],
        "high": [105.0],
        "low": [98.0],
        "close": [104.0],
        "volume": [1000]
    })
    path = sm.save_raw_daily(df, "2026-03-01", "RELIANCE.NS")
    assert os.path.exists(path)
    assert "2026/03/2026-03-01" in path

def test_history_manager_deduplication(temp_storage):
    _, hm = temp_storage
    df1 = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "open": [100.0, 102.0],
        "close": [104.0, 105.0],
        "ticker": ["RELIANCE.NS", "RELIANCE.NS"]
    })
    hm.update_history(df1, category="prices")

    # Update with duplicate date but updated close
    df2 = pd.DataFrame({
        "date": ["2026-03-02", "2026-03-03"],
        "open": [102.0, 106.0],
        "close": [108.0, 109.0],
        "ticker": ["RELIANCE.NS", "RELIANCE.NS"]
    })
    combined = hm.update_history(df2, category="prices")

    assert len(combined) == 3
    rel_0302 = combined[(combined["ticker"] == "RELIANCE.NS") & (combined["date"] == "2026-03-02")]
    assert rel_0302["close"].values[0] == 108.0
