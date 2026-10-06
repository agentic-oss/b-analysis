import os
import shutil
import tempfile
import pandas as pd
from src.storage.manager import StorageManager

def test_storage_manager_lifecycle():
    temp_dir = tempfile.mkdtemp()
    try:
        sm = StorageManager(base_dir=temp_dir)

        df1 = pd.DataFrame({
            'date': ['2025-01-01', '2025-01-02'],
            'open': [100, 102],
            'high': [105, 106],
            'low': [99, 101],
            'close': [103, 105],
            'volume': [1000, 1200]
        })

        # Test appending prices
        p1 = sm.append_processed_prices('RELIANCE', df1)
        assert os.path.exists(p1)

        loaded1 = sm.load_processed_prices('RELIANCE')
        assert len(loaded1) == 2

        # Test append without duplicate duplication
        df2 = pd.DataFrame({
            'date': ['2025-01-02', '2025-01-03'],
            'open': [102, 104],
            'high': [106, 108],
            'low': [101, 103],
            'close': [105, 107],
            'volume': [1200, 1500]
        })

        sm.append_processed_prices('RELIANCE', df2)
        loaded2 = sm.load_processed_prices('RELIANCE')
        assert len(loaded2) == 3 # 2025-01-01, 02, 03

        # Test saving JSON quality report and daily analysis
        qpath = sm.save_quality_report('2025-01-03', {'records_processed': 1})
        assert os.path.exists(qpath)

        apath = sm.save_daily_analysis('2025-01-03', {'status': 'ok'})
        assert os.path.exists(apath)

    finally:
        shutil.rmtree(temp_dir)
