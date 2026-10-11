import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates raw market data and generates quality reports."""

    def __init__(self, volume_anomaly_std_threshold: float = 5.0):
        self.volume_threshold = volume_anomaly_std_threshold

    def validate_ohlc(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates OHLC data for consistency, missing dates, zero/negative prices,
        volume anomalies, and returns record validation results and warnings.
        """
        if df.empty:
            return {
                "records_processed": 0,
                "records_valid": 0,
                "warnings": ["DataFrame is empty."],
                "errors": ["No records to process."],
                "invalid_dates": []
            }

        warnings = []
        errors = []
        total_records = len(df)
        invalid_indices = set()

        # 1. Check required columns
        req_cols = ["date", "open", "high", "low", "close"]
        for col in req_cols:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
                return {
                    "records_processed": total_records,
                    "records_valid": 0,
                    "warnings": warnings,
                    "errors": errors,
                    "invalid_dates": []
                }

        # 2. Check duplicate dates
        duplicate_dates = df[df.duplicated(subset=["date"], keep=False)]["date"].tolist()
        if duplicate_dates:
            warnings.append(f"Found {len(duplicate_dates)} duplicate date records: {set(duplicate_dates)}")

        # 3. Iterate & check OHLC price logic
        for idx, row in df.iterrows():
            d = row.get("date", "unknown")
            o, h, l, c = row.get("open"), row.get("high"), row.get("low"), row.get("close")

            # Check zero/negative
            if pd.isna(o) or pd.isna(h) or pd.isna(l) or pd.isna(c):
                errors.append(f"NaN price detected on date {d}")
                invalid_indices.add(idx)
                continue

            if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                errors.append(f"Zero or negative price on date {d}: O={o}, H={h}, L={l}, C={c}")
                invalid_indices.add(idx)
                continue

            # Check High/Low bounding
            if h < max(o, c) or l > min(o, c) or h < l:
                errors.append(f"Impossible OHLC prices on date {d}: High={h}, Low={l}, Open={o}, Close={c}")
                invalid_indices.add(idx)
                continue

        # 4. Check Volume Anomalies
        if "volume" in df.columns and len(df) > 10:
            vol_mean = df["volume"].mean()
            vol_std = df["volume"].std()
            if vol_std > 0:
                anomalies = df[df["volume"] > vol_mean + self.volume_threshold * vol_std]
                if not anomalies.empty:
                    warnings.append(
                        f"Detected {len(anomalies)} volume anomaly dates exceeding {self.volume_threshold} std dev."
                    )

        # 5. Check gaps / missing dates in range (optional warning)
        if "date" in df.columns and len(df) > 1:
            try:
                dates = pd.to_datetime(df["date"]).sort_values()
                date_diffs = dates.diff().dt.days
                large_gaps = date_diffs[date_diffs > 10]
                if not large_gaps.empty:
                    warnings.append(f"Detected {len(large_gaps)} trading gaps (>10 calendar days).")
            except Exception as e:
                logger.warning(f"Failed date gap check: {e}")

        invalid_dates = df.loc[list(invalid_indices), "date"].tolist() if invalid_indices else []
        valid_records = total_records - len(invalid_indices)

        return {
            "records_processed": total_records,
            "records_valid": valid_records,
            "warnings": warnings,
            "errors": errors,
            "invalid_dates": invalid_dates
        }

    def create_quality_report(self, date_str: str, stock_validations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidates data validation results into a daily quality report."""
        total_processed = 0
        total_valid = 0
        all_warnings = []
        all_errors = []

        for symbol, val in stock_validations.items():
            total_processed += val.get("records_processed", 0)
            total_valid += val.get("records_valid", 0)
            for w in val.get("warnings", []):
                all_warnings.append(f"[{symbol}] {w}")
            for e in val.get("errors", []):
                all_errors.append(f"[{symbol}] {e}")

        return {
            "date": date_str,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "warnings": all_warnings,
            "errors": all_errors,
            "stock_details": stock_validations
        }
