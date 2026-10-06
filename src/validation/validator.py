import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

class DataValidator:
    """Validates raw market data and produces structured quality reports."""

    def __init__(self, volume_anomaly_multiplier: float = 10.0, price_gap_threshold: float = 0.20):
        self.volume_anomaly_multiplier = volume_anomaly_multiplier
        self.price_gap_threshold = price_gap_threshold

    def validate_stock_dataframe(self, ticker: str, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates OHLCV DataFrame for a single stock.
        Returns clean valid DataFrame, list of warnings, and list of errors.
        """
        warnings = []
        errors = []

        if df is None or df.empty:
            errors.append({"ticker": ticker, "type": "EMPTY_DATASET", "message": f"No data received for ticker {ticker}"})
            return pd.DataFrame(), warnings, errors

        df = df.copy()

        # Check required columns
        required_cols = {'date', 'open', 'high', 'low', 'close', 'volume'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            errors.append({"ticker": ticker, "type": "MISSING_COLUMNS", "message": f"Missing columns: {missing_cols}"})
            return pd.DataFrame(), warnings, errors

        # Ensure date format
        df['date'] = pd.to_datetime(df['date'])

        # 1. Duplicate detection
        duplicates = df[df.duplicated(subset=['date'], keep=False)]
        if not duplicates.empty:
            errors.append({
                "ticker": ticker,
                "type": "DUPLICATE_DATES",
                "message": f"Found {len(duplicates)} duplicate date records for {ticker}",
                "dates": [d.strftime('%Y-%m-%d') for d in duplicates['date'].unique()]
            })
            df = df.drop_duplicates(subset=['date'], keep='last')

        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)

        # 2. Zero / Negative Price Check
        invalid_prices = df[(df['open'] <= 0) | (df['high'] <= 0) | (df['low'] <= 0) | (df['close'] <= 0)]
        if not invalid_prices.empty:
            errors.append({
                "ticker": ticker,
                "type": "NON_POSITIVE_PRICE",
                "message": f"Found {len(invalid_prices)} rows with zero or negative price",
                "dates": [d.strftime('%Y-%m-%d') for d in invalid_prices['date']]
            })
            df = df[~df.index.isin(invalid_prices.index)]

        # 3. Impossible OHLC logic (High < Low, High < Open, High < Close, Low > Open, Low > Close)
        impossible_ohlc = df[
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        ]
        if not impossible_ohlc.empty:
            errors.append({
                "ticker": ticker,
                "type": "IMPOSSIBLE_OHLC",
                "message": f"Found {len(impossible_ohlc)} rows with impossible OHLC relationships",
                "dates": [d.strftime('%Y-%m-%d') for d in impossible_ohlc['date']]
            })
            df = df[~df.index.isin(impossible_ohlc.index)]

        # 4. Volume Anomaly Check
        if len(df) > 5:
            rolling_med_vol = df['volume'].rolling(window=20, min_periods=5).median().shift(1)
            anomalous_vol = df[(df['volume'] > self.volume_anomaly_multiplier * rolling_med_vol) & (rolling_med_vol > 0)]
            if not anomalous_vol.empty:
                warnings.append({
                    "ticker": ticker,
                    "type": "ANOMALOUS_VOLUME",
                    "message": f"Volume spike > {self.volume_anomaly_multiplier}x 20-day median on {len(anomalous_vol)} dates",
                    "dates": [d.strftime('%Y-%m-%d') for d in anomalous_vol['date']]
                })

        # 5. Price Gap Anomaly (e.g. potential unadjusted split or data error)
        if len(df) > 1:
            price_change = (df['close'] - df['close'].shift(1)).abs() / df['close'].shift(1)
            large_gaps = df[price_change > self.price_gap_threshold]
            if not large_gaps.empty:
                warnings.append({
                    "ticker": ticker,
                    "type": "LARGE_PRICE_GAP",
                    "message": f"Price change > {self.price_gap_threshold * 100}% on {len(large_gaps)} dates",
                    "dates": [d.strftime('%Y-%m-%d') for d in large_gaps['date']]
                })

        return df, warnings, errors

    def generate_quality_report(self, date_str: str, processed_count: int, valid_count: int, all_warnings: List[Dict[str, Any]], all_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates the data quality summary JSON report."""
        return {
            "date": date_str,
            "records_processed": processed_count,
            "records_valid": valid_count,
            "warnings": all_warnings,
            "errors": all_errors
        }
