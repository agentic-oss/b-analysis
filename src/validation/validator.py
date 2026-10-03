import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates financial market data (OHLCV) and generates quality reports."""

    def __init__(self, price_anomaly_threshold: float = 0.5):
        self.price_anomaly_threshold = price_anomaly_threshold

    def validate_ohlcv(self, df: pd.DataFrame, ticker: str = "") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        warnings = []
        errors = []

        if df is None or df.empty:
            errors.append(f"Empty data received for {ticker}")
            return pd.DataFrame(), {
                "ticker": ticker,
                "records_processed": 0,
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        required_cols = ["date", "open", "high", "low", "close", "volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns for {ticker}: {missing_cols}")
            return pd.DataFrame(), {
                "ticker": ticker,
                "records_processed": len(df),
                "records_valid": 0,
                "warnings": warnings,
                "errors": errors
            }

        df = df.copy()
        processed_count = len(df)

        # Date validation & duplicate detection
        if df["date"].duplicated().any():
            dup_count = df["date"].duplicated().sum()
            warnings.append(f"Found {dup_count} duplicate dates for {ticker}")
            df = df.drop_duplicates(subset=["date"], keep="last")

        # Sort chronologically
        df = df.sort_values("date").reset_index(drop=True)

        # OHLC logic checks: High >= Max(Open, Close) & Low <= Min(Open, Close)
        invalid_high = df[df["high"] < df[["open", "close"]].max(axis=1)]
        if not invalid_high.empty:
            warnings.append(f"Found {len(invalid_high)} records where High < max(Open, Close) for {ticker}")

        invalid_low = df[df["low"] > df[["open", "close"]].min(axis=1)]
        if not invalid_low.empty:
            warnings.append(f"Found {len(invalid_low)} records where Low > min(Open, Close) for {ticker}")

        # Zero or negative price checks
        price_cols = ["open", "high", "low", "close"]
        zero_neg_prices = df[(df[price_cols] <= 0).any(axis=1)]
        if not zero_neg_prices.empty:
            errors.append(f"Found {len(zero_neg_prices)} records with zero or negative prices for {ticker}")
            # Filter out invalid price rows
            df = df[(df[price_cols] > 0).all(axis=1)]

        # Negative volume checks
        neg_volume = df[df["volume"] < 0]
        if not neg_volume.empty:
            errors.append(f"Found {len(neg_volume)} records with negative volume for {ticker}")
            df = df[df["volume"] >= 0]

        # Price anomaly jump detection (>50% single day move)
        if len(df) > 1:
            returns = df["close"].pct_change().abs()
            anomalies = df[returns > self.price_anomaly_threshold]
            if not anomalies.empty:
                warnings.append(f"Found {len(anomalies)} single-day price changes > {self.price_anomaly_threshold * 100}% for {ticker}")

        valid_count = len(df)
        quality_report = {
            "ticker": ticker,
            "records_processed": processed_count,
            "records_valid": valid_count,
            "warnings": warnings,
            "errors": errors
        }

        return df, quality_report
