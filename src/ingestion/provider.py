import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_historical_prices(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical daily OHLCV data."""
        pass

    @abstractmethod
    def get_latest_prices(self, ticker: str) -> pd.DataFrame:
        """Fetch latest daily OHLCV data."""
        pass

    @abstractmethod
    def get_volume_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch volume and trading activity data."""
        pass

    @abstractmethod
    def get_corporate_actions(self, ticker: str) -> pd.DataFrame:
        """Fetch dividends and splits."""
        pass

    @abstractmethod
    def get_index_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical index price data."""
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch company fundamental metrics."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance market data provider implementation with retry logic and error handling."""

    def __init__(self, max_retries: int = 3, retry_backoff: float = 2.0, timeout: int = 15):
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout

    def _download_with_retry(self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Helper to download historical data with retries."""
        for attempt in range(1, self.max_retries + 1):
            try:
                stock = yf.Ticker(ticker)
                if start_date and end_date:
                    df = stock.history(start=start_date, end=end_date, auto_adjust=False, timeout=self.timeout)
                else:
                    df = stock.history(period="1mo", auto_adjust=False, timeout=self.timeout)

                if df is not None and not df.empty:
                    df = df.reset_index()
                    # Ensure Date column is standard YYYY-MM-DD string or datetime
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
                    return df
                else:
                    logger.warning(f"Attempt {attempt}: Empty data returned for {ticker}")
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {ticker}: {str(e)}")
            time.sleep(self.retry_backoff * attempt)

        logger.error(f"Failed to fetch data for {ticker} after {self.max_retries} attempts.")
        return pd.DataFrame()

    def get_historical_prices(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        df = self._download_with_retry(ticker, start_date, end_date)
        if df.empty:
            return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])

        # Standardize columns
        col_map = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume', 'Date': 'date'}
        # Handle cases where Adj Close might be missing
        if 'Adj Close' not in df.columns and 'Close' in df.columns:
            df['Adj Close'] = df['Close']

        df = df.rename(columns=col_map)
        needed = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        existing = [c for c in needed if c in df.columns]
        return df[existing]

    def get_latest_prices(self, ticker: str) -> pd.DataFrame:
        df = self._download_with_retry(ticker)
        if df.empty:
            return pd.DataFrame()
        col_map = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume', 'Date': 'date'}
        if 'Adj Close' not in df.columns and 'Close' in df.columns:
            df['Adj Close'] = df['Close']
        df = df.rename(columns=col_map)
        return df.tail(1)

    def get_volume_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        df = self.get_historical_prices(ticker, start_date, end_date)
        if df.empty:
            return pd.DataFrame()
        return df[['date', 'volume', 'close']]

    def get_corporate_actions(self, ticker: str) -> pd.DataFrame:
        for attempt in range(1, self.max_retries + 1):
            try:
                stock = yf.Ticker(ticker)
                actions = stock.actions
                if actions is not None and not actions.empty:
                    actions = actions.reset_index()
                    actions['Date'] = pd.to_datetime(actions['Date']).dt.tz_localize(None)
                    actions = actions.rename(columns={'Date': 'date', 'Dividends': 'dividends', 'Stock Splits': 'splits'})
                    return actions
                return pd.DataFrame(columns=['date', 'dividends', 'splits'])
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for corporate actions {ticker}: {str(e)}")
                time.sleep(self.retry_backoff * attempt)
        return pd.DataFrame(columns=['date', 'dividends', 'splits'])

    def get_index_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_historical_prices(ticker, start_date, end_date)

    def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            return {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"), # Proxy if ROCE not available directly
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_growth": info.get("earningsGrowth"),
                "ebitda_margins": info.get("ebitdaMargins"),
                "net_margins": info.get("profitMargins"),
                "dividend_yield": info.get("dividendYield"),
                "free_cash_flow": info.get("freeCashflow"),
                "promoter_holding": info.get("heldPercentInsiders"),
                "institutional_holding": info.get("heldPercentInstitutions"),
                "data_source": "yfinance"
            }
        except Exception as e:
            logger.warning(f"Failed to fetch fundamentals for {ticker}: {str(e)}")
            return {}
