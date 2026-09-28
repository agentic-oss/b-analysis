import os
import json
import logging
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger("storage.store")

class StorageEngine:
    """Handles raw, processed, feature, prediction, and report persistence."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.quality_dir = os.path.join(base_dir, "quality")
        self._ensure_directories()

    def _ensure_directories(self):
        for path in [self.raw_dir, self.processed_dir, self.features_dir, self.analysis_dir, self.predictions_dir, self.quality_dir]:
            os.makedirs(path, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, date: str, name: str = "prices"):
        """Saves raw daily dataframe partitioned by YYYY/MM/YYYY-MM-DD."""
        if df.empty:
            return
        dt = pd.to_datetime(date)
        year_str = dt.strftime("%Y")
        month_str = dt.strftime("%m")
        day_dir = os.path.join(self.raw_dir, year_str, month_str, date)
        os.makedirs(day_dir, exist_ok=True)

        csv_path = os.path.join(day_dir, f"{name}.csv")
        parquet_path = os.path.join(day_dir, f"{name}.parquet")

        df.to_csv(csv_path, index=False)
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning(f"Could not save Parquet raw file: {e}")

    def save_processed_prices(self, symbol: str, df: pd.DataFrame):
        """Append or update processed historical price series for a symbol."""
        if df.empty:
            return
        os.makedirs(os.path.join(self.processed_dir, "prices"), exist_ok=True)
        file_path = os.path.join(self.processed_dir, "prices", f"{symbol}.parquet")
        csv_path = os.path.join(self.processed_dir, "prices", f"{symbol}.csv")

        if os.path.exists(file_path):
            try:
                existing_df = pd.read_parquet(file_path)
                combined = pd.concat([existing_df, df]).drop_duplicates(subset=['date'], keep='last')
                combined = combined.sort_values('date').reset_index(drop=True)
            except Exception:
                combined = df.sort_values('date').reset_index(drop=True)
        else:
            combined = df.sort_values('date').reset_index(drop=True)

        try:
            combined.to_parquet(file_path, index=False)
        except Exception as e:
            logger.warning(f"Could not save parquet processed prices: {e}")
        combined.to_csv(csv_path, index=False)

    def load_processed_prices(self, symbol: str) -> pd.DataFrame:
        file_path = os.path.join(self.processed_dir, "prices", f"{symbol}.parquet")
        csv_path = os.path.join(self.processed_dir, "prices", f"{symbol}.csv")
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        elif os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_features(self, date: str, df: pd.DataFrame):
        os.makedirs(os.path.join(self.features_dir, "daily"), exist_ok=True)
        parquet_path = os.path.join(self.features_dir, "daily", f"{date}.parquet")
        csv_path = os.path.join(self.features_dir, "daily", f"{date}.csv")
        if not df.empty:
            df.to_csv(csv_path, index=False)
            try:
                df.to_parquet(parquet_path, index=False)
            except Exception as e:
                logger.warning(f"Could not save features parquet: {e}")

    def save_json(self, relative_path: str, data: Dict[str, Any]):
        full_path = os.path.join(self.base_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load_json(self, relative_path: str) -> Optional[Dict[str, Any]]:
        full_path = os.path.join(self.base_dir, relative_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
