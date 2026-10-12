"""
Data storage manager for managing raw, processed, features, analysis, and report files.
Supports Parquet, CSV, and JSON formats with metadata tagging and append/update deduplication.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd


class StorageManager:
    """
    Handles file saving and loading across data directories:
    data/raw, data/processed, data/features, data/analysis, data/predictions, data/quality, reports/
    """

    def __init__(self, base_data_dir: str = "data", base_reports_dir: str = "reports"):
        self.base_data_dir = base_data_dir
        self.base_reports_dir = base_reports_dir

    def get_raw_dir(self, date_str: str) -> str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        path = os.path.join(self.base_data_dir, "raw", f"{dt.year:04d}", f"{dt.month:02d}", date_str)
        os.makedirs(path, exist_ok=True)
        return path

    def get_processed_dir(self, category: str = "prices") -> str:
        path = os.path.join(self.base_data_dir, "processed", category)
        os.makedirs(path, exist_ok=True)
        return path

    def get_features_dir(self, sub_dir: str = "daily") -> str:
        path = os.path.join(self.base_data_dir, "features", sub_dir)
        os.makedirs(path, exist_ok=True)
        return path

    def get_analysis_dir(self, timeframe: str = "daily") -> str:
        path = os.path.join(self.base_data_dir, "analysis", timeframe)
        os.makedirs(path, exist_ok=True)
        return path

    def get_predictions_dir(self, timeframe: str = "daily") -> str:
        path = os.path.join(self.base_data_dir, "predictions", timeframe)
        os.makedirs(path, exist_ok=True)
        return path

    def get_quality_dir(self) -> str:
        path = os.path.join(self.base_data_dir, "quality")
        os.makedirs(path, exist_ok=True)
        return path

    def get_reports_dir(self, timeframe: str = "daily") -> str:
        path = os.path.join(self.base_reports_dir, timeframe)
        os.makedirs(path, exist_ok=True)
        return path

    def save_dataframe(
        self,
        df: pd.DataFrame,
        filepath_without_ext: str,
        formats: List[str] = ["parquet", "csv"],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Saves DataFrame in requested formats (parquet, csv) and optionally injects metadata.
        """
        if df is None or df.empty:
            return []

        saved_files = []
        df_to_save = df.copy()

        if metadata:
            for k, v in metadata.items():
                if k not in df_to_save.columns:
                    df_to_save[k] = v

        if "parquet" in formats:
            parquet_path = f"{filepath_without_ext}.parquet"
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
            df_to_save.to_parquet(parquet_path, index=False)
            saved_files.append(parquet_path)

        if "csv" in formats:
            csv_path = f"{filepath_without_ext}.csv"
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df_to_save.to_csv(csv_path, index=False)
            saved_files.append(csv_path)

        return saved_files

    def update_processed_dataset(
        self,
        new_df: pd.DataFrame,
        category: str,
        filename: str,
        dedup_keys: List[str] = ["Ticker", "Date"],
    ) -> str:
        """
        Appends new DataFrame records to existing processed dataset, deduplicating on dedup_keys.
        """
        processed_dir = self.get_processed_dir(category)
        parquet_path = os.path.join(processed_dir, f"{filename}.parquet")
        csv_path = os.path.join(processed_dir, f"{filename}.csv")

        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df.copy()

        if dedup_keys:
            # Ensure proper datetime sorting before deduplication
            if "Date" in combined_df.columns:
                combined_df["Date"] = pd.to_datetime(combined_df["Date"])
                combined_df = combined_df.sort_values("Date")
            combined_df = combined_df.drop_duplicates(subset=dedup_keys, keep="last").reset_index(drop=True)

        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        combined_df.to_parquet(parquet_path, index=False)
        combined_df.to_csv(csv_path, index=False)
        return parquet_path

    def save_json(self, data: Dict[str, Any], filepath: str) -> str:
        """
        Saves dictionary data to a JSON file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return filepath

    def load_json(self, filepath: str) -> Dict[str, Any]:
        """
        Loads JSON data from file.
        """
        if not os.path.exists(filepath):
            return {}
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_markdown(self, content: str, filepath: str) -> str:
        """
        Saves text content to a Markdown file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
