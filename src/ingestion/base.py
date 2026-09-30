from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import datetime
import time
import logging

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    """

    @abstractmethod
    def get_historical_prices(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch historical price data for a stock symbol.
        Returns DataFrame with columns: date, open, high, low, close, adj_close, volume, turnover, vwap.
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch latest prices for a list of symbols.
        """
        pass

    @abstractmethod
    def get_volume_data(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch volume data including deliverable quantity if available.
        """
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch corporate actions (dividends, splits, bonuses).
        """
        pass

    @abstractmethod
    def get_index_data(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch index historical price data.
        """
        pass

    @abstractmethod
    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental metrics for a stock symbol.
        """
        pass
