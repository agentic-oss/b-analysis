import os
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class DataStore:
    """Manages file storage for raw, processed, features, analysis, predictions, and reports."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.reports_dir = os.path.join("reports")
        self.quality_dir = os.path.join(base_dir, "quality")

        self._ensure_dirs()

    def _ensure_dirs(self):
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
            os.path.join(self.reports_dir, "daily"),
            self.quality_dir
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_processed_prices(self, ticker: str, df: pd.DataFrame, provider: str = "yfinance") -> str:
        """Saves/Appends processed historical OHLCV prices in Parquet/CSV."""
        if df.empty:
            return ""

        file_path = os.path.join(self.processed_dir, "prices", f"{ticker}.parquet")
        csv_path = os.path.join(self.processed_dir, "prices", f"{ticker}.csv")

        df = df.copy()
        df["ticker"] = ticker
        df["data_provider"] = provider
        df["ingestion_timestamp"] = pd.Timestamp.now().isoformat()

        if os.path.exists(file_path):
            try:
                existing_df = pd.read_parquet(file_path)
                combined = pd.concat([existing_df, df], ignore_index=True)
                combined = combined.drop_duplicates(subset=["ticker", "date"], keep="last")
                combined = combined.sort_values("date").reset_index(drop=True)
                df = combined
            except Exception as e:
                logger.warning(f"Failed to read existing parquet for {ticker}: {e}")

        df.to_parquet(file_path, index=False)
        df.to_csv(csv_path, index=False)
        return file_path

    def load_processed_prices(self, ticker: str) -> pd.DataFrame:
        file_path = os.path.join(self.processed_dir, "prices", f"{ticker}.parquet")
        if not os.path.exists(file_path):
            csv_path = os.path.join(self.processed_dir, "prices", f"{ticker}.csv")
            if os.path.exists(csv_path):
                return pd.read_csv(csv_path)
            return pd.DataFrame()
        return pd.read_parquet(file_path)

    def save_quality_report(self, date_str: str, report: Dict[str, Any]):
        path = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

    def save_daily_analysis(self, date_str: str, data: Dict[str, Any]):
        path = os.path.join(self.analysis_dir, "daily", f"{date_str}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def save_daily_report(self, date_str: str, content: str):
        path = os.path.join(self.reports_dir, "daily", f"{date_str}.md")
        with open(path, "w") as f:
            f.write(content)

    def save_features(self, date_str: str, df: pd.DataFrame):
        if df.empty:
            return
        parquet_path = os.path.join(self.features_dir, "daily", f"{date_str}.parquet")
        csv_path = os.path.join(self.features_dir, "daily", f"{date_str}.csv")
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
