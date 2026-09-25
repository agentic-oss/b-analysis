"""Market Data Provider Abstraction and Implementations."""

from abc import ABC, abstractmethod
import logging
import time
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch historical price and volume data for a single symbol."""
        pass

    @abstractmethod
    def get_latest_prices(
        self,
        symbols: List[str],
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch latest daily prices for a list of symbols."""
        pass

    @abstractmethod
    def get_corporate_actions(
        self,
        symbol: str,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch corporate actions (dividends, splits) for a symbol."""
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Fetch index prices and volume data."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance implementation of MarketDataProvider."""

    def __init__(
        self,
        retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 30
    ):
        self.retries = retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def _format_ticker(self, symbol: str, exchange: str = "NSE") -> str:
        """Format symbol with Yahoo Finance exchange suffix if applicable."""
        symbol = symbol.strip().upper()
        if symbol.startswith("^") or "." in symbol:
            return symbol
        if exchange.upper() == "NSE":
            return f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            return f"{symbol}.BO"
        return symbol

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute a callable with exponential backoff retries."""
        last_exception = None
        for attempt in range(1, self.retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.retries} failed with error: {e}. "
                    f"Retrying in {self.retry_delay * attempt}s..."
                )
                time.sleep(self.retry_delay * attempt)
        logger.error(f"Failed after {self.retries} attempts: {last_exception}")
        raise last_exception

    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch historical prices for stock symbol."""
        ticker_str = self._format_ticker(symbol, exchange)

        def _fetch():
            ticker = yf.Ticker(ticker_str)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                logger.warning(f"No historical data found for {ticker_str}")
                return pd.DataFrame()

            df = df.reset_index()
            # Normalize column names
            rename_map = {
                "Date": "Date",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Adj Close": "Adj Close",
                "Volume": "Volume"
            }
            df = df.rename(columns=rename_map)

            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]

            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
            df["Ticker"] = symbol.upper()
            df["Exchange"] = exchange.upper()
            df["Provider"] = "yfinance"

            required_cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "Ticker", "Exchange", "Provider"]
            available_cols = [col for col in required_cols if col in df.columns]
            return df[available_cols]

        return self._execute_with_retry(_fetch)

    def get_latest_prices(
        self,
        symbols: List[str],
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch latest daily prices for given symbols."""
        dfs = []
        for sym in symbols:
            try:
                ticker_str = self._format_ticker(sym, exchange)
                ticker = yf.Ticker(ticker_str)
                df = ticker.history(period="5d", auto_adjust=False)
                if not df.empty:
                    df = df.reset_index()
                    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
                    df["Ticker"] = sym.upper()
                    df["Exchange"] = exchange.upper()
                    df["Provider"] = "yfinance"
                    if "Adj Close" not in df.columns:
                        df["Adj Close"] = df["Close"]
                    dfs.append(df.tail(1))
            except Exception as e:
                logger.error(f"Error fetching latest price for {sym}: {e}")

        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame()

    def get_corporate_actions(
        self,
        symbol: str,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch corporate actions (dividends and splits)."""
        ticker_str = self._format_ticker(symbol, exchange)

        def _fetch():
            ticker = yf.Ticker(ticker_str)
            actions = ticker.actions
            if actions is None or actions.empty:
                return pd.DataFrame(columns=["Date", "Dividends", "Stock Splits", "Ticker", "Exchange"])
            actions = actions.reset_index()
            actions["Date"] = pd.to_datetime(actions["Date"]).dt.tz_localize(None)
            actions["Ticker"] = symbol.upper()
            actions["Exchange"] = exchange.upper()
            return actions

        return self._execute_with_retry(_fetch)

    def get_index_data(
        self,
        index_symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Fetch index OHLCV data."""
        def _fetch():
            ticker = yf.Ticker(index_symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                logger.warning(f"No index data found for {index_symbol}")
                return pd.DataFrame()
            df = df.reset_index()
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
            df["Ticker"] = index_symbol.upper()
            df["Exchange"] = "INDEX"
            df["Provider"] = "yfinance"
            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]
            return df

        return self._execute_with_retry(_fetch)
