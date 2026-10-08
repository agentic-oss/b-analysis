import time
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf

from src.ingestion.provider import MarketDataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """
    Market Data Provider implementation using yfinance with retry logic and rate limit handling.
    """

    def __init__(self, max_retries: int = 3, retry_backoff: float = 2.0, timeout: float = 30.0):
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed for {func.__name__}: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * attempt)
        logger.error(f"All {self.max_retries} attempts failed.")
        raise last_exception

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        def _fetch():
            ticker = yf.Ticker(symbol)
            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, auto_adjust=False, actions=True)
            elif period:
                df = ticker.history(period=period, auto_adjust=False, actions=True)
            else:
                df = ticker.history(period="5y", auto_adjust=False, actions=True)

            if df.empty:
                logger.warning(f"No price data returned for symbol: {symbol}")
                return pd.DataFrame()

            df = df.reset_index()
            # Standardize date column
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

            # Standardize column names
            rename_map = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
                "Dividends": "dividends",
                "Stock Splits": "splits",
                "Date": "date"
            }
            df = df.rename(columns=rename_map)

            if "adj_close" not in df.columns and "close" in df.columns:
                df["adj_close"] = df["close"]

            # Calculate VWAP estimate: (High + Low + Close) / 3 if turnover not directly provided
            df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0

            # Optional columns
            if "turnover" not in df.columns:
                df["turnover"] = df["close"] * df["volume"]
            if "deliverable_qty" not in df.columns:
                df["deliverable_qty"] = None
            if "delivery_pct" not in df.columns:
                df["delivery_pct"] = None

            cols_order = [
                "date", "open", "high", "low", "close", "adj_close",
                "volume", "turnover", "deliverable_qty", "delivery_pct",
                "vwap", "dividends", "splits"
            ]
            available_cols = [c for c in cols_order if c in df.columns]
            return df[available_cols]

        return self._execute_with_retry(_fetch)

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for sym in symbols:
            try:
                df = self.get_historical_prices(sym, period="5d")
                if not df.empty:
                    latest = df.iloc[-1].to_dict()
                    results[sym] = latest
            except Exception as e:
                logger.error(f"Error fetching latest price for {sym}: {e}")
        return results

    def get_volume_data(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date=start_date, end_date=end_date)
        if df.empty:
            return pd.DataFrame()
        return df[["date", "volume", "turnover", "deliverable_qty", "delivery_pct"]]

    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, period="5y")
        if df.empty:
            return pd.DataFrame()
        ca_df = df[(df.get("dividends", 0) > 0) | (df.get("splits", 0) > 0)]
        return ca_df[["date", "dividends", "splits"]]

    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        return self.get_historical_prices(index_symbol, start_date=start_date, end_date=end_date)
