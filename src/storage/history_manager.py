import os
import logging
from typing import Optional
import pandas as pd
from .storage_manager import StorageManager

logger = logging.getLogger(__name__)

class HistoryManager:
    """Manages continuously growing historical datasets without duplicating records or overwriting history."""

    def __init__(self, storage_manager: Optional[StorageManager] = None):
        self.storage = storage_manager or StorageManager()

    def update_history(self, new_data: pd.DataFrame, category: str = "prices") -> pd.DataFrame:
        """
        Appends new price records to the stored dataset.
        Deduplicates on (ticker, date), preserving latest updates.
        """
        if new_data.empty:
            logger.info(f"No new data to append for {category}")
            return self.storage.load_processed_prices(category)

        existing_data = self.storage.load_processed_prices(category)

        if existing_data.empty:
            combined = new_data.copy()
        else:
            combined = pd.concat([existing_data, new_data], ignore_index=True)

        # Deduplicate based on ticker and date
        if "ticker" in combined.columns and "date" in combined.columns:
            combined["date"] = pd.to_datetime(combined["date"]).dt.strftime("%Y-%m-%d")
            combined = combined.drop_duplicates(subset=["ticker", "date"], keep="last")
            combined = combined.sort_values(by=["ticker", "date"]).reset_index(drop=True)

        self.storage.save_processed_prices(combined, category=category)
        logger.info(f"Updated historical dataset for {category}. Total records: {len(combined)}")
        return combined

    def get_stock_history(self, ticker: str, category: str = "prices") -> pd.DataFrame:
        df = self.storage.load_processed_prices(category)
        if df.empty or "ticker" not in df.columns:
            return pd.DataFrame()
        stock_df = df[df["ticker"] == ticker].sort_values(by="date").reset_index(drop=True)
        return stock_df
