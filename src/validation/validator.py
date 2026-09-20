"""Data Validator for market datasets."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DataValidator:
    """Validates raw market data records and generates quality reports."""

    def validate_df(self, df: pd.DataFrame, date_str: str) -> Dict[str, Any]:
        """Validates a DataFrame of daily price records for multiple tickers or a single ticker."""
        records_processed = len(df)
        warnings = []
        errors = []

        if df.empty:
            errors.append(f"No records found for date {date_str}")
            return {
                "date": date_str,
                "records_processed": 0,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        valid_mask = pd.Series(True, index=df.index)

        # Check required columns
        req_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
        missing_cols = [c for c in req_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return {
                "date": date_str,
                "records_processed": records_processed,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        # Check duplicate ticker/date
        duplicates = df.duplicated(subset=['ticker', 'date'], keep=False)
        if duplicates.any():
            dup_tickers = df[duplicates]['ticker'].unique().tolist()
            warnings.append(f"Duplicate ticker/date entries found for: {dup_tickers}")
            valid_mask = valid_mask & (~df.duplicated(subset=['ticker', 'date'], keep='first'))

        # Check negative or zero prices
        zero_neg_price = (df['open'] <= 0) | (df['high'] <= 0) | (df['low'] <= 0) | (df['close'] <= 0)
        if zero_neg_price.any():
            invalid_tickers = df[zero_neg_price]['ticker'].unique().tolist()
            errors.append(f"Zero or negative prices detected for tickers: {invalid_tickers}")
            valid_mask = valid_mask & (~zero_neg_price)

        # Check impossible High/Low values
        impossible_ohlc = (df['high'] < df['open']) | (df['high'] < df['close']) | (df['high'] < df['low']) | \
                          (df['low'] > df['open']) | (df['low'] > df['close'])
        if impossible_ohlc.any():
            invalid_tickers = df[impossible_ohlc]['ticker'].unique().tolist()
            errors.append(f"Impossible OHLC prices (e.g. Low > Open/Close/High) for tickers: {invalid_tickers}")
            valid_mask = valid_mask & (~impossible_ohlc)

        # Check negative volume
        neg_volume = df['volume'] < 0
        if neg_volume.any():
            invalid_tickers = df[neg_volume]['ticker'].unique().tolist()
            errors.append(f"Negative volume detected for tickers: {invalid_tickers}")
            valid_mask = valid_mask & (~neg_volume)

        # Check for extreme price jumps (e.g. >50% intraday or vs prev day if sorting)
        intraday_jump = ((df['high'] - df['low']) / df['low']) > 0.50
        if intraday_jump.any():
            jump_tickers = df[intraday_jump]['ticker'].unique().tolist()
            warnings.append(f"Anomalous intraday range (>50%) detected for tickers: {jump_tickers}")

        records_valid = int(valid_mask.sum())

        return {
            "date": date_str,
            "records_processed": int(records_processed),
            "records_valid": records_valid,
            "warnings": warnings,
            "errors": errors
        }
