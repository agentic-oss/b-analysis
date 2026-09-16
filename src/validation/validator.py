from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates OHLCV market data before storage and analysis.
    Performs data quality checks:
    - Date formatting & duplicate dates
    - Missing trading days
    - Non-positive prices (zero/negative)
    - Impossible OHLC logic (High < Low, High < Open/Close, Low > Open/Close)
    - Volume anomalies (negative volume, extreme volume spikes > 10x median)
    - Price return anomalies (> 30% daily jump without split)
    - Records detailed quality metrics & warnings in JSON reports.
    """

    def validate_ohlcv(
        self,
        df: pd.DataFrame,
        symbol: str,
        holidays: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        result = {
            "symbol": symbol,
            "total_records": len(df),
            "valid_records": 0,
            "warnings": [],
            "errors": [],
            "is_valid": True,
        }

        if df.empty:
            result["errors"].append("DataFrame is empty.")
            result["is_valid"] = False
            return result

        req_cols = {"Date", "open", "high", "low", "close", "volume"}
        missing_cols = req_cols - set(df.columns)
        if missing_cols:
            result["errors"].append(f"Missing required columns: {missing_cols}")
            result["is_valid"] = False
            return result

        clean_df = df.copy()

        # 1. Duplicate dates check
        dups = clean_df.duplicated(subset=["Date"])
        if dups.any():
            dup_dates = clean_df.loc[dups, "Date"].tolist()
            result["warnings"].append(f"Duplicate dates found and flagged: {dup_dates}")

        # 2. Non-positive price check
        invalid_prices = clean_df[(clean_df["open"] <= 0) | (clean_df["high"] <= 0) |
                                  (clean_df["low"] <= 0) | (clean_df["close"] <= 0)]
        if not invalid_prices.empty:
            dates = invalid_prices["Date"].tolist()
            result["errors"].append(f"Zero or negative prices on dates: {dates}")
            result["is_valid"] = False

        # 3. Impossible OHLC logic
        # High must be >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
        ohlc_violations = clean_df[
            (clean_df["high"] < clean_df["low"]) |
            (clean_df["high"] < clean_df["open"]) |
            (clean_df["high"] < clean_df["close"]) |
            (clean_df["low"] > clean_df["open"]) |
            (clean_df["low"] > clean_df["close"])
        ]
        if not ohlc_violations.empty:
            dates = ohlc_violations["Date"].tolist()
            result["errors"].append(f"Impossible OHLC relationships on dates: {dates}")
            result["is_valid"] = False

        # 4. Volume checks
        neg_volume = clean_df[clean_df["volume"] < 0]
        if not neg_volume.empty:
            result["errors"].append(f"Negative volume found on dates: {neg_volume['Date'].tolist()}")
            result["is_valid"] = False

        # Extreme volume spikes (> 10x 20-day median)
        median_vol = clean_df["volume"].rolling(20, min_periods=5).median()
        vol_spikes = clean_df[(clean_df["volume"] > 10 * median_vol) & (clean_df["volume"] > 100000)]
        if not vol_spikes.empty:
            result["warnings"].append(f"Anomalous volume spike (>10x median) on dates: {vol_spikes['Date'].tolist()}")

        # 5. Daily return anomalies (> 30% single-day change)
        returns = clean_df["close"].pct_change().abs()
        anomalous_returns = clean_df[returns > 0.30]
        if not anomalous_returns.empty:
            result["warnings"].append(
                f"Large price move (>30%) on dates: {anomalous_returns['Date'].tolist()} (verify split/corporate action)"
            )

        # 6. Missing trading days check
        if len(clean_df) > 5:
            dates_dt = pd.to_datetime(clean_df["Date"]).sort_values()
            all_business_days = pd.date_range(start=dates_dt.min(), end=dates_dt.max(), freq="B")
            if holidays:
                holidays_dt = pd.to_datetime(holidays)
                all_business_days = all_business_days[~all_business_days.isin(holidays_dt)]
            missing = set(all_business_days.strftime("%Y-%m-%d")) - set(dates_dt.dt.strftime("%Y-%m-%d"))
            if len(missing) > 10:
                result["warnings"].append(f"Found {len(missing)} missing expected business trading days.")

        result["valid_records"] = len(clean_df) if result["is_valid"] else 0
        return result

    def generate_quality_report(
        self,
        date_str: str,
        results_by_symbol: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        total_symbols = len(results_by_symbol)
        total_records = sum(r.get("total_records", 0) for r in results_by_symbol.values())
        valid_records = sum(r.get("valid_records", 0) for r in results_by_symbol.values())

        all_warnings = []
        all_errors = []

        for sym, res in results_by_symbol.items():
            for w in res.get("warnings", []):
                all_warnings.append({"symbol": sym, "message": w})
            for e in res.get("errors", []):
                all_errors.append({"symbol": sym, "message": e})

        return {
            "date": date_str,
            "symbols_processed": total_symbols,
            "records_processed": total_records,
            "records_valid": valid_records,
            "warnings_count": len(all_warnings),
            "errors_count": len(all_errors),
            "warnings": all_warnings,
            "errors": all_errors,
        }
