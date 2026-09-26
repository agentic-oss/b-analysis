"""
Data validation and data quality report generator module.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates financial market data for errors, anomalies, and quality metrics."""

    def __init__(self, volume_spike_threshold: float = 10.0, price_gap_threshold: float = 0.20):
        self.volume_spike_threshold = volume_spike_threshold
        self.price_gap_threshold = price_gap_threshold

    def validate_stock_dataframe(self, symbol: str, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates OHLCV DataFrame for a single stock.
        Returns (df, warnings, errors) without silently altering raw values.
        """
        warnings = []
        errors = []

        if df.empty:
            errors.append({
                "symbol": symbol,
                "type": "EMPTY_DATA",
                "message": f"DataFrame for {symbol} is empty."
            })
            return df, warnings, errors

        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append({
                "symbol": symbol,
                "type": "MISSING_COLUMNS",
                "message": f"Missing required columns {missing_cols} for {symbol}."
            })
            return df, warnings, errors

        # 1. Date Validation & Duplicate Detection
        duplicates = df[df.duplicated(subset=["Date"], keep=False)]
        if not duplicates.empty:
            errors.append({
                "symbol": symbol,
                "type": "DUPLICATE_DATES",
                "message": f"Found {len(duplicates)} duplicate date records for {symbol}."
            })

        # 2. Check for Non-positive Prices
        for col in ["Open", "High", "Low", "Close"]:
            invalid_prices = df[df[col] <= 0]
            if not invalid_prices.empty:
                errors.append({
                    "symbol": symbol,
                    "type": "NON_POSITIVE_PRICE",
                    "message": f"{len(invalid_prices)} rows have non-positive prices in {col} for {symbol}."
                })

        # 3. Impossible OHLC Relationships
        # High must be >= Open, Low, Close
        bad_high = df[(df["High"] < df["Open"]) | (df["High"] < df["Low"]) | (df["High"] < df["Close"])]
        if not bad_high.empty:
            errors.append({
                "symbol": symbol,
                "type": "IMPOSSIBLE_HIGH",
                "message": f"{len(bad_high)} rows have High price lower than Open/Low/Close for {symbol}."
            })

        # Low must be <= Open, High, Close
        bad_low = df[(df["Low"] > df["Open"]) | (df["Low"] > df["High"]) | (df["Low"] > df["Close"])]
        if not bad_low.empty:
            errors.append({
                "symbol": symbol,
                "type": "IMPOSSIBLE_LOW",
                "message": f"{len(bad_low)} rows have Low price higher than Open/High/Close for {symbol}."
            })

        # 4. Zero / Anomalous Volume Detection
        zero_vol = df[df["Volume"] == 0]
        if not zero_vol.empty:
            warnings.append({
                "symbol": symbol,
                "type": "ZERO_VOLUME",
                "message": f"{len(zero_vol)} trading sessions have zero volume for {symbol}."
            })

        if len(df) >= 20:
            vol_sma = df["Volume"].rolling(20).mean()
            vol_spikes = df[df["Volume"] > (vol_sma * self.volume_spike_threshold)]
            if not vol_spikes.empty:
                warnings.append({
                    "symbol": symbol,
                    "type": "VOLUME_SPIKE",
                    "message": f"{len(vol_spikes)} rows with volume > {self.volume_spike_threshold}x 20DMA for {symbol}."
                })

        # 5. Price Gaps & Unadjusted Splits Detection
        if len(df) > 1:
            returns = df["Close"].pct_change().abs()
            large_gaps = df[returns > self.price_gap_threshold]
            if not large_gaps.empty:
                warnings.append({
                    "symbol": symbol,
                    "type": "LARGE_PRICE_GAP",
                    "message": f"{len(large_gaps)} sessions with > {int(self.price_gap_threshold*100)}% price gap for {symbol}."
                })

        return df, warnings, errors


class QualityReportGenerator:
    """Consolidates market data validation results into structured JSON quality reports."""

    def __init__(self, run_date: str):
        self.run_date = run_date
        self.records_processed = 0
        self.records_valid = 0
        self.warnings: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

    def add_validation_result(self, symbol: str, df: pd.DataFrame, warnings: List[Dict[str, Any]], errors: List[Dict[str, Any]]):
        count = len(df)
        self.records_processed += count
        if not errors:
            self.records_valid += count
        else:
            # Deduct rows in error
            self.records_valid += max(0, count - len(errors))

        self.warnings.extend(warnings)
        self.errors.extend(errors)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.run_date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "records_processed": self.records_processed,
            "records_valid": self.records_valid,
            "total_warnings": len(self.warnings),
            "total_errors": len(self.errors),
            "warnings": self.warnings,
            "errors": self.errors
        }
