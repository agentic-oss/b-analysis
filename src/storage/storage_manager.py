import os
import json
import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Manages historical market data storage adhering to directory standards:
    data/raw/, data/processed/, data/features/, data/analysis/, data/predictions/, data/reports/
    Supports Parquet, CSV, and JSON formats with metadata tracking.
    """

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.quality_dir = os.path.join(base_dir, "quality")
        self.reports_dir = "reports"

        for d in [self.raw_dir, self.processed_dir, self.features_dir, self.analysis_dir, self.predictions_dir, self.quality_dir, self.reports_dir]:
            os.makedirs(d, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, date_str: str) -> str:
        """
        Saves raw ingested data under data/raw/YYYY/MM/YYYY-MM-DD/raw_prices.parquet
        """
        if df.empty:
            return ""
        parts = date_str.split('-')
        year, month = parts[0], parts[1]
        target_dir = os.path.join(self.raw_dir, year, month, date_str)
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, "raw_prices.parquet")
        df.to_parquet(file_path, index=False)

        # Also save CSV for easy human inspection
        csv_path = os.path.join(target_dir, "raw_prices.csv")
        df.to_csv(csv_path, index=False)
        return file_path

    def save_processed_prices(self, df: pd.DataFrame) -> str:
        """
        Saves/appends normalized historical prices to data/processed/prices/historical.parquet
        and updates CSV version.
        Prevents duplicates by deduplicating on (symbol, date).
        """
        if df.empty:
            return ""
        target_dir = os.path.join(self.processed_dir, "prices")
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, "historical.parquet")

        if os.path.exists(file_path):
            existing_df = pd.read_parquet(file_path)
            combined = pd.concat([existing_df, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=['symbol', 'date'], keep='last')
            combined = combined.sort_values(by=['symbol', 'date'])
        else:
            combined = df.drop_duplicates(subset=['symbol', 'date'], keep='last').sort_values(by=['symbol', 'date'])

        combined.to_parquet(file_path, index=False)
        combined.to_csv(os.path.join(target_dir, "historical.csv"), index=False)
        return file_path

    def load_processed_prices(self) -> pd.DataFrame:
        file_path = os.path.join(self.processed_dir, "prices", "historical.parquet")
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return pd.DataFrame()

    def save_quality_report(self, report_dict: Dict[str, Any], date_str: str) -> str:
        target_file = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(target_file, "w") as f:
            json.dump(report_dict, f, indent=2)
        return target_file

    def save_daily_analysis(self, analysis_dict: Dict[str, Any], date_str: str) -> str:
        target_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, f"{date_str}.json")
        with open(target_file, "w") as f:
            json.dump(analysis_dict, f, indent=2)
        return target_file

    def save_daily_report(self, report_markdown: str, date_str: str) -> str:
        target_dir = os.path.join(self.reports_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, f"{date_str}.md")
        with open(target_file, "w") as f:
            f.write(report_markdown)
        return target_file

    def save_features(self, df: pd.DataFrame, date_str: str) -> str:
        target_dir = os.path.join(self.features_dir, "daily")
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, f"{date_str}.parquet")
        df.to_parquet(file_path, index=False)
        return file_path
