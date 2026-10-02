"""
Data Validation Module.
Validates raw stock and index market data and creates quality reports.
"""

import logging
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates daily price, index, and volume data for quality and anomalies."""

    def __init__(self, volume_spike_threshold: float = 5.0, price_gap_threshold: float = 0.20):
        self.volume_spike_threshold = volume_spike_threshold
        self.price_gap_threshold = price_gap_threshold

    def validate_df(self, df: pd.DataFrame, ticker: str = "UNKNOWN") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validates DataFrame records and generates data quality metrics and warnings/errors.
        Returns:
            Tuple of (valid_df, quality_summary)
        """
        summary = {
            "ticker": ticker,
            "records_processed": len(df),
            "records_valid": 0,
            "warnings": [],
            "errors": [],
        }

        if df.empty:
            summary["errors"].append(f"Empty dataset received for {ticker}.")
            return df, summary

        df = df.copy()
        valid_mask = pd.Series(True, index=df.index)

        # Check required columns
        req_cols = ["date", "open", "high", "low", "close"]
        for col in req_cols:
            if col not in df.columns:
                summary["errors"].append(f"Missing required column '{col}' for {ticker}.")
                return pd.DataFrame(), summary

        # 1. Date Validation
        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        invalid_dates = df["date_dt"].isna()
        if invalid_dates.any():
            count = invalid_dates.sum()
            summary["errors"].append(f"Found {count} invalid/unparseable dates.")
            valid_mask &= ~invalid_dates

        # 2. Duplicate Check
        duplicates = df.duplicated(subset=["date"], keep="first")
        if duplicates.any():
            count = duplicates.sum()
            summary["warnings"].append(f"Found {count} duplicate date records. Removing duplicates.")
            valid_mask &= ~duplicates

        # 3. OHLC Value Anomalies (High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close)
        impossible_ohlc = (
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) |
            (df["high"] < df["close"]) |
            (df["low"] > df["open"]) |
            (df["low"] > df["close"])
        )
        if impossible_ohlc.any():
            count = impossible_ohlc.sum()
            summary["errors"].append(f"Found {count} impossible OHLC price relation records.")
            valid_mask &= ~impossible_ohlc

        # 4. Zero / Negative Prices
        zero_neg_prices = (df["open"] <= 0) | (df["high"] <= 0) | (df["low"] <= 0) | (df["close"] <= 0)
        if zero_neg_prices.any():
            count = zero_neg_prices.sum()
            summary["errors"].append(f"Found {count} zero or negative price records.")
            valid_mask &= ~zero_neg_prices

        # Filter valid records
        valid_df = df[valid_mask].sort_values("date_dt").reset_index(drop=True)
        summary["records_valid"] = len(valid_df)

        if len(valid_df) == 0:
            return valid_df, summary

        # 5. Missing Trading Days (Gaps)
        valid_df["date_diff"] = valid_df["date_dt"].diff().dt.days
        gaps = valid_df[valid_df["date_diff"] > 4]  # Weekend is 2-3 days, >4 is likely a holiday or missing gap
        if not gaps.empty:
            summary["warnings"].append(f"Detected {len(gaps)} potential trading day gaps (>4 calendar days).")

        # 6. Volume Spikes
        if "volume" in valid_df.columns:
            mean_vol = valid_df["volume"].rolling(window=20, min_periods=5).mean()
            vol_spikes = (valid_df["volume"] > (mean_vol * self.volume_spike_threshold)) & (mean_vol > 0)
            if vol_spikes.any():
                summary["warnings"].append(f"Detected {vol_spikes.sum()} anomalous volume spikes (> {self.volume_spike_threshold}x 20-day mean).")

        # 7. Extreme Price Gaps / Return Spikes
        valid_df["pct_change"] = valid_df["close"].pct_change().abs()
        price_spikes = valid_df["pct_change"] > self.price_gap_threshold
        if price_spikes.any():
            summary["warnings"].append(f"Detected {price_spikes.sum()} potential stock split / price gap events (> {self.price_gap_threshold * 100:.0f}% daily change).")

        # Drop temporary columns
        if "date_dt" in valid_df.columns:
            valid_df = valid_df.drop(columns=["date_dt", "date_diff", "pct_change"], errors="ignore")

        return valid_df, summary

    def build_quality_report(self, date_str: str, summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidates individual stock summaries into a overall daily quality report."""
        total_processed = sum(s.get("records_processed", 0) for s in summaries)
        total_valid = sum(s.get("records_valid", 0) for s in summaries)
        all_warnings = []
        all_errors = []

        for s in summaries:
            ticker = s.get("ticker", "UNKNOWN")
            for w in s.get("warnings", []):
                all_warnings.append(f"[{ticker}] {w}")
            for e in s.get("errors", []):
                all_errors.append(f"[{ticker}] {e}")

        report = {
            "date": date_str,
            "tickers_processed": len(summaries),
            "records_processed": total_processed,
            "records_valid": total_valid,
            "total_warnings": len(all_warnings),
            "total_errors": len(all_errors),
            "warnings": all_warnings,
            "errors": all_errors,
        }
        return report
