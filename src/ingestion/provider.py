"""Abstract Market Data Provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class MarketDataProvider(ABC):
    """Abstract base class for all market data providers."""

    @abstractmethod
    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical daily OHLCV prices for a stock or index.

        Returns DataFrame with columns:
        ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: list) -> pd.DataFrame:
        """Fetch latest market snapshot for a list of symbols."""
        pass

    @abstractmethod
    def get_volume_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch volume and deliverable volume data if available."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch dividends, stock splits, bonuses."""
        pass

    @abstractmethod
    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch index prices and composition updates."""
        pass
