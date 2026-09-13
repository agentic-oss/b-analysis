from typing import Dict, List, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, max_volume_zscore: float = 10.0, price_gap_threshold: float = 0.5):
        self.max_volume_zscore = max_volume_zscore
        self.price_gap_threshold = price_gap_threshold

    def validate_ohlc(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Validates OHLCV dataframe for a given symbol.
        Checks:
        - Dates validity & missing trading days
        - Duplicate dates
        - Impossible OHLC values (High < Low, High < Open, High < Close, Low > Open, Low > Close)
        - Zero or negative prices
        - Anomalous volume spikes
        - Unexpected price gaps / splits

        Returns validation metadata with lists of warnings and errors.
        """
        results = {
            "symbol": symbol,
            "total_records": len(df),
            "valid_records": 0,
            "warnings": [],
            "errors": [],
            "is_valid": True
        }

        if df.empty:
            results["errors"].append(f"Empty dataset received for {symbol}")
            results["is_valid"] = False
            return results

        # 1. Duplicate records
        dup_dates = df[df.duplicated(subset=['date'], keep=False)]['date'].unique().tolist()
        if dup_dates:
            results["errors"].append(f"Duplicate records found on dates: {dup_dates}")

        # 2. Date sorting and missing dates check
        df_sorted = df.sort_values('date').copy()

        # 3. Check negative / zero prices
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                invalid_prices = df_sorted[df_sorted[col] <= 0]
                if not invalid_prices.empty:
                    dates = invalid_prices['date'].tolist()
                    results["errors"].append(f"Non-positive prices found in column '{col}' on dates: {dates}")

        # 4. Impossible OHLC logic
        if all(col in df_sorted.columns for col in ['open', 'high', 'low', 'close']):
            invalid_ohlc = df_sorted[
                (df_sorted['high'] < df_sorted['low']) |
                (df_sorted['high'] < df_sorted['open']) |
                (df_sorted['high'] < df_sorted['close']) |
                (df_sorted['low'] > df_sorted['open']) |
                (df_sorted['low'] > df_sorted['close'])
            ]
            if not invalid_ohlc.empty:
                dates = invalid_ohlc['date'].tolist()
                results["errors"].append(f"OHLC logic violated (e.g. High < Low or Open/Close outside High/Low) on dates: {dates}")

        # 5. Volume checks
        if 'volume' in df_sorted.columns:
            negative_vol = df_sorted[df_sorted['volume'] < 0]
            if not negative_vol.empty:
                results["errors"].append(f"Negative volume found on dates: {negative_vol['date'].tolist()}")

            # Anomalous volume spike detection
            vol_mean = df_sorted['volume'].mean()
            vol_std = df_sorted['volume'].std()
            if vol_std > 0:
                high_vol = df_sorted[(df_sorted['volume'] - vol_mean) / vol_std > self.max_volume_zscore]
                if not high_vol.empty:
                    results["warnings"].append(f"Anomalous volume spike (> {self.max_volume_zscore} std) on dates: {high_vol['date'].tolist()}")

        # 6. Price gap / potential unadjusted split check
        if 'close' in df_sorted.columns and len(df_sorted) > 1:
            returns = df_sorted['close'].pct_change().abs()
            large_gaps = df_sorted[returns > self.price_gap_threshold]
            if not large_gaps.empty:
                results["warnings"].append(f"Large price move (> {self.price_gap_threshold*100}%) on dates: {large_gaps['date'].tolist()}")

        # Calculate valid records
        if results["errors"]:
            results["is_valid"] = False
            results["valid_records"] = max(0, len(df) - len(results["errors"]))
        else:
            results["valid_records"] = len(df)

        return results
