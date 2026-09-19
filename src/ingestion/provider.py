"""
Market Data Provider Abstract Base Class and Implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract interface for stock and index market data providers."""

    @abstractmethod
    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch historical daily OHLCV price data for a stock or index.
        Returns DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        """
        pass

    @abstractmethod
    def get_corporate_actions(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch corporate actions (dividends, splits).
        Returns DataFrame with columns: ['date', 'dividends', 'splits']
        """
        pass

    @abstractmethod
    def get_fundamental_summary(self, symbol: str) -> Dict[str, Any]:
        """Fetch key fundamental indicators for a symbol."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance Data Provider implementation with retry logic."""

    def __init__(self, max_retries: int = 3, retry_backoff_sec: float = 2.0):
        self.max_retries = max_retries
        self.retry_backoff_sec = retry_backoff_sec

    def _execute_with_retry(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {func.__name__}: {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_sec * attempt)
        logger.error(f"Failed after {self.max_retries} retries.")
        raise last_exception

    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        def fetch():
            ticker = yf.Ticker(symbol)
            # Adjust end_date to include the date itself in yfinance download if needed
            end_dt = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            df = ticker.history(start=start_date, end=end_dt, auto_adjust=False)
            if df.empty:
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])

            df = df.reset_index()
            # Normalize column names
            col_map = {
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            }
            df = df.rename(columns=col_map)

            if 'adj_close' not in df.columns:
                df['adj_close'] = df['close']

            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            required_cols = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
            df = df[[c for c in required_cols if c in df.columns]]
            return df.sort_values('date').reset_index(drop=True)

        try:
            return self._execute_with_retry(fetch)
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])

    def get_corporate_actions(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        def fetch():
            ticker = yf.Ticker(symbol)
            actions = ticker.actions
            if actions is None or actions.empty:
                return pd.DataFrame(columns=['date', 'dividends', 'splits'])
            actions = actions.reset_index()
            actions = actions.rename(columns={'Date': 'date', 'Dividends': 'dividends', 'Stock Splits': 'splits'})
            actions['date'] = pd.to_datetime(actions['date']).dt.strftime('%Y-%m-%d')
            actions = actions[(actions['date'] >= start_date) & (actions['date'] <= end_date)]
            return actions[['date', 'dividends', 'splits']].reset_index(drop=True)

        try:
            return self._execute_with_retry(fetch)
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'dividends', 'splits'])

    def get_fundamental_summary(self, symbol: str) -> Dict[str, Any]:
        def fetch():
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            metrics = {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"), # Proxy or standard asset return if ROCE not present
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_growth": info.get("earningsGrowth"),
                "ebitda_margins": info.get("ebitdaMargins"),
                "net_margins": info.get("profitMargins"),
                "dividend_yield": info.get("dividendYield"),
                "free_cash_flow": info.get("freeCashflow"),
                "promoter_holding": None,
                "institutional_ownership": info.get("heldPercentInstitutions"),
                "fetch_timestamp": datetime.now().isoformat(),
                "data_provider": "yfinance"
            }
            return metrics

        try:
            return self._execute_with_retry(fetch)
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {
                "fetch_timestamp": datetime.now().isoformat(),
                "data_provider": "yfinance",
                "error": str(e)
            }
