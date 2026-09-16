import os
import json
import logging
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class HistoricalStorage:
    """
    Handles read/write operations for historical datasets in Parquet, CSV, and JSON formats.
    Enforces append/update strategy preventing duplicates and ensuring metadata tagging.
    """

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.quality_dir = os.path.join(base_dir, "quality")

        for d in [
            self.raw_dir,
            self.processed_dir,
            self.features_dir,
            self.analysis_dir,
            self.predictions_dir,
            self.quality_dir,
        ]:
            os.makedirs(d, exist_ok=True)

    def _sanitize_symbol(self, symbol: str) -> str:
        return symbol.replace("^", "INDEX_").replace(".", "_")

    def save_raw_daily(self, date_str: str, symbol: str, df: pd.DataFrame) -> str:
        """
        Saves raw data partitioned by date: data/raw/YYYY/MM/YYYY-MM-DD/SYMBOL.parquet
        """
        dt_parts = date_str.split("-")
        if len(dt_parts) == 3:
            year, month, _ = dt_parts
            target_dir = os.path.join(self.raw_dir, year, month, date_str)
        else:
            target_dir = os.path.join(self.raw_dir, date_str)

        os.makedirs(target_dir, exist_ok=True)
        sanitized = self._sanitize_symbol(symbol)
        parquet_path = os.path.join(target_dir, f"{sanitized}.parquet")
        csv_path = os.path.join(target_dir, f"{sanitized}.csv")

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path

    def update_processed_history(
        self,
        symbol: str,
        new_df: pd.DataFrame,
        category: str = "prices"
    ) -> pd.DataFrame:
        """
        Appends new price records to the cumulative historical dataset for a symbol without duplicates.
        data/processed/{category}/{symbol}.parquet
        """
        cat_dir = os.path.join(self.processed_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        sanitized = self._sanitize_symbol(symbol)
        parquet_path = os.path.join(cat_dir, f"{sanitized}.parquet")
        csv_path = os.path.join(cat_dir, f"{sanitized}.csv")

        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined = new_df.copy()

        # Deduplicate on Date and symbol
        if "Date" in combined.columns:
            combined = combined.drop_duplicates(subset=["Date", "symbol"], keep="last")
            combined = combined.sort_values(by="Date").reset_index(drop=True)

        combined.to_parquet(parquet_path, index=False)
        combined.to_csv(csv_path, index=False)
        return combined

    def load_processed_history(self, symbol: str, category: str = "prices") -> pd.DataFrame:
        sanitized = self._sanitize_symbol(symbol)
        parquet_path = os.path.join(self.processed_dir, category, f"{sanitized}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        csv_path = os.path.join(self.processed_dir, category, f"{sanitized}.csv")
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_quality_report(self, date_str: str, report_data: Dict[str, Any]) -> str:
        filepath = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2)
        return filepath

    def save_daily_analysis_json(self, date_str: str, analysis_data: Dict[str, Any]) -> str:
        daily_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(daily_dir, exist_ok=True)
        filepath = os.path.join(daily_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(analysis_data, f, indent=2)
        return filepath
