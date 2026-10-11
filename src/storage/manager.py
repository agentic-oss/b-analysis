import os
import json
import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages raw, processed, feature, analysis, prediction, and report dataset storage."""

    def __init__(self, base_dir: str = "data", config_path: str = "config/config.json"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.reports_dir = "reports"
        self.quality_dir = os.path.join(base_dir, "quality")
        self._ensure_directories()

    def _ensure_directories(self):
        dirs = [
            self.raw_dir,
            os.path.join(self.processed_dir, "prices"),
            os.path.join(self.processed_dir, "indices"),
            os.path.join(self.processed_dir, "corporate_actions"),
            os.path.join(self.features_dir, "daily"),
            os.path.join(self.analysis_dir, "daily"),
            os.path.join(self.predictions_dir, "daily"),
            os.path.join(self.reports_dir, "daily"),
            self.quality_dir,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_raw_price_data(self, df: pd.DataFrame, symbol: str, date_str: str) -> str:
        """Saves raw price data by year/month partition."""
        if df.empty:
            return ""
        year, month, _ = date_str.split("-")
        target_dir = os.path.join(self.raw_dir, year, month, date_str)
        os.makedirs(target_dir, exist_ok=True)
        filename = f"{symbol}.parquet"
        filepath = os.path.join(target_dir, filename)
        df.to_parquet(filepath, index=False)
        # Also export CSV for inspection
        csv_path = os.path.join(target_dir, f"{symbol}.csv")
        df.to_csv(csv_path, index=False)
        return filepath

    def save_processed_prices(self, df: pd.DataFrame, symbol: str, is_index: bool = False) -> str:
        """Saves or appends processed historical price data ensuring no duplicates."""
        if df.empty:
            return ""
        subfolder = "indices" if is_index else "prices"
        target_dir = os.path.join(self.processed_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{symbol}.parquet")

        if os.path.exists(filepath):
            existing_df = pd.read_parquet(filepath)
            combined = pd.concat([existing_df, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date"], keep="last")
            combined = combined.sort_values(by="date").reset_index(drop=True)
            combined.to_parquet(filepath, index=False)
            csv_path = os.path.join(target_dir, f"{symbol}.csv")
            combined.to_csv(csv_path, index=False)
        else:
            df = df.drop_duplicates(subset=["date"], keep="last").sort_values(by="date").reset_index(drop=True)
            df.to_parquet(filepath, index=False)
            csv_path = os.path.join(target_dir, f"{symbol}.csv")
            df.to_csv(csv_path, index=False)

        return filepath

    def load_processed_prices(self, symbol: str, is_index: bool = False) -> pd.DataFrame:
        """Loads historical processed price series for a symbol."""
        subfolder = "indices" if is_index else "prices"
        filepath = os.path.join(self.processed_dir, subfolder, f"{symbol}.parquet")
        if not os.path.exists(filepath):
            csv_path = os.path.join(self.processed_dir, subfolder, f"{symbol}.csv")
            if os.path.exists(csv_path):
                return pd.read_csv(csv_path)
            return pd.DataFrame()
        return pd.read_parquet(filepath)

    def save_quality_report(self, date_str: str, report_data: Dict[str, Any]) -> str:
        """Saves daily data quality report in JSON format."""
        filepath = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2)
        return filepath

    def save_daily_features(self, df: pd.DataFrame, date_str: str) -> str:
        """Saves daily feature set."""
        target_dir = os.path.join(self.features_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        parquet_path = os.path.join(target_dir, f"{date_str}.parquet")
        df.to_parquet(parquet_path, index=False)
        csv_path = os.path.join(target_dir, f"{date_str}.csv")
        df.to_csv(csv_path, index=False)
        return parquet_path

    def save_daily_analysis(self, date_str: str, analysis_data: Dict[str, Any]) -> str:
        """Saves machine-readable daily analysis JSON output."""
        target_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(analysis_data, f, indent=2)
        return filepath

    def save_daily_report(self, date_str: str, report_content: str) -> str:
        """Saves human-readable daily Markdown report."""
        target_dir = os.path.join(self.reports_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{date_str}.md")
        with open(filepath, "w") as f:
            f.write(report_content)
        return filepath
