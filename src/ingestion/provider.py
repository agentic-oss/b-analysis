"""
Abstract base class and models for Market Data Provider.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd


class MarketDataProvider(ABC):
    """
    Abstract interface for fetching stock and index market data.
    """

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y",
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """
        Fetch historical price observations (OHLCV, VWAP, etc.).
        Returns a pandas DataFrame with datetime index or 'Date' column.
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Fetch the most recent daily price snapshot.
        """
        pass

    @abstractmethod
    def get_volume_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """
        Fetch volume and deliverable quantity data if available.
        """
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str, exchange: str = "NSE") -> Dict[str, pd.DataFrame]:
        """
        Fetch dividends and splits history.
        """
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Fetch historical data for a market index (e.g. ^NSEI, ^NSEBANK).
        """
        pass
