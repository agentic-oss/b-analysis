import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validates market price data and generates structured quality reports.
    Does NOT modify raw data to hide errors.
    """

    def validate_price_data(self, df: pd.DataFrame, date_str: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a DataFrame of stock price records.
        Returns:
            is_valid (bool): True if no fatal errors.
            warnings (List[str]): List of data quality warnings.
            errors (List[str]): List of data quality errors.
        """
        warnings = []
        errors = []

        if df.empty:
            errors.append("DataFrame is empty")
            return False, warnings, errors

        # Check required columns
        required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return False, warnings, errors

        # 1. Check duplicate records (symbol + date)
        duplicates = df[df.duplicated(subset=['symbol', 'date'], keep=False)]
        if not duplicates.empty:
            symbols = duplicates['symbol'].unique().tolist()
            errors.append(f"Duplicate records found for symbols: {symbols}")

        # 2. Check zero or negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            invalid_prices = df[df[col] <= 0]
            if not invalid_prices.empty:
                syms = invalid_prices['symbol'].unique().tolist()
                errors.append(f"Zero or negative {col} price detected for symbols: {syms}")

        # 3. Check impossible OHLC relationships
        # High must be >= Open, Low, Close
        # Low must be <= Open, High, Close
        impossible_high = df[(df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close'])]
        if not impossible_high.empty:
            syms = impossible_high['symbol'].unique().tolist()
            errors.append(f"Impossible High price relationship detected for symbols: {syms}")

        impossible_low = df[(df['low'] > df['high']) | (df['low'] > df['open']) | (df['low'] > df['close'])]
        if not impossible_low.empty:
            syms = impossible_low['symbol'].unique().tolist()
            errors.append(f"Impossible Low price relationship detected for symbols: {syms}")

        # 4. Check anomalous volume (e.g. negative volume)
        if 'volume' in df.columns:
            negative_vol = df[df['volume'] < 0]
            if not negative_vol.empty:
                syms = negative_vol['symbol'].unique().tolist()
                errors.append(f"Negative volume detected for symbols: {syms}")

            # Extremely high volume spike check (> 20x average volume for that symbol if full history available)
            for symbol, group in df.groupby('symbol'):
                if len(group) >= 10:
                    avg_vol = group['volume'].mean()
                    if avg_vol > 0:
                        spikes = group[group['volume'] > 20 * avg_vol]
                        if not spikes.empty:
                            warnings.append(f"Unusual volume spike (>20x avg) detected for symbol {symbol}")

        # 5. Price gaps / split check (e.g. >50% price movement in a single day)
        for symbol, group in df.groupby('symbol'):
            if len(group) > 1:
                group = group.sort_values('date')
                pct_change = group['close'].pct_change().abs()
                large_gaps = group[pct_change > 0.50]
                if not large_gaps.empty:
                    gap_dates = large_gaps['date'].tolist()
                    warnings.append(f"Large price move (>50%) detected for symbol {symbol} on dates {gap_dates} - check corporate actions/splits")

        is_valid = len(errors) == 0
        return is_valid, warnings, errors

    def generate_quality_report(self, date_str: str, total_records: int, valid_records: int, warnings: List[str], errors: List[str]) -> Dict[str, Any]:
        """
        Create a standardized quality report dict.
        """
        return {
            "date": date_str,
            "records_processed": total_records,
            "records_valid": valid_records,
            "warnings": warnings,
            "errors": errors
        }
