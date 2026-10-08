import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """
    Abstract Base Class for market data providers.
    Provides standard interface for fetching equities and indices historical prices,
    latest quotes, volume data, and corporate actions.
    """

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch historical price data (Date, Open, High, Low, Close, Adj Close, Volume, VWAP, etc.)."""
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch latest market quotes for a list of symbols."""
        pass

    @abstractmethod
    def get_volume_data(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Fetch volume and deliverable quantity details if available."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        """Fetch corporate actions including dividends, splits, and bonuses."""
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch index historical performance."""
        pass
