import os
import pytest
import pandas as pd
from src.storage.historical_storage import HistoricalStorage

def test_historical_storage(tmp_path):
    storage = HistoricalStorage(base_dir=str(tmp_path))

    df1 = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02"],
        "symbol": ["RELIANCE.NS", "RELIANCE.NS"],
        "close": [100.0, 102.0],
        "provider": ["yfinance", "yfinance"]
    })

    storage.save_raw_daily("2025-01-02", "RELIANCE.NS", df1)

    # Test update and deduplication
    storage.update_processed_history("RELIANCE.NS", df1)

    df2 = pd.DataFrame({
        "Date": ["2025-01-02", "2025-01-03"],
        "symbol": ["RELIANCE.NS", "RELIANCE.NS"],
        "close": [102.5, 105.0],
        "provider": ["yfinance", "yfinance"]
    })

    updated = storage.update_processed_history("RELIANCE.NS", df2)
    assert len(updated) == 3
    assert updated.loc[updated["Date"] == "2025-01-02", "close"].values[0] == 102.5

    loaded = storage.load_processed_history("RELIANCE.NS")
    assert len(loaded) == 3
