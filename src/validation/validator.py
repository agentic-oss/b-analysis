"""
Data validator for market data records and data quality reporting.
"""
import datetime
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates daily OHLCV stock price data and generates data-quality reports."""

    def validate_dataframe(
        self, df: pd.DataFrame, symbol: str
    ) -> Tuple[pd.DataFrame, List[str], List[str]]:
        """
        Validates OHLCV dataframe for a given symbol.
        Returns:
            clean_df: DataFrame with invalid rows removed/handled where appropriate
            warnings: List of data quality warnings
            errors: List of data quality errors
        """
        warnings = []
        errors = []

        if df is None or df.empty:
            errors.append(f"No data available for symbol {symbol}")
            return pd.DataFrame(), warnings, errors

        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"{symbol}: Missing required columns {missing_cols}")
            return pd.DataFrame(), warnings, errors

        df = df.copy()

        # 1. Date Validation & Duplicate Detection
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        duplicates = df[df.duplicated(subset=["Date"], keep=False)]
        if not duplicates.empty:
            warnings.append(
                f"{symbol}: Found {len(duplicates)} duplicate date records. Retaining last."
            )
            df = df.drop_duplicates(subset=["Date"], keep="last")

        df = df.sort_values("Date").reset_index(drop=True)

        valid_mask = pd.Series(True, index=df.index)

        # 2. Check for zero or negative prices
        price_cols = ["Open", "High", "Low", "Close"]
        for col in price_cols:
            invalid_prices = df[df[col] <= 0]
            if not invalid_prices.empty:
                errors.append(
                    f"{symbol}: Found {len(invalid_prices)} rows with zero or negative {col}."
                )
                valid_mask = valid_mask & (df[col] > 0)

        # 3. Check impossible OHLC logic (Low <= Open, Close, High and High >= Open, Close, Low)
        impossible_ohlc = df[
            (df["Low"] > df["High"])
            | (df["Low"] > df["Open"])
            | (df["Low"] > df["Close"])
            | (df["High"] < df["Open"])
            | (df["High"] < df["Close"])
        ]
        if not impossible_ohlc.empty:
            errors.append(
                f"{symbol}: Found {len(impossible_ohlc)} rows with impossible OHLC relationship."
            )
            valid_mask = valid_mask & ~(
                (df["Low"] > df["High"])
                | (df["Low"] > df["Open"])
                | (df["Low"] > df["Close"])
                | (df["High"] < df["Open"])
                | (df["High"] < df["Close"])
            )

        # 4. Check negative volume
        negative_vol = df[df["Volume"] < 0]
        if not negative_vol.empty:
            warnings.append(f"{symbol}: Found {len(negative_vol)} rows with negative volume.")
            df.loc[df["Volume"] < 0, "Volume"] = 0

        # 5. Check extreme price jumps / potential unadjusted splits or errors (> 50% single day move)
        if len(df) > 1:
            pct_change = df["Close"].pct_change().abs()
            extreme_jumps = df[pct_change > 0.5]
            if not extreme_jumps.empty:
                for idx, row in extreme_jumps.iterrows():
                    warnings.append(
                        f"{symbol}: Large price change (>50%) detected on date {row['Date']}."
                    )

        # Filter invalid rows
        clean_df = df[valid_mask].reset_index(drop=True)
        return clean_df, warnings, errors

    def generate_quality_report(
        self,
        date_str: str,
        total_symbols: int,
        valid_symbols: int,
        warnings: List[str],
        errors: List[str],
    ) -> Dict[str, Any]:
        """Generates structured quality report output."""
        return {
            "date": date_str,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "records_processed": total_symbols,
            "records_valid": valid_symbols,
            "warnings_count": len(warnings),
            "errors_count": len(errors),
            "warnings": warnings,
            "errors": errors,
        }
