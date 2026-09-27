"""
Storage manager handling raw, processed, feature, analysis, prediction, and report artifacts.
"""
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages reading and writing data across the pipeline directory structure."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "data" / "raw"
        self.processed_dir = self.base_dir / "data" / "processed"
        self.features_dir = self.base_dir / "data" / "features"
        self.analysis_dir = self.base_dir / "data" / "analysis"
        self.predictions_dir = self.base_dir / "data" / "predictions"
        self.quality_dir = self.base_dir / "data" / "quality"
        self.reports_dir = self.base_dir / "reports" / "daily"

        for d in [
            self.raw_dir,
            self.processed_dir / "prices",
            self.processed_dir / "indices",
            self.processed_dir / "corporate_actions",
            self.features_dir / "daily",
            self.analysis_dir / "daily",
            self.predictions_dir / "daily",
            self.quality_dir,
            self.reports_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def save_raw_data(
        self, df: pd.DataFrame, symbol: str, date_str: str, data_provider: str = "yfinance"
    ) -> Path:
        """Saves raw market data into partitioned raw directory structure."""
        if df.empty:
            return None
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        dir_path = self.raw_dir / f"{dt.year:04d}" / f"{dt.month:02d}" / date_str
        dir_path.mkdir(parents=True, exist_ok=True)

        df = df.copy()
        df["ticker"] = symbol
        df["provider"] = data_provider
        df["ingestion_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        filepath = dir_path / f"{symbol.replace('^', '').replace('=', '')}.csv"
        df.to_csv(filepath, index=False)
        return filepath

    def save_processed_prices(
        self, df: pd.DataFrame, symbol: str, is_index: bool = False
    ) -> Path:
        """Saves or appends processed historical prices to Parquet and CSV files without duplicates."""
        if df.empty:
            return None
        target_sub = "indices" if is_index else "prices"
        clean_sym = symbol.replace("^", "").replace("=", "").replace(".NS", "")
        p_dir = self.processed_dir / target_sub
        p_dir.mkdir(parents=True, exist_ok=True)

        parquet_file = p_dir / f"{clean_sym}.parquet"
        csv_file = p_dir / f"{clean_sym}.csv"

        df = df.copy()
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        if parquet_file.exists():
            try:
                existing_df = pd.read_parquet(parquet_file)
                combined = pd.concat([existing_df, df], ignore_index=True)
                combined = combined.drop_duplicates(subset=["Date"], keep="last")
                combined = combined.sort_values("Date").reset_index(drop=True)
                df = combined
            except Exception as e:
                logger.warning(f"Error reading existing parquet {parquet_file}: {e}")

        df.to_parquet(parquet_file, index=False)
        df.to_csv(csv_file, index=False)
        return parquet_file

    def get_processed_prices(self, symbol: str, is_index: bool = False) -> pd.DataFrame:
        """Reads processed prices for a symbol."""
        target_sub = "indices" if is_index else "prices"
        clean_sym = symbol.replace("^", "").replace("=", "").replace(".NS", "")
        parquet_file = self.processed_dir / target_sub / f"{clean_sym}.parquet"
        csv_file = self.processed_dir / target_sub / f"{clean_sym}.csv"

        if parquet_file.exists():
            return pd.read_parquet(parquet_file)
        elif csv_file.exists():
            return pd.read_csv(csv_file)
        return pd.DataFrame()

    def save_features(self, df: pd.DataFrame, date_str: str) -> Path:
        """Saves daily feature dataset."""
        f_dir = self.features_dir / "daily"
        f_dir.mkdir(parents=True, exist_ok=True)
        parquet_file = f_dir / f"{date_str}.parquet"
        csv_file = f_dir / f"{date_str}.csv"
        df.to_parquet(parquet_file, index=False)
        df.to_csv(csv_file, index=False)
        return parquet_file

    def save_daily_analysis(self, analysis_data: Dict[str, Any], date_str: str) -> Path:
        """Saves structured daily analysis JSON."""
        json_file = self.analysis_dir / "daily" / f"{date_str}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2)
        return json_file

    def save_quality_report(self, report_data: Dict[str, Any], date_str: str) -> Path:
        """Saves data quality report JSON."""
        json_file = self.quality_dir / f"{date_str}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        return json_file

    def save_daily_report_md(self, content: str, date_str: str) -> Path:
        """Saves daily Markdown report."""
        md_file = self.reports_dir / f"{date_str}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)
        return md_file
