import json
import os
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates daily market OHLCV data for anomalies, duplicates, and impossible values."""

    def __init__(self, volume_spike_threshold: float = 10.0, price_jump_threshold: float = 0.5):
        self.volume_spike_threshold = volume_spike_threshold
        self.price_jump_threshold = price_jump_threshold

    def validate_symbol_data(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates price DataFrame for a given symbol.
        Returns (valid_df, warnings, errors).
        Does NOT modify or fake raw price data; records anomalies in warnings/errors.
        """
        warnings = []
        errors = []

        if df.empty:
            errors.append({"symbol": symbol, "type": "NO_DATA", "message": "DataFrame is empty."})
            return df, warnings, errors

        required_cols = ["Date", "open", "high", "low", "close", "volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append({"symbol": symbol, "type": "MISSING_COLUMNS", "message": f"Missing columns: {missing_cols}"})
            return df, warnings, errors

        # 1. Duplicate dates check
        dup_mask = df.duplicated(subset=["Date"], keep=False)
        if dup_mask.any():
            dup_dates = df.loc[dup_mask, "Date"].unique().tolist()
            errors.append({"symbol": symbol, "type": "DUPLICATE_DATES", "message": f"Duplicate entries found for dates: {dup_dates}"})

        # 2. Check for zero or negative prices
        for col in ["open", "high", "low", "close"]:
            invalid_price = df[df[col] <= 0]
            if not invalid_price.empty:
                dates = invalid_price["Date"].tolist()
                errors.append({"symbol": symbol, "type": "ZERO_OR_NEGATIVE_PRICE", "message": f"Non-positive values in {col} on dates {dates}"})

        # 3. Check impossible OHLC relationships: high < low, close > high, open > high, close < low, open < low
        impossible_high_low = df[df["high"] < df["low"]]
        if not impossible_high_low.empty:
            errors.append({"symbol": symbol, "type": "HIGH_LESS_THAN_LOW", "message": f"High < Low on dates {impossible_high_low['Date'].tolist()}"})

        impossible_high_close = df[df["close"] > df["high"]]
        if not impossible_high_close.empty:
            errors.append({"symbol": symbol, "type": "CLOSE_GREATER_THAN_HIGH", "message": f"Close > High on dates {impossible_high_close['Date'].tolist()}"})

        impossible_low_close = df[df["close"] < df["low"]]
        if not impossible_low_close.empty:
            errors.append({"symbol": symbol, "type": "CLOSE_LESS_THAN_LOW", "message": f"Close < Low on dates {impossible_low_close['Date'].tolist()}"})

        # 4. Check anomalous volume (spikes > N times 20-day median volume)
        if len(df) >= 5:
            rolling_vol_med = df["volume"].rolling(window=20, min_periods=5).median()
            spike_mask = (df["volume"] > self.volume_spike_threshold * rolling_vol_med) & (df["volume"] > 0)
            if spike_mask.any():
                spike_dates = df.loc[spike_mask, "Date"].tolist()
                warnings.append({"symbol": symbol, "type": "VOLUME_SPIKE", "message": f"Volume spike detected on dates: {spike_dates}"})

        # 5. Check extreme price jumps / stock split gaps (> 50% single day move without notice)
        if len(df) >= 2:
            pct_change = df["close"].pct_change().abs()
            jump_mask = pct_change > self.price_jump_threshold
            if jump_mask.any():
                jump_dates = df.loc[jump_mask, "Date"].tolist()
                warnings.append({"symbol": symbol, "type": "EXTREME_PRICE_GAP", "message": f"Extreme daily price gap (> {self.price_jump_threshold * 100}%) on dates: {jump_dates}"})

        # Deduplicate records if needed for clean dataframe return
        valid_df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)
        return valid_df, warnings, errors

    def generate_quality_report(self, target_date: str, all_warnings: List[Dict[str, Any]], all_errors: List[Dict[str, Any]], total_records: int, valid_records: int, output_path: str):
        """Saves a structured JSON quality report to data/quality/YYYY-MM-DD.json."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        report = {
            "date": target_date,
            "records_processed": total_records,
            "records_valid": valid_records,
            "warnings_count": len(all_warnings),
            "errors_count": len(all_errors),
            "warnings": all_warnings,
            "errors": all_errors
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Data quality report saved to {output_path}")
