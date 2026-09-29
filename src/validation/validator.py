"""
Data Validation module for market data quality checks.
"""
import os
import json
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates market price data against sanity rules and generates quality reports.
    """

    def __init__(self, quality_dir: str = "data/quality"):
        self.quality_dir = quality_dir
        os.makedirs(self.quality_dir, exist_ok=True)

    def validate_dataframe(self, df: pd.DataFrame, ticker: str = "UNKNOWN") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validates OHLCV dataframe for sanity, duplicates, missing trading days, zero/negative prices,
        and unusual gaps.

        Returns:
            (cleaned_df, validation_summary)
        """
        warnings = []
        errors = []
        records_processed = len(df)

        if df is None or df.empty:
            errors.append(f"Empty dataframe for ticker {ticker}")
            return pd.DataFrame(), {
                "ticker": ticker,
                "records_processed": 0,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        valid_df = df.copy()

        # 1. Date validation & deduplication
        if "Date" in valid_df.columns:
            duplicates = valid_df.duplicated(subset=["Date"], keep="last")
            dup_count = int(duplicates.sum())
            if dup_count > 0:
                warnings.append(f"Found and removed {dup_count} duplicate Date records for {ticker}")
                valid_df = valid_df[~duplicates]

            valid_df["Date"] = pd.to_datetime(valid_df["Date"])
            valid_df = valid_df.sort_values("Date").reset_index(drop=True)

            # Check gaps (more than 5 calendar days between trading days)
            date_diffs = valid_df["Date"].diff().dt.days
            large_gaps = date_diffs[date_diffs > 5]
            if not large_gaps.empty:
                warnings.append(f"Detected {len(large_gaps)} trading gaps (>5 days) for {ticker}")

            valid_df["Date"] = valid_df["Date"].dt.strftime("%Y-%m-%d")

        # 2. Impossible OHLC values & zero/negative price checks
        price_cols = [c for c in ["open", "high", "low", "close", "adj_close"] if c in valid_df.columns]
        invalid_rows = set()

        for idx, row in valid_df.iterrows():
            # Zero or negative prices
            for col in price_cols:
                val = row[col]
                if pd.isna(val) or val <= 0:
                    errors.append(f"Invalid price value {val} in column '{col}' at index {idx} for {ticker}")
                    invalid_rows.add(idx)

            # High/Low/Open/Close sanity: High must be >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
            if "high" in row and "low" in row:
                if row["high"] < row["low"]:
                    errors.append(f"High price ({row['high']}) < Low price ({row['low']}) at index {idx} for {ticker}")
                    invalid_rows.add(idx)
            if "high" in row and "open" in row and row["high"] < row["open"]:
                errors.append(f"High price ({row['high']}) < Open price ({row['open']}) at index {idx} for {ticker}")
                invalid_rows.add(idx)
            if "high" in row and "close" in row and row["high"] < row["close"]:
                errors.append(f"High price ({row['high']}) < Close price ({row['close']}) at index {idx} for {ticker}")
                invalid_rows.add(idx)

        # 3. Volume sanity
        if "volume" in valid_df.columns:
            negative_vol = valid_df[valid_df["volume"] < 0]
            if not negative_vol.empty:
                errors.append(f"Found {len(negative_vol)} records with negative volume for {ticker}")
                invalid_rows.update(negative_vol.index.tolist())

            # Anomalous volume spike (> 20x 20-day moving average volume)
            vol_ma = valid_df["volume"].rolling(window=20, min_periods=5).mean()
            vol_spikes = valid_df[(valid_df["volume"] > 20 * vol_ma) & (valid_df["volume"] > 100000)]
            if not vol_spikes.empty:
                warnings.append(f"Detected {len(vol_spikes)} anomalous volume spikes (>20x 20DMA) for {ticker}")

        # Filter out invalid rows (keeping raw data unmodified elsewhere, but cleaning dataset for pipeline downstream)
        clean_df = valid_df.drop(index=list(invalid_rows)).reset_index(drop=True)
        records_valid = len(clean_df)

        summary = {
            "ticker": ticker,
            "records_processed": records_processed,
            "records_valid": records_valid,
            "warnings": warnings,
            "errors": errors
        }

        return clean_df, summary

    def generate_quality_report(self, run_date: str, ticker_summaries: List[Dict[str, Any]]) -> str:
        """
        Consolidates summaries into a daily quality report saved to data/quality/YYYY-MM-DD.json.
        """
        total_processed = sum(s.get("records_processed", 0) for s in ticker_summaries)
        total_valid = sum(s.get("records_valid", 0) for s in ticker_summaries)
        all_warnings = []
        all_errors = []

        for s in ticker_summaries:
            for w in s.get("warnings", []):
                all_warnings.append(f"[{s.get('ticker')}] {w}")
            for e in s.get("errors", []):
                all_errors.append(f"[{s.get('ticker')}] {e}")

        report = {
            "date": run_date,
            "tickers_checked": len(ticker_summaries),
            "records_processed": total_processed,
            "records_valid": total_valid,
            "warnings_count": len(all_warnings),
            "errors_count": len(all_errors),
            "warnings": all_warnings,
            "errors": all_errors,
            "details": ticker_summaries
        }

        filepath = os.path.join(self.quality_dir, f"{run_date}.json")
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved data quality report to {filepath}")
        return filepath
