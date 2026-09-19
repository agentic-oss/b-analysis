"""
Storage Manager for persisting raw, processed, features, analysis, and quality datasets.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages raw, processed, feature, analysis, and quality data storage."""

    def __init__(self, base_dir: str = "data", reports_dir: str = "reports"):
        self.base_dir = Path(base_dir)
        self.reports_dir = Path(reports_dir)
        self._init_directories()

    def _init_directories(self):
        """Ensure standard directory hierarchy exists."""
        dirs = [
            self.base_dir / "raw",
            self.base_dir / "processed" / "prices",
            self.base_dir / "processed" / "indices",
            self.base_dir / "processed" / "corporate_actions",
            self.base_dir / "processed" / "fundamentals",
            self.base_dir / "features" / "daily",
            self.base_dir / "analysis" / "daily",
            self.base_dir / "analysis" / "weekly",
            self.base_dir / "analysis" / "monthly",
            self.base_dir / "predictions" / "daily",
            self.base_dir / "quality",
            self.reports_dir / "daily"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def save_raw_data(self, df: pd.DataFrame, ticker: str, date_str: str) -> Path:
        """Save raw daily OHLCV data under data/raw/YYYY/MM/YYYY-MM-DD/."""
        year, month, _ = date_str.split("-")
        target_dir = self.base_dir / "raw" / year / month / date_str
        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = target_dir / f"{ticker}.parquet"
        csv_path = target_dir / f"{ticker}.csv"

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path

    def save_processed_prices(self, df: pd.DataFrame, ticker: str, category: str = "prices") -> Path:
        """Save or append processed price history for a symbol under data/processed/{category}/{ticker}.parquet."""
        target_dir = self.base_dir / "processed" / category
        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = target_dir / f"{ticker}.parquet"
        csv_path = target_dir / f"{ticker}.csv"

        if parquet_path.exists():
            existing_df = pd.read_parquet(parquet_path)
            combined = pd.concat([existing_df, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date"], keep="last")
            combined = combined.sort_values("date").reset_index(drop=True)
        else:
            combined = df.sort_values("date").reset_index(drop=True)

        combined.to_parquet(parquet_path, index=False)
        combined.to_csv(csv_path, index=False)
        return parquet_path

    def load_processed_prices(self, ticker: str, category: str = "prices") -> pd.DataFrame:
        """Load processed historical price dataset for a ticker."""
        parquet_path = self.base_dir / "processed" / category / f"{ticker}.parquet"
        if not parquet_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(parquet_path)

    def save_quality_report(self, report: Dict[str, Any], date_str: str) -> Path:
        """Save data quality report to data/quality/YYYY-MM-DD.json."""
        target_path = self.base_dir / "quality" / f"{date_str}.json"
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return target_path

    def save_features(self, df: pd.DataFrame, date_str: str) -> Path:
        """Save daily engineered features dataset."""
        target_dir = self.base_dir / "features" / "daily"
        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = target_dir / f"{date_str}.parquet"
        csv_path = target_dir / f"{date_str}.csv"

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        return parquet_path

    def save_daily_analysis(self, analysis_data: Dict[str, Any], date_str: str) -> Path:
        """Save daily structured analysis to data/analysis/daily/YYYY-MM-DD.json."""
        target_dir = self.base_dir / "analysis" / "daily"
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / f"{date_str}.json"
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2)
        return target_path

    def save_daily_report(self, markdown_content: str, date_str: str) -> Path:
        """Save daily markdown report to reports/daily/YYYY-MM-DD.md."""
        target_dir = self.reports_dir / "daily"
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / f"{date_str}.md"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return target_path
