from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd


class MarketDataProvider(ABC):
    """
    Abstract Base Class for market data ingestion providers.
    Supports extensible providers (e.g. yfinance, NSE API, custom mock/offline).
    """

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = "2y",
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a stock or index symbol.
        Returns DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume, VWAP, Deliverable Volume (if available).
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch the most recent daily price record for a list of symbols.
        """
        pass

    @abstractmethod
    def get_volume_data(self, symbol: str, period: str = "1m") -> pd.DataFrame:
        """
        Fetch volume and turnover/delivery details for a symbol if available.
        """
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch corporate actions (dividends, splits, bonuses).
        """
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical price data for market/sector indices.
        """
        pass
