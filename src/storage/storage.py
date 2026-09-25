"""Data Storage Architecture and Persistence."""

import json
import logging
import os
from typing import Any, Dict, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles structured data persistence across Parquet, CSV, and JSON formats."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.reports_dir = os.path.join(base_dir, "reports")
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary data directory structure."""
        dirs = [
            self.raw_dir,
            os.path.join(self.processed_dir, "prices"),
            os.path.join(self.processed_dir, "indices"),
            os.path.join(self.processed_dir, "corporate_actions"),
            os.path.join(self.features_dir, "daily"),
            os.path.join(self.analysis_dir, "daily"),
            os.path.join(self.predictions_dir, "daily"),
            os.path.join(self.reports_dir, "daily"),
            "reports/daily"
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_raw_prices(
        self,
        df: pd.DataFrame,
        symbol: str,
        date_str: str
    ) -> str:
        """Save raw price data for a specific ticker and date."""
        if df.empty:
            return ""
        year, month = date_str.split("-")[0], date_str.split("-")[1]
        raw_path_dir = os.path.join(self.raw_dir, year, month, date_str)
        os.makedirs(raw_path_dir, exist_ok=True)

        clean_sym = symbol.replace("^", "").replace(".", "_")
        csv_path = os.path.join(raw_path_dir, f"{clean_sym}.csv")
        df.to_csv(csv_path, index=False)
        return csv_path

    def update_processed_prices(
        self,
        df: pd.DataFrame,
        symbol: str,
        is_index: bool = False
    ) -> str:
        """Append or update processed historical OHLCV dataset for a ticker/index."""
        if df.empty:
            return ""

        subfolder = "indices" if is_index else "prices"
        clean_sym = symbol.replace("^", "").replace(".", "_")
        parquet_path = os.path.join(self.processed_dir, subfolder, f"{clean_sym}.parquet")
        csv_path = os.path.join(self.processed_dir, subfolder, f"{clean_sym}.csv")

        df = df.copy()
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])

        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            existing_df["Date"] = pd.to_datetime(existing_df["Date"])
            combined = pd.concat([existing_df, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["Date"], keep="last")
            combined = combined.sort_values("Date").reset_index(drop=True)
        else:
            combined = df.sort_values("Date").reset_index(drop=True)

        combined.to_parquet(parquet_path, index=False)
        combined.to_csv(csv_path, index=False)
        return parquet_path

    def load_processed_prices(self, symbol: str, is_index: bool = False) -> pd.DataFrame:
        """Load processed price DataFrame for a symbol."""
        subfolder = "indices" if is_index else "prices"
        clean_sym = symbol.replace("^", "").replace(".", "_")
        parquet_path = os.path.join(self.processed_dir, subfolder, f"{clean_sym}.parquet")

        if os.path.exists(parquet_path):
            df = pd.read_parquet(parquet_path)
            df["Date"] = pd.to_datetime(df["Date"])
            return df

        csv_path = os.path.join(self.processed_dir, subfolder, f"{clean_sym}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df["Date"] = pd.to_datetime(df["Date"])
            return df

        return pd.DataFrame()

    def save_features(self, df: pd.DataFrame, date_str: str) -> str:
        """Save daily engineered feature dataset."""
        if df.empty:
            return ""
        parquet_path = os.path.join(self.features_dir, "daily", f"{date_str}.parquet")
        csv_path = os.path.join(self.features_dir, "daily", f"{date_str}.csv")
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path

    def load_features(self, date_str: str) -> pd.DataFrame:
        """Load daily features DataFrame for a date."""
        parquet_path = os.path.join(self.features_dir, "daily", f"{date_str}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        csv_path = os.path.join(self.features_dir, "daily", f"{date_str}.csv")
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_analysis_json(self, data: Dict[str, Any], date_str: str) -> str:
        """Save machine-readable daily analysis JSON."""
        file_path = os.path.join(self.analysis_dir, "daily", f"{date_str}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return file_path

    def load_analysis_json(self, date_str: str) -> Dict[str, Any]:
        """Load machine-readable daily analysis JSON."""
        file_path = os.path.join(self.analysis_dir, "daily", f"{date_str}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_report_md(self, content: str, date_str: str) -> str:
        """Save human-readable Markdown report."""
        file_path = os.path.join("reports", "daily", f"{date_str}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path
