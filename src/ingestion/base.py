import abc
from typing import Dict, Any, Optional
import pandas as pd

class MarketDataProvider(abc.ABC):
    """Abstract Base Class for Indian Stock Market Data Providers."""

    @abc.abstractmethod
    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical daily OHLCV prices for a stock or index.
        Returns DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume, Symbol, Provider, IngestionTimestamp.
        """
        pass

    @abc.abstractmethod
    def get_latest_prices(self, symbols: list) -> pd.DataFrame:
        """Fetch latest daily prices for a list of symbols."""
        pass

    @abc.abstractmethod
    def get_volume_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical volume, turnover, deliverable quantity and delivery % where available."""
        pass

    @abc.abstractmethod
    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        """Fetch splits, bonuses, dividends for a symbol."""
        pass

    @abc.abstractmethod
    def get_index_data(self, index_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical index values."""
        pass

    @abc.abstractmethod
    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental data key-value metrics for a stock."""
        pass
