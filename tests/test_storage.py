import os
import json
import pytest
import pandas as pd
import tempfile
from src.storage.storage import DataStorage

def test_data_storage_flow():
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = DataStorage(base_dir=temp_dir)

        df = pd.DataFrame({
            'date': ['2026-01-01', '2026-01-02'],
            'open': [100.0, 102.0],
            'high': [105.0, 106.0],
            'low': [99.0, 100.0],
            'close': [102.0, 101.0],
            'adj_close': [102.0, 101.0],
            'volume': [1000, 1200]
        })

        # Test save raw
        raw_path = storage.save_raw_data(df, "RELIANCE", "2026-01-02")
        assert os.path.exists(raw_path)

        # Test save processed
        processed_path = storage.save_processed_prices(df, "RELIANCE")
        assert os.path.exists(processed_path)

        # Test load processed
        loaded_df = storage.load_processed_prices("RELIANCE")
        assert len(loaded_df) == 2

        # Test save quality report
        quality_path = storage.save_quality_report({"records_processed": 2}, "2026-01-02")
        assert os.path.exists(quality_path)

        # Test save daily analysis
        analysis_path = storage.save_daily_analysis({"date": "2026-01-02"}, "2026-01-02")
        assert os.path.exists(analysis_path)
