"""
Storage Manager for persisting raw, processed, feature, analysis, prediction, quality, and report files.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file persistence across raw, processed, features, analysis, predictions, and reports."""

    def __init__(self, base_dir: str = "data", reports_dir: str = "reports"):
        self.base_dir = base_dir
        self.reports_dir = reports_dir
        self._ensure_directories()

    def _ensure_directories(self):
        dirs = [
            os.path.join(self.base_dir, "raw"),
            os.path.join(self.base_dir, "processed", "prices"),
            os.path.join(self.base_dir, "processed", "indices"),
            os.path.join(self.base_dir, "processed", "corporate_actions"),
            os.path.join(self.base_dir, "features", "daily"),
            os.path.join(self.base_dir, "analysis", "daily"),
            os.path.join(self.base_dir, "analysis", "weekly"),
            os.path.join(self.base_dir, "analysis", "monthly"),
            os.path.join(self.base_dir, "predictions", "daily"),
            os.path.join(self.base_dir, "quality"),
            os.path.join(self.reports_dir, "daily"),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, ticker: str, date_str: str) -> str:
        """Saves raw ingested dataframe under data/raw/YYYY/MM/YYYY-MM-DD/ticker.parquet and .csv."""
        dt = pd.to_datetime(date_str)
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        raw_path_dir = os.path.join(self.base_dir, "raw", year, month, date_str)
        os.makedirs(raw_path_dir, exist_ok=True)

        clean_ticker = ticker.replace("^", "").replace(".", "_")
        parquet_path = os.path.join(raw_path_dir, f"{clean_ticker}.parquet")
        csv_path = os.path.join(raw_path_dir, f"{clean_ticker}.csv")

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path

    def update_historical_dataset(
        self, new_df: pd.DataFrame, identifier: str, category: str = "prices"
    ) -> pd.DataFrame:
        """
        Appends new observations to historical dataset without creating duplicate dates.
        Saves under data/processed/{category}/{identifier}.parquet and .csv
        """
        clean_id = identifier.replace("^", "").replace(".", "_")
        processed_dir = os.path.join(self.base_dir, "processed", category)
        os.makedirs(processed_dir, exist_ok=True)

        parquet_path = os.path.join(processed_dir, f"{clean_id}.parquet")
        csv_path = os.path.join(processed_dir, f"{clean_id}.csv")

        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date"], keep="last")
            combined = combined.sort_values("date").reset_index(drop=True)
        else:
            combined = new_df.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)

        combined.to_parquet(parquet_path, index=False)
        combined.to_csv(csv_path, index=False)
        return combined

    def load_historical_dataset(self, identifier: str, category: str = "prices") -> pd.DataFrame:
        """Loads historical dataset for a ticker or index."""
        clean_id = identifier.replace("^", "").replace(".", "_")
        parquet_path = os.path.join(self.base_dir, "processed", category, f"{clean_id}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        return pd.DataFrame()

    def save_features(self, df: pd.DataFrame, date_str: str) -> str:
        """Saves engineered daily feature set."""
        feat_dir = os.path.join(self.base_dir, "features", "daily")
        os.makedirs(feat_dir, exist_ok=True)
        parquet_path = os.path.join(feat_dir, f"{date_str}.parquet")
        csv_path = os.path.join(feat_dir, f"{date_str}.csv")
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path

    def save_quality_report(self, report: Dict[str, Any], date_str: str) -> str:
        """Saves data quality report JSON."""
        path = os.path.join(self.base_dir, "quality", f"{date_str}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return path

    def save_daily_analysis_json(self, data: Dict[str, Any], date_str: str) -> str:
        """Saves machine-readable daily analysis JSON."""
        path = os.path.join(self.base_dir, "analysis", "daily", f"{date_str}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def save_daily_report_md(self, content: str, date_str: str) -> str:
        """Saves human-readable daily report Markdown."""
        path = os.path.join(self.reports_dir, "daily", f"{date_str}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
