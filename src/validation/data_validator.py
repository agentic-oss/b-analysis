"""
Data Validation Layer for Checking Market Data Quality.
"""

from typing import Dict, List, Any, Tuple
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates daily stock and index data and generates a quality report."""

    def __init__(self, max_allowed_daily_return: float = 0.5):
        self.max_allowed_daily_return = max_allowed_daily_return

    def validate_df(self, df: pd.DataFrame, ticker: str) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates a dataframe of daily stock data.
        Returns:
            (clean_valid_df, list_of_warnings, list_of_errors)
        """
        warnings = []
        errors = []

        if df.empty:
            errors.append({"ticker": ticker, "type": "empty_data", "message": "No data returned for ticker"})
            return pd.DataFrame(), warnings, errors

        # Standard check: required columns
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append({
                "ticker": ticker,
                "type": "missing_columns",
                "message": f"Missing required columns: {missing_cols}"
            })
            return pd.DataFrame(), warnings, errors

        df = df.copy()

        # 1. Date Validation & Duplicates
        df["date"] = pd.to_datetime(df["date"])
        duplicate_dates = df[df.duplicated("date", keep=False)]
        if not duplicate_dates.empty:
            warnings.append({
                "ticker": ticker,
                "type": "duplicate_dates",
                "message": f"Found {len(duplicate_dates)} duplicate date rows. Deduplicating by keeping last."
            })
            df = df.drop_duplicates(subset=["date"], keep="last")

        df = df.sort_values("date").reset_index(drop=True)

        # 2. Impossible OHLC relationships
        # High should be >= Open, Close, Low. Low should be <= Open, Close, High.
        invalid_ohlc = df[
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) |
            (df["high"] < df["close"]) |
            (df["low"] > df["open"]) |
            (df["low"] > df["close"])
        ]
        if not invalid_ohlc.empty:
            errors.append({
                "ticker": ticker,
                "type": "invalid_ohlc",
                "message": f"Found {len(invalid_ohlc)} rows with invalid OHLC relationship on dates: {invalid_ohlc['date'].dt.strftime('%Y-%m-%d').tolist()}"
            })

        # 3. Non-positive Prices
        non_positive = df[(df["open"] <= 0) | (df["high"] <= 0) | (df["low"] <= 0) | (df["close"] <= 0)]
        if not non_positive.empty:
            errors.append({
                "ticker": ticker,
                "type": "non_positive_price",
                "message": f"Found {len(non_positive)} rows with price <= 0"
            })

        # 4. Negative Volume
        neg_volume = df[df["volume"] < 0]
        if not neg_volume.empty:
            errors.append({
                "ticker": ticker,
                "type": "negative_volume",
                "message": f"Found {len(neg_volume)} rows with negative volume"
            })

        # 5. Anomalous Return Spikes (potential unadjusted split or bad data)
        df["prev_close"] = df["close"].shift(1)
        df["daily_return"] = (df["close"] - df["prev_close"]).abs() / df["prev_close"]
        spikes = df[df["daily_return"] > self.max_allowed_daily_return]
        if not spikes.empty:
            warnings.append({
                "ticker": ticker,
                "type": "extreme_price_spike",
                "message": f"Found {len(spikes)} days with price change > {self.max_allowed_daily_return * 100}%: {spikes['date'].dt.strftime('%Y-%m-%d').tolist()}"
            })

        # Convert date back to string format
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        clean_cols = [c for c in df.columns if c not in ["prev_close", "daily_return"]]
        valid_df = df[clean_cols]

        return valid_df, warnings, errors

    def create_quality_report(
        self, date_str: str, total_processed: int, valid_count: int, warnings: List[Dict[str, Any]], errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Creates standard quality report dictionary."""
        return {
            "date": date_str,
            "records_processed": total_processed,
            "records_valid": valid_count,
            "warnings_count": len(warnings),
            "errors_count": len(errors),
            "warnings": warnings,
            "errors": errors
        }
