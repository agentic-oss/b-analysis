import os
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages reading, writing, and partitioning of datasets across data/ directory."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.reports_dir = os.path.join(base_dir, "reports")

        for d in [self.raw_dir, self.processed_dir, self.features_dir, self.analysis_dir, self.predictions_dir, self.reports_dir]:
            os.makedirs(d, exist_ok=True)

    def save_raw_daily(self, df: pd.DataFrame, date_str: str, ticker: str) -> str:
        """
        Saves raw OHLCV dataframe partitioned by YYYY/MM/YYYY-MM-DD/ticker.parquet
        """
        if df.empty:
            logger.warning(f"Empty dataframe provided for raw save: {ticker} on {date_str}")
            return ""

        parts = date_str.split("-")
        if len(parts) == 3:
            year, month, day = parts
        else:
            dt = pd.to_datetime(date_str)
            year, month, day = dt.strftime("%Y"), dt.strftime("%m"), dt.strftime("%d")

        target_dir = os.path.join(self.raw_dir, year, month, date_str)
        os.makedirs(target_dir, exist_ok=True)

        # Attach metadata
        df_copy = df.copy()
        df_copy["ticker"] = ticker
        df_copy["ingestion_timestamp"] = pd.Timestamp.now().isoformat()

        clean_ticker = ticker.replace("^", "").replace(".", "_")
        parquet_path = os.path.join(target_dir, f"{clean_ticker}.parquet")
        csv_path = os.path.join(target_dir, f"{clean_ticker}.csv")

        try:
            df_copy.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning(f"Failed to write Parquet for {ticker}: {e}. Falling back to CSV.")

        df_copy.to_csv(csv_path, index=False)
        return parquet_path if os.path.exists(parquet_path) else csv_path

    def save_processed_prices(self, df: pd.DataFrame, category: str = "prices") -> str:
        """
        Saves clean, processed prices/indices to data/processed/{category}.parquet and csv.
        """
        target_dir = os.path.join(self.processed_dir, category)
        os.makedirs(target_dir, exist_ok=True)

        parquet_path = os.path.join(target_dir, "dataset.parquet")
        csv_path = os.path.join(target_dir, "dataset.csv")

        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning(f"Failed to write Parquet: {e}")

        df.to_csv(csv_path, index=False)
        return parquet_path if os.path.exists(parquet_path) else csv_path

    def load_processed_prices(self, category: str = "prices") -> pd.DataFrame:
        target_dir = os.path.join(self.processed_dir, category)
        parquet_path = os.path.join(target_dir, "dataset.parquet")
        csv_path = os.path.join(target_dir, "dataset.csv")

        if os.path.exists(parquet_path):
            try:
                return pd.read_parquet(parquet_path)
            except Exception:
                pass
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()
