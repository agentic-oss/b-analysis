"""
Abstract base class and implementation for market data providers.
"""
from abc import ABC, abstractmethod
import datetime
import logging
import time
from typing import Dict, Any, Optional, List
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract interface for market data providers."""

    @abstractmethod
    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Fetch historical daily OHLCV price data.
        Returns DataFrame with columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbol: str) -> pd.DataFrame:
        """Fetch latest price data for a symbol."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        """
        Fetch corporate actions (dividends, splits).
        Returns DataFrame with date index and action details.
        """
        pass

    @abstractmethod
    def get_index_data(
        self, index_symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch index price history."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance market data provider implementation with retries and exception handling."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0, timeout: int = 15):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def _retry_fetch(self, fetch_func, *args, **kwargs) -> Any:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = fetch_func(*args, **kwargs)
                if result is not None and not (isinstance(result, pd.DataFrame) and result.empty):
                    return result
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries}: Empty data returned for {args} {kwargs}"
                )
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed with error: {e}"
                )
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)
        if last_exception:
            logger.error(f"Failed after {self.max_retries} attempts: {last_exception}")
        return pd.DataFrame()

    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch daily historical price data from Yahoo Finance."""
        def _fetch():
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            # Standardize column names
            col_map = {
                "Date": "Date",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Adj Close": "Adj Close",
                "Volume": "Volume"
            }
            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]
            cols = [c for c in col_map.keys() if c in df.columns]
            df = df[cols]
            # Convert Date column to string YYYY-MM-DD
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            return df

        df = self._retry_fetch(_fetch)
        return df

    def get_latest_prices(self, symbol: str) -> pd.DataFrame:
        end_dt = datetime.date.today() + datetime.timedelta(days=1)
        start_dt = end_dt - datetime.timedelta(days=7)
        return self.get_historical_prices(
            symbol, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
        )

    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        """Fetch corporate actions (Dividends and Stock Splits)."""
        def _fetch():
            ticker = yf.Ticker(symbol)
            actions = ticker.actions
            if actions is None or actions.empty:
                return pd.DataFrame(columns=["Date", "Dividends", "Stock Splits"])
            actions = actions.reset_index()
            actions["Date"] = pd.to_datetime(actions["Date"]).dt.strftime("%Y-%m-%d")
            return actions

        df = self._retry_fetch(_fetch)
        if df.empty:
            return pd.DataFrame(columns=["Date", "Dividends", "Stock Splits"])
        return df

    def get_index_data(
        self, index_symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        return self.get_historical_prices(index_symbol, start_date, end_date)
