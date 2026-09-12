import os
import json
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates raw market data and generates data quality reports without altering raw data."""

    def __init__(self, quality_report_dir: str = "data/quality"):
        self.quality_report_dir = quality_report_dir
        os.makedirs(self.quality_report_dir, exist_ok=True)

    def validate(self, df: pd.DataFrame, ticker: str) -> Dict[str, Any]:
        """
        Validate OHLCV DataFrame for a ticker.
        Returns a dictionary summary of validation results and quality warnings.
        """
        warnings = []
        errors = []

        if df.empty:
            errors.append(f"No records returned for {ticker}")
            return {
                "ticker": ticker,
                "records_processed": 0,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        total_records = len(df)
        invalid_count = 0

        # Check required columns
        req_cols = ["date", "open", "high", "low", "close", "volume"]
        missing_cols = [c for c in req_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return {
                "ticker": ticker,
                "records_processed": total_records,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        # 1. Validate dates & check duplicates
        if df["date"].duplicated().any():
            dup_dates = df[df["date"].duplicated()]["date"].tolist()
            warnings.append(f"Duplicate date records detected: {dup_dates}")
            invalid_count += len(dup_dates)

        # Parse dates to check sorting & missing trading days
        try:
            dates = pd.to_datetime(df["date"]).sort_values()
            date_gaps = (dates.diff().dt.days > 5)
            if date_gaps.any():
                gaps = dates[date_gaps].tolist()
                warnings.append(f"Unexpected date gaps (>5 calendar days) found near: {[g.strftime('%Y-%m-%d') for g in gaps]}")
        except Exception as e:
            errors.append(f"Invalid date format detected: {e}")

        # 2. Check zero/negative prices
        price_cols = ["open", "high", "low", "close"]
        for col in price_cols:
            invalid_prices = df[df[col] <= 0]
            if not invalid_prices.empty:
                errors.append(f"Zero or negative prices in {col}: {len(invalid_prices)} rows")
                invalid_count += len(invalid_prices)

        # 3. Impossible OHLC relationships
        # High must be >= Open, Close, Low
        high_invalid = df[(df["high"] < df["open"]) | (df["high"] < df["close"]) | (df["high"] < df["low"])]
        if not high_invalid.empty:
            errors.append(f"High price lower than Open/Close/Low in {len(high_invalid)} rows")
            invalid_count += len(high_invalid)

        # Low must be <= Open, Close, High
        low_invalid = df[(df["low"] > df["open"]) | (df["low"] > df["close"])]
        if not low_invalid.empty:
            errors.append(f"Low price higher than Open/Close in {len(low_invalid)} rows")
            invalid_count += len(low_invalid)

        # 4. Anomalous volume
        volume_zeros = df[df["volume"] == 0]
        if not volume_zeros.empty:
            warnings.append(f"Zero volume recorded in {len(volume_zeros)} trading sessions")

        # 5. Volatility / Price spikes (e.g. daily return > 50%)
        if "close" in df.columns and len(df) > 1:
            returns = df["close"].pct_change().abs()
            extreme_spikes = df[returns > 0.5]
            if not extreme_spikes.empty:
                warnings.append(f"Extreme single-day price movement (>50%) on dates: {extreme_spikes['date'].tolist()}")

        valid_records = max(0, total_records - invalid_count)

        return {
            "ticker": ticker,
            "records_processed": total_records,
            "records_valid": valid_records,
            "warnings": warnings,
            "errors": errors
        }

    def generate_daily_quality_report(self, date_str: str, ticker_results: List[Dict[str, Any]]) -> str:
        """
        Consolidates quality reports for all tickers on a given date and saves to JSON.
        """
        total_processed = sum(r["records_processed"] for r in ticker_results)
        total_valid = sum(r["records_valid"] for r in ticker_results)
        all_warnings = []
        all_errors = []

        for r in ticker_results:
            ticker = r["ticker"]
            for w in r.get("warnings", []):
                all_warnings.append(f"[{ticker}] {w}")
            for e in r.get("errors", []):
                all_errors.append(f"[{ticker}] {e}")

        report = {
            "date": date_str,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "tickers_checked": len(ticker_results),
            "warnings": all_warnings,
            "errors": all_errors
        }

        report_path = os.path.join(self.quality_report_dir, f"{date_str}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved daily data quality report to {report_path}")
        return report_path
