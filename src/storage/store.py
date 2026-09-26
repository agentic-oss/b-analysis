"""
Storage architecture and data persistence engine supporting Parquet, CSV,
and JSON formats with idempotent append/update strategies.
"""

from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)


class DataStore:
    """Manages directory creation, file layout, Parquet/CSV/JSON saving, and idempotent updates."""

    def __init__(self, base_dir: Union[str, Path] = "data", reports_dir: Union[str, Path] = "reports"):
        self.base_dir = Path(base_dir)
        self.reports_dir = Path(reports_dir)
        self._init_directories()

    def _init_directories(self):
        """Ensure all required storage subdirectories exist."""
        subdirs = [
            self.base_dir / "raw",
            self.base_dir / "processed" / "prices",
            self.base_dir / "processed" / "indices",
            self.base_dir / "processed" / "corporate_actions",
            self.base_dir / "features" / "daily",
            self.base_dir / "analysis" / "daily",
            self.base_dir / "analysis" / "weekly",
            self.base_dir / "analysis" / "monthly",
            self.base_dir / "predictions" / "daily",
            self.base_dir / "quality",
            self.reports_dir / "daily"
        ]
        for d in subdirs:
            d.mkdir(parents=True, exist_ok=True)

    def save_raw_snapshot(self, date_str: str, symbol: str, data: Union[Dict, pd.DataFrame]):
        """Save raw API snapshot to data/raw/YYYY/MM/YYYY-MM-DD/symbol.json or .parquet."""
        dt = pd.to_datetime(date_str)
        raw_path = self.base_dir / "raw" / f"{dt.year:04d}" / f"{dt.month:02d}" / date_str
        raw_path.mkdir(parents=True, exist_ok=True)

        if isinstance(data, pd.DataFrame):
            data.to_parquet(raw_path / f"{symbol}.parquet", index=False)
            data.to_csv(raw_path / f"{symbol}.csv", index=False)
        else:
            with open(raw_path / f"{symbol}.json", "w") as f:
                json.dump(data, f, indent=2)

    def update_processed_dataset(
        self, symbol: str, new_df: pd.DataFrame, category: str = "prices"
    ) -> pd.DataFrame:
        """
        Idempotent append/update of historical price/index series.
        Reads existing Parquet dataset if available, merges new records, deduplicates by Date, and saves back.
        """
        if new_df.empty:
            return new_df

        target_dir = self.base_dir / "processed" / category
        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_file = target_dir / f"{symbol}.parquet"
        csv_file = target_dir / f"{symbol}.csv"

        if parquet_file.exists():
            try:
                existing_df = pd.read_parquet(parquet_file)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            except Exception as e:
                logger.warning(f"Could not read existing parquet file for {symbol}: {e}")
                combined_df = new_df
        else:
            combined_df = new_df

        # Ensure Date column string format YYYY-MM-DD
        combined_df["Date"] = pd.to_datetime(combined_df["Date"]).dt.strftime("%Y-%m-%d")

        # Deduplicate keeping latest record for each date
        combined_df = combined_df.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)

        # Save back in both Parquet and CSV
        combined_df.to_parquet(parquet_file, index=False)
        combined_df.to_csv(csv_file, index=False)
        return combined_df

    def load_processed_dataset(self, symbol: str, category: str = "prices") -> pd.DataFrame:
        """Load processed dataset for a ticker or index."""
        parquet_file = self.base_dir / "processed" / category / f"{symbol}.parquet"
        csv_file = self.base_dir / "processed" / category / f"{symbol}.csv"

        if parquet_file.exists():
            return pd.read_parquet(parquet_file)
        elif csv_file.exists():
            return pd.read_csv(csv_file)
        else:
            return pd.DataFrame()

    def save_quality_report(self, date_str: str, report_dict: Dict[str, Any]):
        """Save data quality report to data/quality/YYYY-MM-DD.json."""
        out_file = self.base_dir / "quality" / f"{date_str}.json"
        with open(out_file, "w") as f:
            json.dump(report_dict, f, indent=2)

    def save_daily_analysis_json(self, date_str: str, analysis_dict: Dict[str, Any]):
        """Save machine-readable daily analysis to data/analysis/daily/YYYY-MM-DD.json."""
        out_file = self.base_dir / "analysis" / "daily" / f"{date_str}.json"
        with open(out_file, "w") as f:
            json.dump(analysis_dict, f, indent=2)

    def save_daily_report_md(self, date_str: str, content: str):
        """Save human-readable markdown report to reports/daily/YYYY-MM-DD.md."""
        out_file = self.reports_dir / "daily" / f"{date_str}.md"
        with open(out_file, "w") as f:
            f.write(content)

    def save_features(self, date_str: str, df: pd.DataFrame):
        """Save engineered features for a date to data/features/daily/YYYY-MM-DD.parquet."""
        out_parquet = self.base_dir / "features" / "daily" / f"{date_str}.parquet"
        out_csv = self.base_dir / "features" / "daily" / f"{date_str}.csv"
        df.to_parquet(out_parquet, index=False)
        df.to_csv(out_csv, index=False)

    def save_predictions(self, date_str: str, df: pd.DataFrame):
        """Save prediction outputs to data/predictions/daily/YYYY-MM-DD.parquet."""
        out_parquet = self.base_dir / "predictions" / "daily" / f"{date_str}.parquet"
        out_csv = self.base_dir / "predictions" / "daily" / f"{date_str}.csv"
        df.to_parquet(out_parquet, index=False)
        df.to_csv(out_csv, index=False)
