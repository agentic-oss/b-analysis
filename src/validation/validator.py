"""
Data Validation Module for Indian Stock Market Data Pipeline.
"""

import logging
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates OHLCV market data and records data quality issues."""

    def __init__(self, volume_anomaly_multiplier: float = 100.0, max_allowed_gap_pct: float = 30.0):
        self.volume_anomaly_multiplier = volume_anomaly_multiplier
        self.max_allowed_gap_pct = max_allowed_gap_pct

    def validate_ohlcv(
        self, df: pd.DataFrame, ticker: str
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate price dataframe and return (cleaned_df, quality_report)."""
        report = {
            "ticker": ticker,
            "records_processed": len(df),
            "records_valid": 0,
            "warnings": [],
            "errors": []
        }

        if df is None or df.empty:
            report["errors"].append("Dataframe is empty or None")
            return pd.DataFrame(), report

        required_cols = ["date", "open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            report["errors"].append(f"Missing required columns: {missing_cols}")
            return pd.DataFrame(), report

        df = df.copy()

        # Date validation & duplicate check
        try:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        except Exception as e:
            report["errors"].append(f"Invalid date format: {e}")
            return pd.DataFrame(), report

        duplicates = df[df.duplicated(subset=["date"], keep=False)]
        if not duplicates.empty:
            report["warnings"].append(
                f"Found {len(duplicates)} duplicate date records. Dropping duplicates (keeping last)."
            )
            df = df.drop_duplicates(subset=["date"], keep="last")

        df = df.sort_values("date").reset_index(drop=True)

        valid_indices = []

        for idx, row in df.iterrows():
            row_warnings = []
            is_valid = True

            # Negative or zero prices
            if row["open"] <= 0 or row["high"] <= 0 or row["low"] <= 0 or row["close"] <= 0:
                report["errors"].append(f"Date {row['date']}: Zero or negative price detected (O:{row['open']}, H:{row['high']}, L:{row['low']}, C:{row['close']})")
                is_valid = False

            # Impossible OHLC relationship
            if row["low"] > row["high"]:
                report["errors"].append(f"Date {row['date']}: Low price ({row['low']}) > High price ({row['high']})")
                is_valid = False

            if row["open"] > row["high"] or row["open"] < row["low"]:
                report["errors"].append(f"Date {row['date']}: Open ({row['open']}) outside High-Low range [{row['low']}, {row['high']}]")
                is_valid = False

            if row["close"] > row["high"] or row["close"] < row["low"]:
                report["errors"].append(f"Date {row['date']}: Close ({row['close']}) outside High-Low range [{row['low']}, {row['high']}]")
                is_valid = False

            # Negative volume
            if row["volume"] < 0:
                report["errors"].append(f"Date {row['date']}: Negative volume detected ({row['volume']})")
                is_valid = False

            if is_valid:
                valid_indices.append(idx)

        valid_df = df.loc[valid_indices].copy().reset_index(drop=True)

        # Gap and anomaly checks across time series
        if len(valid_df) > 1:
            valid_df["prev_close"] = valid_df["close"].shift(1)
            valid_df["price_change_pct"] = ((valid_df["close"] - valid_df["prev_close"]) / valid_df["prev_close"]).abs() * 100

            large_gaps = valid_df[valid_df["price_change_pct"] > self.max_allowed_gap_pct]
            for _, g_row in large_gaps.iterrows():
                report["warnings"].append(f"Date {g_row['date']}: Large single-day price movement ({g_row['price_change_pct']:.2f}%)")

            # Volume anomaly check (compared to 20-day rolling median)
            rolling_vol_med = valid_df["volume"].rolling(20, min_periods=5).median()
            vol_anomalies = valid_df[valid_df["volume"] > rolling_vol_med * self.volume_anomaly_multiplier]
            for _, v_row in vol_anomalies.iterrows():
                report["warnings"].append(f"Date {v_row['date']}: Spike in volume ({v_row['volume']}) vs rolling median")

            if "prev_close" in valid_df.columns:
                valid_df = valid_df.drop(columns=["prev_close", "price_change_pct"])

        report["records_valid"] = len(valid_df)
        return valid_df, report
