"""Storage Manager for structured parquet, JSON, and CSV storage."""

import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class StorageManager:
    """Handles structured directory storage for raw, processed, features, analysis, predictions, reports, and quality."""

    def __init__(self, base_dir: str = "data", reports_dir: str = "reports"):
        self.base_dir = base_dir
        self.reports_dir = reports_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.quality_dir = os.path.join(base_dir, "quality")

        # Ensure directories exist
        for d in [self.raw_dir, self.processed_dir, self.features_dir, self.analysis_dir,
                  self.predictions_dir, self.quality_dir, self.reports_dir]:
            os.makedirs(d, exist_ok=True)

    def save_raw_prices(self, df: pd.DataFrame, date_str: str):
        """Saves raw price data into data/raw/YYYY/MM/YYYY-MM-DD/ in parquet, csv, and json formats."""
        if df.empty:
            return
        year, month, _ = date_str.split('-')
        target_dir = os.path.join(self.raw_dir, year, month, date_str)
        os.makedirs(target_dir, exist_ok=True)

        parquet_path = os.path.join(target_dir, "raw_prices.parquet")
        csv_path = os.path.join(target_dir, "raw_prices.csv")
        json_path = os.path.join(target_dir, "raw_prices.json")

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient="records", indent=2)
        logger.info(f"Saved raw prices to {target_dir}")

    def save_processed_prices(self, df: pd.DataFrame, category: str = "prices"):
        """Saves or appends processed historical price dataframe."""
        if df.empty:
            return
        target_dir = os.path.join(self.processed_dir, category)
        os.makedirs(target_dir, exist_ok=True)

        parquet_path = os.path.join(target_dir, "historical.parquet")
        csv_path = os.path.join(target_dir, "historical.csv")

        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['ticker', 'date'], keep='last')
        else:
            combined_df = df

        combined_df.sort_values(by=['ticker', 'date'], inplace=True)
        combined_df.to_parquet(parquet_path, index=False)
        combined_df.to_csv(csv_path, index=False)

    def save_features(self, df: pd.DataFrame, date_str: str):
        """Saves daily feature set."""
        if df.empty:
            return
        daily_dir = os.path.join(self.features_dir, "daily")
        os.makedirs(daily_dir, exist_ok=True)

        parquet_path = os.path.join(daily_dir, f"{date_str}.parquet")
        csv_path = os.path.join(daily_dir, f"{date_str}.csv")

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)

    def save_quality_report(self, report: Dict[str, Any], date_str: str):
        """Saves data quality report to data/quality/YYYY-MM-DD.json."""
        filepath = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, cls=NumpyEncoder)

    def save_daily_analysis_json(self, analysis_data: Dict[str, Any], date_str: str):
        """Saves machine-readable daily analysis to data/analysis/daily/YYYY-MM-DD.json."""
        daily_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(daily_dir, exist_ok=True)
        filepath = os.path.join(daily_dir, f"{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(analysis_data, f, indent=2, cls=NumpyEncoder)

    def save_daily_report_markdown(self, markdown_content: str, date_str: str):
        """Saves human-readable daily report to reports/daily/YYYY-MM-DD.md."""
        daily_dir = os.path.join(self.reports_dir, "daily")
        os.makedirs(daily_dir, exist_ok=True)
        filepath = os.path.join(daily_dir, f"{date_str}.md")
        with open(filepath, "w") as f:
            f.write(markdown_content)
