"""
Storage Manager for multi-tiered directory structure and dataset persistence.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Handles read/write operations for raw, processed, features, analysis, predictions, and reports datasets.
    Supports Parquet, CSV, and JSON outputs with metadata tagging.
    """

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.reports_dir = "reports/daily"
        self.quality_dir = os.path.join(base_dir, "quality")

        self._ensure_directories()

    def _ensure_directories(self):
        dirs = [
            self.raw_dir,
            self.processed_dir,
            os.path.join(self.processed_dir, "prices"),
            os.path.join(self.processed_dir, "indices"),
            os.path.join(self.processed_dir, "corporate_actions"),
            self.features_dir,
            os.path.join(self.features_dir, "daily"),
            self.analysis_dir,
            os.path.join(self.analysis_dir, "daily"),
            os.path.join(self.analysis_dir, "weekly"),
            os.path.join(self.analysis_dir, "monthly"),
            self.predictions_dir,
            os.path.join(self.predictions_dir, "daily"),
            self.reports_dir,
            self.quality_dir
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, ticker: str, run_date: str) -> str:
        """
        Saves raw data partitioned by YYYY/MM/YYYY-MM-DD.
        """
        if df.empty:
            return ""
        year, month = run_date.split("-")[0], run_date.split("-")[1]
        target_dir = os.path.join(self.raw_dir, year, month, run_date)
        os.makedirs(target_dir, exist_ok=True)

        filepath = os.path.join(target_dir, f"{ticker}.parquet")
        df.to_parquet(filepath, index=False)

        # CSV fallback export for inspection
        csv_path = os.path.join(target_dir, f"{ticker}.csv")
        df.to_csv(csv_path, index=False)

        return filepath

    def save_processed_prices(self, df: pd.DataFrame, ticker: str) -> str:
        """
        Appends/updates cumulative historical processed price dataset per ticker.
        """
        if df.empty:
            return ""
        target_dir = os.path.join(self.processed_dir, "prices")
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{ticker}.parquet")

        if os.path.exists(filepath):
            existing_df = pd.read_parquet(filepath)
            combined = pd.concat([existing_df, df], ignore_index=True)
            # Deduplicate by Date
            if "Date" in combined.columns:
                combined = combined.drop_duplicates(subset=["Date"], keep="last")
            combined = combined.sort_values("Date").reset_index(drop=True)
            combined.to_parquet(filepath, index=False)
        else:
            df.to_parquet(filepath, index=False)

        return filepath

    def get_processed_prices(self, ticker: str) -> pd.DataFrame:
        """
        Retrieves processed prices for a given ticker.
        """
        filepath = os.path.join(self.processed_dir, "prices", f"{ticker}.parquet")
        if os.path.exists(filepath):
            return pd.read_parquet(filepath)
        return pd.DataFrame()

    def save_features(self, df: pd.DataFrame, run_date: str) -> str:
        """
        Saves daily computed feature matrix.
        """
        target_dir = os.path.join(self.features_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{run_date}.parquet")
        df.to_parquet(filepath, index=False)

        csv_path = os.path.join(target_dir, f"{run_date}.csv")
        df.to_csv(csv_path, index=False)

        return filepath

    def save_daily_analysis(self, data: Dict[str, Any], run_date: str) -> str:
        """
        Saves machine-readable daily analysis JSON output.
        """
        target_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{run_date}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def save_daily_report(self, markdown_content: str, run_date: str) -> str:
        """
        Saves human-readable daily Markdown report.
        """
        os.makedirs(self.reports_dir, exist_ok=True)
        filepath = os.path.join(self.reports_dir, f"{run_date}.md")
        with open(filepath, "w") as f:
            f.write(markdown_content)
        return filepath
