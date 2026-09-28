import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger("validation.validator")

class DataValidator:
    """Validates financial data records and outputs data quality reports."""

    def __init__(self, volume_anomaly_threshold: float = 5.0, price_change_threshold: float = 0.30):
        self.volume_anomaly_threshold = volume_anomaly_threshold
        self.price_change_threshold = price_change_threshold

    def validate_daily_prices(self, df: pd.DataFrame, target_date: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validates daily price data and returns (valid_df, quality_report)."""
        warnings = []
        errors = []

        if df.empty:
            return df, {
                "date": target_date,
                "records_processed": 0,
                "records_valid": 0,
                "warnings": ["Empty dataframe received"],
                "errors": ["No records found for target date"]
            }

        records_processed = len(df)
        valid_rows = []

        for idx, row in df.iterrows():
            symbol = row.get("symbol", f"row_{idx}")
            row_errors = []

            # Check OHLC missing or non-numeric
            for col in ['open', 'high', 'low', 'close']:
                val = row.get(col)
                if pd.isnull(val) or val <= 0:
                    row_errors.append(f"{symbol}: Invalid or non-positive {col} price ({val})")

            # Check OHLC logical relationship: low <= min(open, close) & high >= max(open, close)
            open_p, high_p, low_p, close_p = row.get('open', 0), row.get('high', 0), row.get('low', 0), row.get('close', 0)
            if open_p > 0 and high_p > 0 and low_p > 0 and close_p > 0:
                if low_p > min(open_p, close_p) * 1.0001:
                    row_errors.append(f"{symbol}: Low price ({low_p}) > min(open, close)")
                if high_p < max(open_p, close_p) * 0.9999:
                    row_errors.append(f"{symbol}: High price ({high_p}) < max(open, close)")

            # Check volume
            vol = row.get('volume', 0)
            if pd.isnull(vol) or vol < 0:
                row_errors.append(f"{symbol}: Invalid volume ({vol})")
            elif vol == 0:
                warnings.append(f"{symbol}: Zero trading volume recorded")

            if row_errors:
                errors.extend(row_errors)
            else:
                valid_rows.append(row)

        valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
        records_valid = len(valid_df)

        report = {
            "date": target_date,
            "records_processed": records_processed,
            "records_valid": records_valid,
            "warnings": warnings,
            "errors": errors
        }

        return valid_df, report

    def check_historical_gaps_and_anomalies(self, df: pd.DataFrame) -> List[str]:
        """Detect price spikes, unusual volume, and missing trading days in time series."""
        warnings = []
        if df.empty or len(df) < 2:
            return warnings

        df_sorted = df.sort_values('date').reset_index(drop=True)

        # Check daily price returns for unreasonable jumps (>30%)
        df_sorted['pct_change'] = df_sorted['close'].pct_change().abs()
        spikes = df_sorted[df_sorted['pct_change'] > self.price_change_threshold]
        for _, row in spikes.iterrows():
            warnings.append(f"{row['symbol']} on {row['date']}: Large price jump ({row['pct_change']*100:.1f}%) detected")

        # Check volume spikes against historical rolling average prior to current day
        mean_vol = df_sorted['volume'].shift(1).rolling(20, min_periods=1).mean()
        df_sorted['vol_ratio'] = df_sorted['volume'] / (mean_vol + 1e-5)
        vol_spikes = df_sorted[df_sorted['vol_ratio'] > self.volume_anomaly_threshold]
        for _, row in vol_spikes.iterrows():
            warnings.append(f"{row['symbol']} on {row['date']}: Volume anomaly ({row['vol_ratio']:.1f}x historical average)")

        return warnings
