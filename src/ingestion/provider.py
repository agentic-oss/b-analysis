import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_historical_prices(self, ticker: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch historical daily OHLCV data."""
        pass

    @abstractmethod
    def get_latest_prices(self, ticker: str) -> pd.DataFrame:
        """Fetch recent intra-day or latest daily prices."""
        pass

    @abstractmethod
    def get_corporate_actions(self, ticker: str) -> pd.DataFrame:
        """Fetch dividends and splits data."""
        pass

    @abstractmethod
    def get_index_data(self, index_symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch index daily OHLCV data."""
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch fundamental metrics where available."""
        pass


class YFinanceProvider(MarketDataProvider):
    """yfinance market data provider implementation with retries, logging, and error handling."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5, timeout: int = 30):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        import yfinance as yf
        self.yf = yf

    def _retry_fetch(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    if isinstance(result, (pd.DataFrame, pd.Series)) and result.empty:
                        logger.warning(f"Empty data returned on attempt {attempt}")
                    else:
                        return result
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed with error: {e}")
                last_exception = e
            time.sleep(self.backoff_factor ** attempt)

        logger.error(f"All {self.max_retries} attempts failed. Last exception: {last_exception}")
        return pd.DataFrame()

    def get_historical_prices(self, ticker: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        logger.info(f"Fetching historical prices for {ticker} from {start_date} to {end_date}")

        def _fetch():
            t = self.yf.Ticker(ticker)
            df = t.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                return df

            # Reset index to make Date a column
            df = df.reset_index()
            # Standardize columns
            col_map = {
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
                "Stock Splits": "splits",
                "Dividends": "dividends"
            }
            df = df.rename(columns=col_map)

            if "adj_close" not in df.columns and "close" in df.columns:
                df["adj_close"] = df["close"]

            # Normalize date column to YYYY-MM-DD format string/datetime
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

            required_cols = ["date", "open", "high", "low", "close", "adj_close", "volume"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = np.nan

            df["ticker"] = ticker
            df["provider"] = "yfinance"
            return df[required_cols + ["ticker", "provider"]]

        res = self._retry_fetch(_fetch)
        return res if isinstance(res, pd.DataFrame) else pd.DataFrame()

    def get_latest_prices(self, ticker: str) -> pd.DataFrame:
        # Fetch last 5 days
        return self.get_historical_prices(ticker, start_date=pd.Timestamp.now().sub(pd.Timedelta(days=5)).strftime("%Y-%m-%d"))

    def get_corporate_actions(self, ticker: str) -> pd.DataFrame:
        logger.info(f"Fetching corporate actions for {ticker}")
        def _fetch():
            t = self.yf.Ticker(ticker)
            actions = t.actions
            if actions is None or actions.empty:
                return pd.DataFrame(columns=["date", "dividends", "splits", "ticker"])
            actions = actions.reset_index()
            actions = actions.rename(columns={"Date": "date", "Dividends": "dividends", "Stock Splits": "splits"})
            actions["date"] = pd.to_datetime(actions["date"]).dt.strftime("%Y-%m-%d")
            actions["ticker"] = ticker
            return actions
        res = self._retry_fetch(_fetch)
        return res if isinstance(res, pd.DataFrame) else pd.DataFrame()

    def get_index_data(self, index_symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        return self.get_historical_prices(index_symbol, start_date=start_date, end_date=end_date)

    def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        logger.info(f"Fetching fundamental data for {ticker}")
        def _fetch():
            t = self.yf.Ticker(ticker)
            info = t.info
            if not info:
                return {}

            # Map common metrics
            return {
                "ticker": ticker,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"), # Proxy or fallback if ROCE not available directly
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_growth": info.get("earningsGrowth"),
                "ebitda_margin": info.get("ebitdaMargins"),
                "net_margin": info.get("profitMargins"),
                "dividend_yield": info.get("dividendYield"),
                "free_cash_flow": info.get("freeCashflow"),
                "promoter_holding": info.get("heldPercentInsiders"),
                "institutional_ownership": info.get("heldPercentInstitutions"),
                "source": "yfinance",
                "timestamp": pd.Timestamp.now().isoformat()
            }

        try:
            return self._retry_fetch(_fetch) or {}
        except Exception as e:
            logger.error(f"Failed to fetch fundamental data for {ticker}: {e}")
            return {}
