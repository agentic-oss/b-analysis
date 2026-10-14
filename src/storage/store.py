import os
import json
import logging
from typing import Optional, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

class DataStore:
    """
    Manages partition directories and idempotent reads/writes for:
    - data/raw/
    - data/processed/
    - data/features/
    - data/analysis/
    - data/predictions/
    - reports/
    """

    def __init__(self, base_dir: str = "data", reports_dir: str = "reports"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.features_dir = os.path.join(base_dir, "features")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.predictions_dir = os.path.join(base_dir, "predictions")
        self.quality_dir = os.path.join(base_dir, "quality")
        self.reports_dir = reports_dir

        for d in [self.raw_dir, self.processed_dir, self.features_dir,
                  self.analysis_dir, self.predictions_dir, self.quality_dir, self.reports_dir]:
            os.makedirs(d, exist_ok=True)

    def save_processed_prices(self, symbol: str, df: pd.DataFrame):
        """Saves processed OHLCV historical dataset to Parquet and CSV for a given symbol."""
        if df.empty:
            return
        clean_sym = symbol.replace("^", "INDEX_").replace(".NS", "").replace(".BO", "")
        prices_dir = os.path.join(self.processed_dir, "prices")
        os.makedirs(prices_dir, exist_ok=True)

        parquet_path = os.path.join(prices_dir, f"{clean_sym}.parquet")
        csv_path = os.path.join(prices_dir, f"{clean_sym}.csv")

        # Idempotent append/update logic
        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined = pd.concat([existing_df, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)
        else:
            combined = df.sort_values("Date").reset_index(drop=True)

        combined.to_parquet(parquet_path, index=False)
        combined.to_csv(csv_path, index=False)
        logger.info(f"Saved processed dataset for {symbol} ({len(combined)} rows) to {parquet_path}")

    def load_processed_prices(self, symbol: str) -> pd.DataFrame:
        """Loads processed price DataFrame for a given symbol."""
        clean_sym = symbol.replace("^", "INDEX_").replace(".NS", "").replace(".BO", "")
        parquet_path = os.path.join(self.processed_dir, "prices", f"{clean_sym}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        csv_path = os.path.join(self.processed_dir, "prices", f"{clean_sym}.csv")
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_features(self, target_date: str, df: pd.DataFrame):
        """Saves daily feature set to data/features/daily/YYYY-MM-DD.parquet and CSV."""
        if df.empty:
            return
        daily_feat_dir = os.path.join(self.features_dir, "daily")
        os.makedirs(daily_feat_dir, exist_ok=True)
        p_path = os.path.join(daily_feat_dir, f"{target_date}.parquet")
        c_path = os.path.join(daily_feat_dir, f"{target_date}.csv")
        df.to_parquet(p_path, index=False)
        df.to_csv(c_path, index=False)

    def save_daily_analysis(self, target_date: str, data: Dict[str, Any]):
        """Saves daily machine-readable JSON output to data/analysis/daily/YYYY-MM-DD.json."""
        daily_analysis_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(daily_analysis_dir, exist_ok=True)
        json_path = os.path.join(daily_analysis_dir, f"{target_date}.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    def save_daily_report(self, target_date: str, markdown_content: str):
        """Saves daily human-readable Markdown report to reports/daily/YYYY-MM-DD.md."""
        daily_reports_dir = os.path.join(self.reports_dir, "daily")
        os.makedirs(daily_reports_dir, exist_ok=True)
        md_path = os.path.join(daily_reports_dir, f"{target_date}.md")
        with open(md_path, "w") as f:
            f.write(markdown_content)
