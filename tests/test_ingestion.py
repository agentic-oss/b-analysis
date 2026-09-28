import os
import tempfile
import pandas as pd
import pytest
from src.ingestion.provider import YFinanceProvider
from src.storage.store import StorageEngine

def test_yfinance_provider_ticker_format():
    provider = YFinanceProvider()
    assert provider._ticker_symbol("RELIANCE", "NSE") == "RELIANCE.NS"
    assert provider._ticker_symbol("TCS", "BSE") == "TCS.BO"
    assert provider._ticker_symbol("^NSEI", "NSE") == "^NSEI"

def test_storage_engine_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = StorageEngine(base_dir=tmpdir)
        df_sample = pd.DataFrame([{
            'date': '2026-03-27',
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'open': 2500.0,
            'high': 2550.0,
            'low': 2480.0,
            'close': 2530.0,
            'volume': 1000000
        }])

        store.save_raw_data(df_sample, '2026-03-27', 'prices')
        assert os.path.exists(os.path.join(tmpdir, 'raw', '2026', '03', '2026-03-27', 'prices.csv'))

        store.save_processed_prices('RELIANCE', df_sample)
        loaded_df = store.load_processed_prices('RELIANCE')
        assert not loaded_df.empty
        assert loaded_df.iloc[0]['symbol'] == 'RELIANCE'
