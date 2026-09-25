"""Data Quality Validation and Reporting."""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates raw and processed market data and generates quality reports."""

    def __init__(self, holidays: Optional[List[str]] = None):
        self.holidays = set(holidays) if holidays else set()

    def validate_df(self, df: pd.DataFrame, ticker: str = "") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate an OHLCV DataFrame for a single ticker/symbol.

        Returns:
            Tuple of (clean_df, validation_summary)
        """
        warnings: List[str] = []
        errors: List[str] = []

        if df.empty:
            errors.append(f"Empty dataset provided for ticker {ticker}")
            summary = {
                "ticker": ticker,
                "records_processed": 0,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }
            return df, summary

        initial_len = len(df)
        clean_df = df.copy()

        # 1. Date validation & deduplication
        if "Date" not in clean_df.columns:
            errors.append(f"Missing required 'Date' column for ticker {ticker}")
            return clean_df, {
                "ticker": ticker,
                "records_processed": initial_len,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        clean_df["Date"] = pd.to_datetime(clean_df["Date"])

        # Check duplicates
        duplicate_mask = clean_df.duplicated(subset=["Date"], keep="first")
        num_duplicates = int(duplicate_mask.sum())
        if num_duplicates > 0:
            warnings.append(f"Found and removed {num_duplicates} duplicate date records for {ticker}")
            clean_df = clean_df[~duplicate_mask]

        clean_df = clean_df.sort_values("Date").reset_index(drop=True)

        # 2. Impossible OHLC logic & non-positive price detection
        for col in ["Open", "High", "Low", "Close"]:
            if col in clean_df.columns:
                invalid_prices = clean_df[clean_df[col] <= 0]
                if not invalid_prices.empty:
                    err_msg = f"Found {len(invalid_prices)} rows with non-positive values in column '{col}' for {ticker}"
                    errors.append(err_msg)

        if all(col in clean_df.columns for col in ["Open", "High", "Low", "Close"]):
            # High < Low check
            high_low_invalid = clean_df[clean_df["High"] < clean_df["Low"]]
            if not high_low_invalid.empty:
                errors.append(f"Found {len(high_low_invalid)} rows where High < Low for {ticker}")

            # High < Open or Close check
            high_open_close_invalid = clean_df[
                (clean_df["High"] < clean_df["Open"]) | (clean_df["High"] < clean_df["Close"])
            ]
            if not high_open_close_invalid.empty:
                errors.append(f"Found {len(high_open_close_invalid)} rows where High < Open or Close for {ticker}")

            # Low > Open or Close check
            low_open_close_invalid = clean_df[
                (clean_df["Low"] > clean_df["Open"]) | (clean_df["Low"] > clean_df["Close"])
            ]
            if not low_open_close_invalid.empty:
                errors.append(f"Found {len(low_open_close_invalid)} rows where Low > Open or Close for {ticker}")

        # 3. Volume anomalies
        if "Volume" in clean_df.columns:
            negative_vol = clean_df[clean_df["Volume"] < 0]
            if not negative_vol.empty:
                errors.append(f"Found {len(negative_vol)} rows with negative volume for {ticker}")

            if len(clean_df) >= 20:
                vol_sma = clean_df["Volume"].rolling(window=20).mean()
                spike_mask = (clean_df["Volume"] > 10 * vol_sma) & (vol_sma > 0)
                num_spikes = int(spike_mask.sum())
                if num_spikes > 0:
                    warnings.append(f"Detected {num_spikes} extreme volume spikes (>10x 20DMA) for {ticker}")

        # 4. Large price gap/split detection
        if "Close" in clean_df.columns and len(clean_df) > 1:
            pct_change = clean_df["Close"].pct_change().abs()
            split_gaps = clean_df[pct_change > 0.4]  # >40% single-day change
            if not split_gaps.empty:
                warnings.append(f"Detected {len(split_gaps)} potential price gaps or split events (>40% change) for {ticker}")

        valid_count = len(clean_df)
        summary = {
            "ticker": ticker,
            "records_processed": initial_len,
            "records_valid": valid_count,
            "warnings": warnings,
            "errors": errors
        }
        return clean_df, summary

    def generate_quality_report(
        self,
        date_str: str,
        summaries: List[Dict[str, Any]],
        output_dir: str = "data/quality"
    ) -> str:
        """Combine ticker validation summaries and write quality report JSON."""
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f"{date_str}.json")

        total_processed = sum(s.get("records_processed", 0) for s in summaries)
        total_valid = sum(s.get("records_valid", 0) for s in summaries)
        all_warnings = [
            f"[{s['ticker']}] {w}"
            for s in summaries
            for w in s.get("warnings", [])
        ]
        all_errors = [
            f"[{s['ticker']}] {e}"
            for s in summaries
            for e in s.get("errors", [])
        ]

        report = {
            "date": date_str,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "warnings": all_warnings,
            "errors": all_errors,
            "summary_by_ticker": summaries
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved data quality report to {report_path}")
        return report_path
