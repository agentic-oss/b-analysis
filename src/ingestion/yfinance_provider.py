"""
Yahoo Finance implementation of MarketDataProvider for Indian stock market.
"""
import time
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import yfinance as yf

from src.ingestion.provider import MarketDataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """
    Market data provider implementation using yfinance with retry & error handling.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 1.5,
        timeout: int = 30
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    def _to_yf_symbol(self, symbol: str, exchange: str = "NSE") -> str:
        """
        Maps symbol to yfinance ticker string.
        """
        if symbol.startswith("^"):
            return symbol
        if exchange.upper() == "NSE" and not symbol.endswith(".NS"):
            return f"{symbol}.NS"
        if exchange.upper() == "BSE" and not symbol.endswith(".BO"):
            return f"{symbol}.BO"
        return symbol

    def _execute_with_retry(self, func, *args, **kwargs):
        delay = self.retry_delay
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= self.backoff_factor
        logger.error(f"Failed after {self.max_retries} retries in {func.__name__}: {last_exception}")
        raise last_exception

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y",
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        yf_symbol = self._to_yf_symbol(symbol, exchange)

        def _fetch():
            ticker = yf.Ticker(yf_symbol)
            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            elif start_date:
                df = ticker.history(start=start_date, auto_adjust=False)
            else:
                df = ticker.history(period=period, auto_adjust=False)

            if df.empty:
                logger.warning(f"No historical data returned for {yf_symbol}")
                return pd.DataFrame()

            # Normalize dataframe columns
            df = df.reset_index()
            # Standardize date column format (YYYY-MM-DD string or datetime date)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

            rename_cols = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
                "Dividends": "dividends",
                "Stock Splits": "splits"
            }
            df = df.rename(columns=rename_cols)

            if "adj_close" not in df.columns and "close" in df.columns:
                df["adj_close"] = df["close"]

            # Calculate VWAP estimate if high, low, close, volume present
            if all(col in df.columns for col in ["high", "low", "close", "volume"]):
                typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
                df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum().replace(0, 1)
            else:
                df["vwap"] = df.get("close", 0)

            df["ticker"] = symbol
            df["exchange"] = exchange.upper()
            df["provider"] = "yfinance"

            return df

        return self._execute_with_retry(_fetch)

    def get_latest_prices(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        df = self.get_historical_prices(symbol=symbol, period="5d", exchange=exchange)
        if df.empty:
            return {}
        latest_row = df.iloc[-1].to_dict()
        return latest_row

    def get_volume_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        df = self.get_historical_prices(symbol=symbol, start_date=start_date, end_date=end_date, exchange=exchange)
        if df.empty:
            return pd.DataFrame()
        cols = [c for c in ["Date", "ticker", "volume", "close", "vwap"] if c in df.columns]
        return df[cols]

    def get_corporate_actions(self, symbol: str, exchange: str = "NSE") -> Dict[str, pd.DataFrame]:
        yf_symbol = self._to_yf_symbol(symbol, exchange)

        def _fetch():
            ticker = yf.Ticker(yf_symbol)
            divs = ticker.dividends
            splits = ticker.splits
            div_df = divs.reset_index() if isinstance(divs, pd.Series) and not divs.empty else pd.DataFrame()
            split_df = splits.reset_index() if isinstance(splits, pd.Series) and not splits.empty else pd.DataFrame()
            return {"dividends": div_df, "splits": split_df}

        try:
            return self._execute_with_retry(_fetch)
        except Exception as e:
            logger.warning(f"Failed to fetch corporate actions for {symbol}: {e}")
            return {"dividends": pd.DataFrame(), "splits": pd.DataFrame()}

    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        return self.get_historical_prices(
            symbol=index_symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            exchange="NSE"
        )
