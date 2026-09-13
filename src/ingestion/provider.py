from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    @abstractmethod
    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical OHLCV data for a given symbol."""
        pass

    @abstractmethod
    def get_latest_prices(self, symbol: str) -> pd.DataFrame:
        """Fetch the latest available prices for a given symbol."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        """Fetch dividends and stock splits for a given symbol."""
        pass

    @abstractmethod
    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch index data for a given symbol."""
        pass


class YFinanceProvider(MarketDataProvider):
    def __init__(self, max_retries: int = 3, retry_backoff: float = 1.5, timeout: int = 30):
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout

    def _fetch_with_retry(self, symbol: str, fetch_func) -> Any:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = fetch_func()
                if isinstance(result, pd.DataFrame) and result.empty:
                    logger.warning(f"Attempt {attempt}: Empty data received for symbol {symbol}")
                else:
                    return result
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {symbol}: {str(e)}")
                last_exception = e
            time.sleep(self.retry_backoff ** attempt)

        if last_exception:
            raise last_exception
        return pd.DataFrame()

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        def _fetch():
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                return pd.DataFrame()

            df = df.reset_index()
            # Normalize column names
            rename_dict = {
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume',
                'Dividends': 'dividends',
                'Stock Splits': 'splits'
            }
            df = df.rename(columns=rename_dict)
            if 'adj_close' not in df.columns:
                df['adj_close'] = df['close']

            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
            cols = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
            existing_cols = [c for c in cols if c in df.columns]
            return df[existing_cols]

        return self._fetch_with_retry(symbol, _fetch)

    def get_latest_prices(self, symbol: str) -> pd.DataFrame:
        def _fetch():
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='5d', auto_adjust=False)
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            rename_dict = {
                'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
            }
            df = df.rename(columns=rename_dict)
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
            return df

        return self._fetch_with_retry(symbol, _fetch)

    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        def _fetch():
            ticker = yf.Ticker(symbol)
            actions = ticker.actions
            if actions is None or actions.empty:
                return pd.DataFrame(columns=['date', 'dividends', 'splits'])
            actions = actions.reset_index()
            actions['date'] = pd.to_datetime(actions['Date']).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
            actions = actions.rename(columns={'Dividends': 'dividends', 'Stock Splits': 'splits'})
            return actions[['date', 'dividends', 'splits']]

        return self._fetch_with_retry(symbol, _fetch)

    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_historical_prices(symbol, start_date, end_date)
