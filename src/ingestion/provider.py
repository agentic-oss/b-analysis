"""
Market Data Provider Interface and Implementation.
Provides an abstraction layer for fetching Indian equities and indices market data.
"""

import abc
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(abc.ABC):
    """Abstract base class for market data providers."""

    @abc.abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch historical price data for a stock."""
        pass

    @abc.abstractmethod
    def get_latest_prices(
        self,
        symbol: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch the latest price data for a stock."""
        pass

    @abc.abstractmethod
    def get_volume_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch volume and delivery data for a stock."""
        pass

    @abc.abstractmethod
    def get_corporate_actions(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch dividends and stock splits for a stock."""
        pass

    @abc.abstractmethod
    def get_index_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Fetch historical data for a market or sector index."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance implementation of MarketDataProvider."""

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.provider_name = "yfinance"

    def _resolve_ticker(
        self,
        symbol: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> str:
        """Helper to resolve symbol to yfinance ticker."""
        if ticker_override:
            return ticker_override
        if symbol.startswith("^"):
            return symbol
        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        return f"{symbol}{suffix}"

    def _execute_with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Executes a function with retry logic and exponential backoff."""
        attempt = 0
        last_exception = None
        while attempt < self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed: {e}. Retrying..."
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff_factor ** attempt)
        logger.error(f"Failed after {self.max_retries} attempts: {last_exception}")
        raise last_exception

    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        ticker_str = self._resolve_ticker(symbol, exchange, ticker_override)

        def _fetch():
            ticker_obj = yf.Ticker(ticker_str)
            df = ticker_obj.history(start=start_date, end=end_date, auto_adjust=False)
            return df

        try:
            df = self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return pd.DataFrame()

        if df.empty:
            logger.warning(f"No price data returned for {symbol} ({ticker_str}) between {start_date} and {end_date}")
            return pd.DataFrame()

        df = df.reset_index()
        # Rename columns to standard schema
        rename_map = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
        df = df.rename(columns=rename_map)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        if "adj_close" not in df.columns and "close" in df.columns:
            df["adj_close"] = df["close"]

        # Calculate VWAP estimate: sum(Typical Price * Volume) / sum(Volume) or (High + Low + Close)/3
        df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0
        df["turnover"] = df["vwap"] * df["volume"]
        df["deliverable_qty"] = np.nan
        df["delivery_pct"] = np.nan

        # Metadata
        df["ticker"] = symbol
        df["exchange"] = exchange
        df["provider"] = self.provider_name
        df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

        cols = [
            "ticker",
            "exchange",
            "date",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "vwap",
            "turnover",
            "deliverable_qty",
            "delivery_pct",
            "provider",
            "ingestion_timestamp",
        ]
        available_cols = [c for c in cols if c in df.columns]
        return df[available_cols]

    def get_latest_prices(
        self,
        symbol: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        today_str = datetime.now().strftime("%Y-%m-%d")
        # Get historical for last 5 calendar days to ensure catching latest trading day
        start_str = (pd.Timestamp.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        df = self.get_historical_prices(symbol, start_date=start_str, end_date=today_str, exchange=exchange, ticker_override=ticker_override)
        if df.empty:
            return pd.DataFrame()
        return df.tail(1)

    def get_volume_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date, exchange, ticker_override)
        if df.empty:
            return pd.DataFrame()
        return df[["ticker", "date", "volume", "vwap", "turnover", "deliverable_qty", "delivery_pct"]]

    def get_corporate_actions(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE",
        ticker_override: Optional[str] = None,
    ) -> pd.DataFrame:
        ticker_str = self._resolve_ticker(symbol, exchange, ticker_override)

        def _fetch():
            t = yf.Ticker(ticker_str)
            actions = t.actions
            return actions

        try:
            actions = self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {e}")
            return pd.DataFrame()

        if actions is None or actions.empty:
            return pd.DataFrame(columns=["ticker", "exchange", "date", "dividends", "stock_splits", "provider", "ingestion_timestamp"])

        actions = actions.reset_index()
        actions["date"] = pd.to_datetime(actions["Date"]).dt.strftime("%Y-%m-%d")
        actions = actions[(actions["date"] >= start_date) & (actions["date"] <= end_date)]

        actions = actions.rename(columns={"Dividends": "dividends", "Stock Splits": "stock_splits"})
        actions["ticker"] = symbol
        actions["exchange"] = exchange
        actions["provider"] = self.provider_name
        actions["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

        cols = ["ticker", "exchange", "date", "dividends", "stock_splits", "provider", "ingestion_timestamp"]
        available = [c for c in cols if c in actions.columns]
        return actions[available]

    def get_index_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        return self.get_historical_prices(symbol, start_date, end_date, exchange="INDEX", ticker_override=symbol)
