"""
Storage Architecture & Management Module.
Handles loading and saving raw, processed, feature, analysis, prediction, and report files.
Supports Parquet, CSV, and JSON storage with deduplication and metadata enrichment.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """Centralized storage layer for raw, processed, features, analysis, and reports."""

    def __init__(self, base_dir: Union[str, Path] = "."):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "data" / "raw"
        self.processed_dir = self.base_dir / "data" / "processed"
        self.features_dir = self.base_dir / "data" / "features"
        self.analysis_dir = self.base_dir / "data" / "analysis"
        self.predictions_dir = self.base_dir / "data" / "predictions"
        self.quality_dir = self.base_dir / "data" / "quality"
        self.reports_dir = self.base_dir / "reports"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        dirs = [
            self.raw_dir,
            self.processed_dir / "prices",
            self.processed_dir / "indices",
            self.processed_dir / "corporate_actions",
            self.features_dir / "daily",
            self.analysis_dir / "daily",
            self.analysis_dir / "weekly",
            self.analysis_dir / "monthly",
            self.predictions_dir / "daily",
            self.quality_dir,
            self.reports_dir / "daily",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, ticker: str, date_str: str) -> Path:
        """Saves raw ingested data under data/raw/YYYY/MM/YYYY-MM-DD/ticker.csv."""
        dt = pd.to_datetime(date_str)
        year_str = dt.strftime("%Y")
        month_str = dt.strftime("%m")

        target_dir = self.raw_dir / year_str / month_str / date_str
        target_dir.mkdir(parents=True, exist_ok=True)

        clean_ticker = ticker.replace("^", "").replace(".", "_")
        filepath = target_dir / f"{clean_ticker}.csv"
        df.to_csv(filepath, index=False)
        return filepath

    def update_processed_dataset(
        self,
        new_df: pd.DataFrame,
        dataset_type: str = "prices",
        filename: str = "historical_prices",
    ) -> Path:
        """
        Appends new_df to existing processed dataset, deduplicating by (ticker, date).
        Saves as Parquet and CSV for redundancy.
        """
        if new_df.empty:
            logger.warning(f"Empty DataFrame passed to update_processed_dataset for {dataset_type}")
            return self.processed_dir / dataset_type / f"{filename}.parquet"

        target_dir = self.processed_dir / dataset_type
        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = target_dir / f"{filename}.parquet"
        csv_path = target_dir / f"{filename}.csv"

        existing_df = pd.DataFrame()
        if parquet_path.exists():
            try:
                existing_df = pd.read_parquet(parquet_path)
            except Exception as e:
                logger.warning(f"Could not read existing Parquet at {parquet_path}: {e}")
                if csv_path.exists():
                    existing_df = pd.read_csv(csv_path)

        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df.copy()

        # Deduplicate
        dedup_cols = ["ticker", "date"]
        avail_dedup = [c for c in dedup_cols if c in combined_df.columns]
        if avail_dedup:
            combined_df = combined_df.drop_duplicates(subset=avail_dedup, keep="last")

        if "date" in combined_df.columns:
            combined_df = combined_df.sort_values(avail_dedup).reset_index(drop=True)

        # Save parquet and CSV
        combined_df.to_parquet(parquet_path, index=False)
        combined_df.to_csv(csv_path, index=False)

        return parquet_path

    def load_processed_prices(self, dataset_type: str = "prices", filename: str = "historical_prices") -> pd.DataFrame:
        """Loads cumulative processed prices/indices dataset."""
        parquet_path = self.processed_dir / dataset_type / f"{filename}.parquet"
        csv_path = self.processed_dir / dataset_type / f"{filename}.csv"

        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        elif csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_features(self, features_df: pd.DataFrame, date_str: str) -> Path:
        """Saves engineered feature dataset for date_str."""
        target_dir = self.features_dir / "daily"
        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = target_dir / f"{date_str}.parquet"
        csv_path = target_dir / f"{date_str}.csv"

        features_df.to_parquet(parquet_path, index=False)
        features_df.to_csv(csv_path, index=False)
        return parquet_path

    def save_quality_report(self, report: Dict[str, Any], date_str: str) -> Path:
        """Saves daily data quality report to data/quality/YYYY-MM-DD.json."""
        filepath = self.quality_dir / f"{date_str}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return filepath

    def save_json_output(self, data: Dict[str, Any], relative_path: str) -> Path:
        """Saves arbitrary JSON output to given relative path under base_dir."""
        target_path = self.base_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return target_path

    def save_markdown_report(self, content: str, date_str: str) -> Path:
        """Saves daily markdown report to reports/daily/YYYY-MM-DD.md."""
        filepath = self.reports_dir / "daily" / f"{date_str}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
