"""
Data validation module for Indian stock market OHLCV data.
Validates prices, volumes, dates, price anomalies, and missing trading days.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np


class DataValidator:
    """
    Validates OHLCV DataFrame for a stock or index and generates a data quality report.
    """

    def __init__(
        self,
        max_daily_return_pct: float = 0.50, # 50% single-day change threshold warning
        max_volume_spike_factor: float = 20.0, # 20x 20-day SMA volume spike warning
    ):
        self.max_daily_return_pct = max_daily_return_pct
        self.max_volume_spike_factor = max_volume_spike_factor

    def validate_df(self, df: pd.DataFrame, ticker: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validates OHLCV dataframe.
        Returns cleaned/filtered dataframe and a validation summary report.
        Does NOT fabricate or alter raw values to hide errors, but can filter out invalid records.
        """
        warnings = []
        errors = []

        if df is None or df.empty:
            errors.append(f"Empty or None DataFrame provided for ticker {ticker}")
            return pd.DataFrame(), {
                "records_processed": 0,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors,
            }

        total_records = len(df)
        valid_df = df.copy()

        # Ensure Date column is datetime
        if "Date" in valid_df.columns:
            valid_df["Date"] = pd.to_datetime(valid_df["Date"])

        # 1. Duplicate check
        if "Date" in valid_df.columns:
            dups = valid_df.duplicated(subset=["Date"], keep="first")
            num_dups = dups.sum()
            if num_dups > 0:
                warnings.append(f"{ticker}: Found {num_dups} duplicate date records. Retaining first occurrences.")
                valid_df = valid_df[~dups]

        # Sort by date
        if "Date" in valid_df.columns:
            valid_df = valid_df.sort_values("Date").reset_index(drop=True)

        # 2. Check for zero or negative prices
        invalid_prices = (
            (valid_df["Open"] <= 0)
            | (valid_df["High"] <= 0)
            | (valid_df["Low"] <= 0)
            | (valid_df["Close"] <= 0)
        )
        num_invalid_prices = invalid_prices.sum()
        if num_invalid_prices > 0:
            errors.append(f"{ticker}: Found {num_invalid_prices} records with zero or negative OHLC prices.")
            valid_df = valid_df[~invalid_prices]

        # 3. Check High < Low, High < Open/Close, Low > Open/Close
        ohlc_inconsistent = (
            (valid_df["High"] < valid_df["Low"])
            | (valid_df["High"] < valid_df["Open"])
            | (valid_df["High"] < valid_df["Close"])
            | (valid_df["Low"] > valid_df["Open"])
            | (valid_df["Low"] > valid_df["Close"])
        )
        num_inconsistent = ohlc_inconsistent.sum()
        if num_inconsistent > 0:
            errors.append(f"{ticker}: Found {num_inconsistent} records with High/Low inconsistent with Open/Close.")
            valid_df = valid_df[~ohlc_inconsistent]

        # 4. Negative volume check
        neg_volume = valid_df["Volume"] < 0
        num_neg_volume = neg_volume.sum()
        if num_neg_volume > 0:
            errors.append(f"{ticker}: Found {num_neg_volume} records with negative volume.")
            valid_df = valid_df[~neg_volume]

        # 5. Daily return anomalies
        if len(valid_df) > 1:
            returns = valid_df["Close"].pct_change().abs()
            anomalous_returns = returns > self.max_daily_return_pct
            if anomalous_returns.sum() > 0:
                dates_anomalous = valid_df.loc[anomalous_returns, "Date"].dt.strftime("%Y-%m-%d").tolist()
                warnings.append(f"{ticker}: Found extreme daily price change (> {self.max_daily_return_pct*100}%) on dates: {dates_anomalous}")

        # 6. Check for volume spikes
        if len(valid_df) >= 20:
            vol_sma = valid_df["Volume"].rolling(20).mean()
            vol_spikes = valid_df["Volume"] > (vol_sma * self.max_volume_spike_factor)
            if vol_spikes.sum() > 0:
                dates_spikes = valid_df.loc[vol_spikes, "Date"].dt.strftime("%Y-%m-%d").tolist()
                warnings.append(f"{ticker}: Found extreme volume spike (> {self.max_volume_spike_factor}x 20-day SMA) on dates: {dates_spikes}")

        # 7. Check date gaps (> 5 calendar days gap, excluding long weekends/holidays)
        if len(valid_df) > 1:
            date_diffs = (valid_df["Date"] - valid_df["Date"].shift(1)).dt.days
            large_gaps = date_diffs > 7
            if large_gaps.sum() > 0:
                gap_dates = valid_df.loc[large_gaps, "Date"].dt.strftime("%Y-%m-%d").tolist()
                warnings.append(f"{ticker}: Found data gaps greater than 7 calendar days before dates: {gap_dates}")

        report = {
            "ticker": ticker,
            "records_processed": total_records,
            "records_valid": len(valid_df),
            "warnings": warnings,
            "errors": errors,
        }

        return valid_df, report

    @staticmethod
    def create_daily_quality_report(date_str: str, validation_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combines individual validation reports into a daily summary report structure.
        """
        total_processed = sum(r.get("records_processed", 0) for r in validation_reports)
        total_valid = sum(r.get("records_valid", 0) for r in validation_reports)
        all_warnings = []
        all_errors = []

        for r in validation_reports:
            all_warnings.extend(r.get("warnings", []))
            all_errors.extend(r.get("errors", []))

        return {
            "date": date_str,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "warnings": all_warnings,
            "errors": all_errors,
        }
