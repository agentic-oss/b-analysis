import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages raw, processed, feature, analysis, prediction, and report storage formats
    (Parquet, CSV, JSON) with strict metadata inclusion.
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

        for d in [
            self.raw_dir,
            self.processed_dir,
            self.features_dir,
            self.analysis_dir,
            self.predictions_dir,
            self.quality_dir,
            self.reports_dir,
        ]:
            os.makedirs(d, exist_ok=True)

    def _attach_metadata(
        self,
        df: pd.DataFrame,
        ticker: str,
        exchange: str,
        data_provider: str = "yfinance",
    ) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        if "ticker" not in df.columns:
            df["ticker"] = ticker
        if "exchange" not in df.columns:
            df["exchange"] = exchange
        if "data_provider" not in df.columns:
            df["data_provider"] = data_provider
        if "ingestion_timestamp" not in df.columns:
            df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
        return df

    def save_raw_data(
        self,
        df: pd.DataFrame,
        ticker: str,
        exchange: str,
        date_str: str,
        data_provider: str = "yfinance",
    ):
        """Saves raw data partitioned by YYYY/MM/YYYY-MM-DD/ticker.parquet and .csv"""
        if df.empty:
            return
        df_meta = self._attach_metadata(df, ticker, exchange, data_provider)

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year_str = dt.strftime("%Y")
            month_str = dt.strftime("%m")
        except Exception:
            year_str = "unknown"
            month_str = "unknown"

        dir_path = os.path.join(self.raw_dir, year_str, month_str, date_str)
        os.makedirs(dir_path, exist_ok=True)

        parquet_path = os.path.join(dir_path, f"{ticker}.parquet")
        csv_path = os.path.join(dir_path, f"{ticker}.csv")

        df_meta.to_parquet(parquet_path, index=False)
        df_meta.to_csv(csv_path, index=False)
        logger.info(f"Saved raw data for {ticker} to {parquet_path}")

    def save_processed_prices(
        self,
        df: pd.DataFrame,
        ticker: str,
        exchange: str,
        data_provider: str = "yfinance",
    ):
        """Saves or appends processed historical prices to data/processed/prices/{ticker}.parquet & .csv"""
        if df.empty:
            return
        df_meta = self._attach_metadata(df, ticker, exchange, data_provider)
        prices_dir = os.path.join(self.processed_dir, "prices")
        os.makedirs(prices_dir, exist_ok=True)

        parquet_path = os.path.join(prices_dir, f"{ticker}.parquet")
        csv_path = os.path.join(prices_dir, f"{ticker}.csv")

        # Deduplicate with existing historical data if present
        if os.path.exists(parquet_path):
            existing_df = pd.read_parquet(parquet_path)
            combined = pd.concat([existing_df, df_meta], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date", "ticker"], keep="last")
            combined = combined.sort_values("date").reset_index(drop=True)
        else:
            combined = df_meta.sort_values("date").reset_index(drop=True)

        combined.to_parquet(parquet_path, index=False)
        combined.to_csv(csv_path, index=False)
        logger.info(f"Updated processed prices for {ticker} at {parquet_path}")

    def load_processed_prices(self, ticker: str) -> pd.DataFrame:
        parquet_path = os.path.join(self.processed_dir, "prices", f"{ticker}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        csv_path = os.path.join(self.processed_dir, "prices", f"{ticker}.csv")
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def save_features(self, df: pd.DataFrame, ticker: str):
        """Saves engineered features in data/features/daily/{ticker}.parquet"""
        if df.empty:
            return
        daily_features_dir = os.path.join(self.features_dir, "daily")
        os.makedirs(daily_features_dir, exist_ok=True)
        parquet_path = os.path.join(daily_features_dir, f"{ticker}.parquet")
        csv_path = os.path.join(daily_features_dir, f"{ticker}.csv")

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)

    def load_features(self, ticker: str) -> pd.DataFrame:
        parquet_path = os.path.join(self.features_dir, "daily", f"{ticker}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        return pd.DataFrame()

    def save_quality_report(self, date_str: str, report_data: Dict[str, Any]):
        file_path = os.path.join(self.quality_dir, f"{date_str}.json")
        with open(file_path, "w") as f:
            json.dump(report_data, f, indent=2)

    def save_daily_analysis(self, date_str: str, analysis_data: Dict[str, Any]):
        daily_analysis_dir = os.path.join(self.analysis_dir, "daily")
        os.makedirs(daily_analysis_dir, exist_ok=True)
        file_path = os.path.join(daily_analysis_dir, f"{date_str}.json")
        with open(file_path, "w") as f:
            json.dump(analysis_data, f, indent=2)

    def save_daily_report(self, date_str: str, report_content: str):
        daily_reports_dir = os.path.join(self.reports_dir, "daily")
        os.makedirs(daily_reports_dir, exist_ok=True)
        file_path = os.path.join(daily_reports_dir, f"{date_str}.md")
        with open(file_path, "w") as f:
            f.write(report_content)
