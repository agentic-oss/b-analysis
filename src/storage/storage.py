import os
import json
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DataStorage:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.reports_dir = os.path.join(base_dir, "reports")
        self.quality_dir = os.path.join(base_dir, "quality")

        self._init_dirs()

    def _init_dirs(self):
        dirs = [
            self.raw_dir,
            os.path.join(self.processed_dir, "prices"),
            os.path.join(self.processed_dir, "indices"),
            os.path.join(self.processed_dir, "corporate_actions"),
            os.path.join(self.features_dir, "daily"),
            os.path.join(self.analysis_dir, "daily"),
            os.path.join(self.predictions_dir, "daily"),
            os.path.join(self.reports_dir, "daily"),
            self.quality_dir
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, ticker: str, date_str: str, provider: str = "yfinance") -> str:
        """Saves raw snapshot partitioned by YYYY/MM/YYYY-MM-DD/."""
        if df.empty:
            return ""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year_str = date_obj.strftime("%Y")
        month_str = date_obj.strftime("%m")

        target_dir = os.path.join(self.raw_dir, year_str, month_str, date_str)
        os.makedirs(target_dir, exist_ok=True)

        df_to_save = df.copy()
        df_to_save['ticker'] = ticker
        df_to_save['provider'] = provider
        df_to_save['ingestion_timestamp'] = datetime.now(timezone.utc).isoformat()

        file_path = os.path.join(target_dir, f"{ticker}.csv")
        df_to_save.to_csv(file_path, index=False)
        return file_path

    def save_processed_prices(self, df: pd.DataFrame, ticker: str, is_index: bool = False) -> str:
        """Saves or appends processed prices to Parquet and CSV without duplicates."""
        if df.empty:
            return ""
        sub_folder = "indices" if is_index else "prices"
        folder = os.path.join(self.processed_dir, sub_folder)
        os.makedirs(folder, exist_ok=True)

        parquet_path = os.path.join(folder, f"{ticker}.parquet")
        csv_path = os.path.join(folder, f"{ticker}.csv")

        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last').sort_values('date')
        else:
            combined_df = df.drop_duplicates(subset=['date'], keep='last').sort_values('date')

        combined_df.to_parquet(parquet_path, index=False)
        combined_df.to_csv(csv_path, index=False)
        return parquet_path

    def load_processed_prices(self, ticker: str, is_index: bool = False) -> pd.DataFrame:
        sub_folder = "indices" if is_index else "prices"
        parquet_path = os.path.join(self.processed_dir, sub_folder, f"{ticker}.parquet")
        csv_path = os.path.join(self.processed_dir, sub_folder, f"{ticker}.csv")

        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        elif os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_quality_report(self, report: Dict[str, Any], date_str: str) -> str:
        file_path = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2)
        return file_path

    def save_daily_analysis(self, analysis_data: Dict[str, Any], date_str: str) -> str:
        file_path = os.path.join(self.analysis_dir, "daily", f"{date_str}.json")
        with open(file_path, "w") as f:
            json.dump(analysis_data, f, indent=2)
        return file_path

    def save_features(self, df: pd.DataFrame, date_str: str) -> str:
        if df.empty:
            return ""
        parquet_path = os.path.join(self.features_dir, "daily", f"{date_str}.parquet")
        csv_path = os.path.join(self.features_dir, "daily", f"{date_str}.csv")
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path
