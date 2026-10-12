"""
Abstract base class and interface for market data providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class MarketDataProvider(ABC):
    """
    Abstract interface for fetching Indian stock market data, indices, volume data,
    corporate actions, and fundamental financial metrics.
    """

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV price history for a given symbol.
        Returned DataFrame should include columns:
        ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Ticker']
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch latest available daily prices for a list of symbols.
        """
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch corporate actions (dividends, splits, bonuses) for a symbol.
        """
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y",
    ) -> pd.DataFrame:
        """
        Fetch historical price data for a stock market index.
        """
        pass

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental indicators and metrics for a stock.
        """
        pass
