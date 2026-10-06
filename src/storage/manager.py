import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages raw, processed, features, analysis, and report file persistence."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.quality_dir = os.path.join(base_dir, "quality")
        self.reports_dir = os.path.join("reports", "daily")

        self._ensure_directories()

    def _ensure_directories(self):
        """Create standard folder structure."""
        dirs = [
            self.raw_dir,
            os.path.join(self.processed_dir, "prices"),
            os.path.join(self.processed_dir, "indices"),
            os.path.join(self.processed_dir, "corporate_actions"),
            os.path.join(self.features_dir, "daily"),
            os.path.join(self.analysis_dir, "daily"),
            os.path.join(self.analysis_dir, "weekly"),
            os.path.join(self.analysis_dir, "monthly"),
            os.path.join(self.predictions_dir, "daily"),
            self.quality_dir,
            self.reports_dir,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_raw_daily(self, date_str: str, ticker: str, df: pd.DataFrame, exchange: str = "NSE", provider: str = "yfinance") -> str:
        """Save raw downloaded DataFrame for a specific date and ticker."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        folder = os.path.join(self.raw_dir, f"{dt.year:04d}", f"{dt.month:02d}", date_str)
        os.makedirs(folder, exist_ok=True)

        if not df.empty:
            df_to_save = df.copy()
            df_to_save["ticker"] = ticker
            df_to_save["exchange"] = exchange
            df_to_save["data_provider"] = provider
            df_to_save["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

            filepath_parquet = os.path.join(folder, f"{ticker}.parquet")
            filepath_csv = os.path.join(folder, f"{ticker}.csv")

            df_to_save.to_parquet(filepath_parquet, index=False)
            df_to_save.to_csv(filepath_csv, index=False)
            return filepath_parquet
        return ""

    def append_processed_prices(self, ticker: str, df: pd.DataFrame, category: str = "prices", exchange: str = "NSE", provider: str = "yfinance") -> str:
        """
        Appends new validated price records to the cumulative historical dataset for a ticker.
        Deduplicates on date, keeping the latest record.
        """
        if df.empty:
            return ""

        target_dir = os.path.join(self.processed_dir, category)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{ticker}.parquet")
        filepath_csv = os.path.join(target_dir, f"{ticker}.csv")

        new_data = df.copy()
        new_data["ticker"] = ticker
        new_data["exchange"] = exchange
        new_data["data_provider"] = provider
        if "ingestion_timestamp" not in new_data.columns:
            new_data["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

        # Ensure date column is standard string YYYY-MM-DD for consistency
        new_data["date"] = pd.to_datetime(new_data["date"]).dt.strftime("%Y-%m-%d")

        if os.path.exists(filepath):
            existing_df = pd.read_parquet(filepath)
            existing_df["date"] = pd.to_datetime(existing_df["date"]).dt.strftime("%Y-%m-%d")

            combined = pd.concat([existing_df, new_data], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date"], keep="last")
            combined = combined.sort_values("date").reset_index(drop=True)
        else:
            combined = new_data.sort_values("date").reset_index(drop=True)

        combined.to_parquet(filepath, index=False)
        combined.to_csv(filepath_csv, index=False)
        return filepath

    def load_processed_prices(self, ticker: str, category: str = "prices") -> pd.DataFrame:
        """Load cumulative historical dataset for a ticker."""
        filepath = os.path.join(self.processed_dir, category, f"{ticker}.parquet")
        if os.path.exists(filepath):
            df = pd.read_parquet(filepath)
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").reset_index(drop=True)
        return pd.DataFrame()

    def save_quality_report(self, date_str: str, report: Dict[str, Any]) -> str:
        """Save data quality report JSON."""
        filepath = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        return filepath

    def save_daily_analysis(self, date_str: str, data: Dict[str, Any]) -> str:
        """Save machine-readable daily analysis JSON."""
        filepath = os.path.join(self.analysis_dir, "daily", f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def save_daily_report(self, date_str: str, markdown_content: str) -> str:
        """Save human-readable daily markdown report."""
        filepath = os.path.join(self.reports_dir, f"{date_str}.md")
        with open(filepath, "w") as f:
            f.write(markdown_content)
        return filepath
