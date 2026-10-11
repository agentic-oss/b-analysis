import pytest
import pandas as pd
from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.manager import StorageManager


def test_validator_ohlc():
    validator = DataValidator()
    df_valid = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "open": [100.0, 105.0],
        "high": [110.0, 112.0],
        "low": [95.0, 102.0],
        "close": [105.0, 108.0],
        "volume": [1000, 1500]
    })
    res = validator.validate_ohlc(df_valid)
    assert res["records_processed"] == 2
    assert res["records_valid"] == 2
    assert len(res["errors"]) == 0

    df_invalid = pd.DataFrame({
        "date": ["2026-03-01"],
        "open": [100.0],
        "high": [90.0], # Impossible high < open
        "low": [95.0],
        "close": [105.0],
        "volume": [1000]
    })
    res_inv = validator.validate_ohlc(df_invalid)
    assert res_inv["records_valid"] == 0
    assert len(res_inv["errors"]) > 0


def test_storage_manager(tmp_path):
    mgr = StorageManager(base_dir=str(tmp_path))
    df = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "open": [100.0, 105.0],
        "high": [110.0, 112.0],
        "low": [95.0, 102.0],
        "close": [105.0, 108.0],
        "volume": [1000, 1500],
        "symbol": ["RELIANCE", "RELIANCE"]
    })
    path = mgr.save_processed_prices(df, "RELIANCE")
    assert path != ""

    loaded = mgr.load_processed_prices("RELIANCE")
    assert len(loaded) == 2
    assert loaded["close"].iloc[0] == 105.0
