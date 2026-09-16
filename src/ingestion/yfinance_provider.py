import time
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf
from src.ingestion.base import MarketDataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """
    yfinance implementation of MarketDataProvider for Indian stock market data.
    Includes retry logic, rate limit handling, logging, and metadata tagging.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _fetch_with_retry(self, ticker_obj: yf.Ticker, method_name: str, **kwargs) -> Any:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                method = getattr(ticker_obj, method_name)
                if callable(method):
                    data = method(**kwargs)
                else:
                    data = method
                if data is not None and (not isinstance(data, (pd.DataFrame, pd.Series)) or not data.empty):
                    return data
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {ticker_obj.ticker} method '{method_name}': {e}"
                )
                time.sleep(self.retry_delay * attempt)
        if last_exception:
            logger.error(f"Failed to fetch data for {ticker_obj.ticker} after {self.max_retries} retries.")
        return None

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = "2y",
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                if start_date and end_date:
                    df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
                else:
                    df = ticker.history(period=period, auto_adjust=False)

                if df is not None and not df.empty:
                    df = df.reset_index()
                    # Ensure Date column is standard YYYY-MM-DD string or datetime
                    if "Date" in df.columns:
                        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")

                    # Normalize column names
                    col_map = {
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Adj Close": "adj_close",
                        "Volume": "volume",
                        "Stock Splits": "splits",
                        "Dividends": "dividends",
                    }
                    df = df.rename(columns=col_map)

                    if "adj_close" not in df.columns and "close" in df.columns:
                        df["adj_close"] = df["close"]

                    # Compute VWAP approximation if absent: (High + Low + Close) / 3
                    if "vwap" not in df.columns and {"high", "low", "close"}.issubset(df.columns):
                        df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0

                    # Tag metadata
                    df["symbol"] = symbol
                    df["provider"] = "yfinance"
                    df["ingested_at"] = pd.Timestamp.now().isoformat()

                    return df
            except Exception as e:
                last_err = e
                logger.warning(f"Download attempt {attempt} failed for {symbol}: {e}")
                time.sleep(self.retry_delay * attempt)

        logger.error(f"Failed to download historical prices for {symbol}: {last_err}")
        return pd.DataFrame()

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        records = []
        for sym in symbols:
            df = self.get_historical_prices(sym, period="5d")
            if not df.empty:
                records.append(df.iloc[-1:])
        if records:
            return pd.concat(records, ignore_index=True)
        return pd.DataFrame()

    def get_volume_data(self, symbol: str, period: str = "1m") -> pd.DataFrame:
        df = self.get_historical_prices(symbol, period=period)
        if not df.empty and "volume" in df.columns:
            return df[["Date", "symbol", "close", "volume", "vwap"]]
        return pd.DataFrame()

    def get_corporate_actions(self, symbol: str) -> Dict[str, pd.DataFrame]:
        ticker = yf.Ticker(symbol)
        actions = {}
        try:
            divs = ticker.dividends
            if divs is not None and not divs.empty:
                div_df = divs.reset_index()
                div_df.columns = ["date", "dividend"]
                div_df["date"] = pd.to_datetime(div_df["date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                actions["dividends"] = div_df
            splits = ticker.splits
            if splits is not None and not splits.empty:
                split_df = splits.reset_index()
                split_df.columns = ["date", "split_ratio"]
                split_df["date"] = pd.to_datetime(split_df["date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                actions["splits"] = split_df
        except Exception as e:
            logger.warning(f"Error fetching corporate actions for {symbol}: {e}")
        return actions

    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        return self.get_historical_prices(index_symbol, start_date=start_date, end_date=end_date, period="2y")
