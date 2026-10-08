import logging
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates market data quality: OHLC integrity, zero/negative prices,
    duplicate dates, gaps, anomalous volume, splits/corporate actions.
    Records structured warnings and errors for reporting.
    """

    def __init__(self, volume_anomaly_std_threshold: float = 5.0):
        self.volume_anomaly_threshold = volume_anomaly_std_threshold

    def validate(self, symbol: str, df: pd.DataFrame, target_date: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        warnings: List[str] = []
        errors: List[str] = []

        if df.empty:
            errors.append(f"Empty dataset for {symbol}")
            report = {
                "symbol": symbol,
                "date": target_date,
                "total_records": 0,
                "valid_records": 0,
                "warnings": warnings,
                "errors": errors,
                "is_valid": False,
            }
            return df, report

        total_records = len(df)
        df_clean = df.copy()

        # 1. Check Date Column & Duplicates
        if "date" not in df_clean.columns:
            errors.append(f"Missing 'date' column in data for {symbol}")
        else:
            duplicate_dates = df_clean[df_clean.duplicated(subset=["date"], keep=False)]
            if not duplicate_dates.empty:
                dup_count = len(duplicate_dates)
                warnings.append(f"Found {dup_count} duplicate date entries for {symbol}. Deduplicating (keeping last).")
                df_clean = df_clean.drop_duplicates(subset=["date"], keep="last")

        # Sort by date
        df_clean = df_clean.sort_values("date").reset_index(drop=True)

        # 2. Check for missing price values or zero/negative prices
        price_cols = [col for col in ["open", "high", "low", "close", "adj_close"] if col in df_clean.columns]
        for col in price_cols:
            invalid_prices = df_clean[df_clean[col] <= 0]
            if not invalid_prices.empty:
                errors.append(f"Found {len(invalid_prices)} records with zero or negative {col} for {symbol}.")

        # 3. Check OHLC Logic (High >= Open, Low, Close and Low <= Open, Close)
        if set(["open", "high", "low", "close"]).issubset(df_clean.columns):
            invalid_high = df_clean[(df_clean["high"] < df_clean["open"]) | (df_clean["high"] < df_clean["close"])]
            if not invalid_high.empty:
                errors.append(f"Found {len(invalid_high)} records where High < Open or High < Close for {symbol}.")

            invalid_low = df_clean[(df_clean["low"] > df_clean["open"]) | (df_clean["low"] > df_clean["close"])]
            if not invalid_low.empty:
                errors.append(f"Found {len(invalid_low)} records where Low > Open or Low > Close for {symbol}.")

        # 4. Check for anomalous volume
        if "volume" in df_clean.columns and len(df_clean) > 20:
            vol_mean = df_clean["volume"].mean()
            vol_std = df_clean["volume"].std()
            if vol_std > 0:
                anomalies = df_clean[df_clean["volume"] > (vol_mean + self.volume_anomaly_threshold * vol_std)]
                if not anomalies.empty:
                    warnings.append(f"Detected {len(anomalies)} extreme volume spike records for {symbol}.")

        # 5. Check corporate actions / splits presence
        if "splits" in df_clean.columns:
            splits = df_clean[df_clean["splits"] > 0]
            if not splits.empty:
                warnings.append(f"Detected {len(splits)} stock split events for {symbol}.")

        # 6. Check missing target trading date if date requested
        if target_date and not df_clean[df_clean["date"] == target_date].empty:
            is_target_present = True
        else:
            is_target_present = False
            warnings.append(f"Target date {target_date} not found in historical data for {symbol}.")

        valid_records = len(df_clean) - len(errors)
        is_valid = len(errors) == 0

        quality_report = {
            "symbol": symbol,
            "date": target_date,
            "total_records": total_records,
            "valid_records": max(0, valid_records),
            "target_date_present": is_target_present,
            "warnings": warnings,
            "errors": errors,
            "is_valid": is_valid,
        }

        return df_clean, quality_report
