"""Yahoo Finance Data Provider for Indian Stocks and Indices."""

import logging
import time
import pandas as pd
import yfinance as yf
from typing import List, Optional
from src.ingestion.provider import MarketDataProvider
from src.ingestion.mock_provider import MockMarketDataProvider

logger = logging.getLogger(__name__)

class YahooFinanceProvider(MarketDataProvider):
    """Fetches market data from Yahoo Finance with retries and rate-limiting."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, fallback_to_mock: bool = True):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fallback_to_mock = fallback_to_mock
        self.mock_provider = MockMarketDataProvider()

    def _fetch_with_retry(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        for attempt in range(1, self.max_retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
                if not df.empty:
                    df = df.reset_index()
                    # Standardize column names
                    cols_map = {
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Adj Close': 'adj_close',
                        'Volume': 'volume'
                    }
                    df = df.rename(columns=cols_map)
                    if 'adj_close' not in df.columns and 'close' in df.columns:
                        df['adj_close'] = df['close']

                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                    df['ticker'] = symbol
                    df['provider'] = 'yfinance'

                    req_cols = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'ticker', 'provider']
                    df = df[[c for c in req_cols if c in df.columns]]
                    return df
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {symbol}: {e}")
                time.sleep(self.retry_delay * attempt)

        logger.error(f"Failed to fetch {symbol} after {self.max_retries} attempts.")
        if self.fallback_to_mock:
            logger.info(f"Using mock data fallback for {symbol}")
            return self.mock_provider.get_historical_prices(symbol, start_date, end_date)
        return pd.DataFrame()

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self._fetch_with_retry(symbol, start_date, end_date)

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        dfs = []
        for sym in symbols:
            df = self._fetch_with_retry(sym, start_date=None, end_date=None)
            if not df.empty:
                dfs.append(df.tail(1))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def get_volume_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date)
        if not df.empty:
            # Deliverable volume is not directly available in standard yfinance, so estimate if needed
            df['deliverable_volume'] = (df['volume'] * 0.5).astype(int)
            df['delivery_percentage'] = 50.0
        return df

    def get_corporate_actions(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            ticker = yf.Ticker(symbol)
            actions = ticker.actions
            if actions is not None and not actions.empty:
                actions = actions.reset_index()
                actions['Date'] = pd.to_datetime(actions['Date']).dt.strftime('%Y-%m-%d')
                actions['ticker'] = symbol
                return actions
        except Exception as e:
            logger.warning(f"Error fetching corporate actions for {symbol}: {e}")
        return pd.DataFrame(columns=['Date', 'Dividends', 'Stock Splits', 'ticker'])

    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_historical_prices(symbol, start_date, end_date)
