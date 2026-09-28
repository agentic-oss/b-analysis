from abc import ABC, abstractmethod
import time
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import yfinance as yf

logger = logging.getLogger("ingestion.provider")

class MarketDataProvider(ABC):
    """Abstract Base Class for Market Data Ingestion Providers."""

    @abstractmethod
    def get_historical_prices(self, symbol: str, exchange: str = "NSE", start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Fetch daily historical OHLCV data."""
        pass

    @abstractmethod
    def get_latest_prices(self, symbol: str, exchange: str = "NSE") -> pd.DataFrame:
        """Fetch the latest available price data."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str, exchange: str = "NSE") -> pd.DataFrame:
        """Fetch corporate actions (dividends, splits)."""
        pass

    @abstractmethod
    def get_index_data(self, yahoo_ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Fetch index OHLCV data."""
        pass

    @abstractmethod
    def get_fundamentals(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Fetch fundamental metrics for a stock."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance implementation of MarketDataProvider."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _ticker_symbol(self, symbol: str, exchange: str) -> str:
        symbol = symbol.strip().upper()
        if symbol.startswith("^") or symbol.endswith(".NS") or symbol.endswith(".BO"):
            return symbol
        if exchange == "BSE":
            return f"{symbol}.BO"
        return f"{symbol}.NS"

    def _fetch_with_retry(self, fetch_func, *args, **kwargs) -> Any:
        for attempt in range(1, self.max_retries + 1):
            try:
                res = fetch_func(*args, **kwargs)
                if res is not None and not (isinstance(res, pd.DataFrame) and res.empty):
                    return res
                if res is not None and isinstance(res, pd.DataFrame) and res.empty:
                    logger.warning(f"Attempt {attempt}: Download returned empty DataFrame for args {args}")
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed with error: {e}")
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)
        logger.error(f"Failed to fetch data after {self.max_retries} attempts for {args}")
        return pd.DataFrame()

    def get_historical_prices(self, symbol: str, exchange: str = "NSE", start_date: str = None, end_date: str = None) -> pd.DataFrame:
        ticker_str = self._ticker_symbol(symbol, exchange)

        def _download():
            ticker = yf.Ticker(ticker_str)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            # Standardize column names
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
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            df['symbol'] = symbol
            df['exchange'] = exchange
            df['provider'] = 'yfinance'

            # Ensure required columns exist
            for col in ['open', 'high', 'low', 'close', 'adj_close', 'volume']:
                if col not in df.columns:
                    df[col] = 0.0
            if 'adj_close' not in df.columns or df['adj_close'].isnull().all():
                df['adj_close'] = df['close']

            # Delivery volume & percentage estimates if available
            df['turnover'] = df['close'] * df['volume']
            df['vwap'] = (df['high'] + df['low'] + df['close']) / 3.0
            return df[['date', 'symbol', 'exchange', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'turnover', 'vwap', 'provider']]

        return self._fetch_with_retry(_download)

    def get_latest_prices(self, symbol: str, exchange: str = "NSE") -> pd.DataFrame:
        return self.get_historical_prices(symbol, exchange, start_date=None, end_date=None)

    def get_corporate_actions(self, symbol: str, exchange: str = "NSE") -> pd.DataFrame:
        ticker_str = self._ticker_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(ticker_str)
            actions = ticker.actions
            if actions is None or actions.empty:
                return pd.DataFrame(columns=['date', 'symbol', 'dividends', 'stock_splits'])
            actions = actions.reset_index()
            actions['date'] = pd.to_datetime(actions['Date']).dt.strftime('%Y-%m-%d')
            actions['symbol'] = symbol
            actions = actions.rename(columns={'Dividends': 'dividends', 'Stock Splits': 'stock_splits'})
            return actions[['date', 'symbol', 'dividends', 'stock_splits']]
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'symbol', 'dividends', 'stock_splits'])

    def get_index_data(self, yahoo_ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        return self.get_historical_prices(yahoo_ticker, exchange="NSE", start_date=start_date, end_date=end_date)

    def get_fundamentals(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        ticker_str = self._ticker_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(ticker_str)
            info = ticker.info or {}
            return {
                "symbol": symbol,
                "exchange": exchange,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"), # fallback
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margins": info.get("profitMargins"),
                "gross_margins": info.get("grossMargins"),
                "ebitda_margins": info.get("ebitdaMargins"),
                "dividend_yield": info.get("dividendYield"),
                "free_cash_flow": info.get("freeCashflow"),
                "promoter_holding": info.get("heldPercentInsiders"),
                "institutional_ownership": info.get("heldPercentInstitutions"),
                "provider": "yfinance"
            }
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {"symbol": symbol, "exchange": exchange, "error": str(e)}
