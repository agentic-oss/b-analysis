"""
Market Data Provider Abstraction and Implementation for Yahoo Finance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import logging
import time
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract Base Class for Market Data Providers."""

    @abstractmethod
    def get_historical_prices(
        self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Fetch historical daily price data (Open, High, Low, Close, Adj Close, Volume)."""
        pass

    @abstractmethod
    def get_latest_prices(self, tickers: List[str]) -> pd.DataFrame:
        """Fetch latest price data for a list of tickers."""
        pass

    @abstractmethod
    def get_corporate_actions(self, ticker: str) -> pd.DataFrame:
        """Fetch corporate actions (dividends, splits)."""
        pass

    @abstractmethod
    def get_index_data(
        self, index_symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Fetch historical index daily data."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance implementation with retries, backoff, and error handling."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5, timeout: int = 15):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    def _download_with_retry(self, ticker: str, start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
        attempt = 0
        last_error = None
        while attempt < self.max_retries:
            try:
                logger.info(f"Downloading data for {ticker} (Attempt {attempt + 1}/{self.max_retries})")
                yf_ticker = yf.Ticker(ticker)

                # Use history with date bounds or max period
                if start_date and end_date:
                    df = yf_ticker.history(start=start_date, end=end_date, auto_adjust=False, timeout=self.timeout)
                elif start_date:
                    df = yf_ticker.history(start=start_date, auto_adjust=False, timeout=self.timeout)
                else:
                    df = yf_ticker.history(period="2y", auto_adjust=False, timeout=self.timeout)

                if df.empty:
                    logger.warning(f"Empty dataframe returned for ticker: {ticker}")
                    return pd.DataFrame()

                # Clean and standardize columns
                df = df.reset_index()
                # Ensure Date is timezone naive string or standard format
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

                # Standardize column naming
                column_mapping = {
                    "Date": "date",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                    "Stock Splits": "splits",
                    "Dividends": "dividends",
                }
                df = df.rename(columns=column_mapping)

                # Standardize required columns
                required_cols = ["date", "open", "high", "low", "close", "adj_close", "volume"]
                for col in required_cols:
                    if col not in df.columns:
                        if col == "adj_close" and "close" in df.columns:
                            df["adj_close"] = df["close"]
                        else:
                            df[col] = None

                df["date"] = df["date"].dt.strftime("%Y-%m-%d")
                return df[required_cols]

            except Exception as e:
                last_error = e
                logger.error(f"Error fetching data for {ticker}: {e}")
                attempt += 1
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor ** attempt
                    time.sleep(sleep_time)

        logger.error(f"Failed to fetch data for {ticker} after {self.max_retries} attempts. Last error: {last_error}")
        return pd.DataFrame()

    def get_historical_prices(
        self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        return self._download_with_retry(ticker, start_date, end_date)

    def get_latest_prices(self, tickers: List[str]) -> pd.DataFrame:
        results = []
        for ticker in tickers:
            df = self.get_historical_prices(ticker)
            if not df.empty:
                latest = df.iloc[-1:].copy()
                latest["ticker"] = ticker
                results.append(latest)
        if results:
            return pd.concat(results, ignore_index=True)
        return pd.DataFrame()

    def get_corporate_actions(self, ticker: str) -> pd.DataFrame:
        try:
            yf_ticker = yf.Ticker(ticker)
            actions = yf_ticker.actions
            if actions is not None and not actions.empty:
                actions = actions.reset_index()
                if "Date" in actions.columns:
                    actions["date"] = pd.to_datetime(actions["Date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                actions = actions.rename(columns={"Dividends": "dividends", "Stock Splits": "splits"})
                return actions[["date", "dividends", "splits"]]
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {ticker}: {e}")
        return pd.DataFrame(columns=["date", "dividends", "splits"])

    def get_index_data(
        self, index_symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        return self.get_historical_prices(index_symbol, start_date, end_date)
