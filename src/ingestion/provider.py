import abc
import time
import logging
from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider(abc.ABC):
    """Abstract base class for market data ingestion providers."""

    @abc.abstractmethod
    def get_historical_prices(
        self, symbol: str, ticker: str, start_date: str, end_date: str, exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch historical daily OHLCV prices."""
        pass

    @abc.abstractmethod
    def get_corporate_actions(
        self, symbol: str, ticker: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch corporate actions (dividends, splits)."""
        pass

    @abc.abstractmethod
    def get_fundamental_data(self, symbol: str, ticker: str) -> Dict[str, Any]:
        """Fetch basic fundamental data."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance implementation of MarketDataProvider."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _retry_fetch(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                res = func(*args, **kwargs)
                if res is not None and not (isinstance(res, (pd.DataFrame, pd.Series)) and res.empty):
                    return res
                if attempt < self.max_retries:
                    time.sleep(self.backoff_factor * (2 ** (attempt - 1)))
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {args}: {e}")
                last_exception = e
                if attempt < self.max_retries:
                    time.sleep(self.backoff_factor * (2 ** (attempt - 1)))
        if last_exception:
            logger.error(f"Failed after {self.max_retries} attempts: {last_exception}")
        return None

    def get_historical_prices(
        self, symbol: str, ticker: str, start_date: str, end_date: str, exchange: str = "NSE"
    ) -> pd.DataFrame:
        def fetch():
            t = yf.Ticker(ticker)
            df = t.history(start=start_date, end=end_date, auto_adjust=False)
            return df

        df = self._retry_fetch(fetch)
        if df is None or df.empty:
            logger.error(f"No price data retrieved for symbol={symbol}, ticker={ticker}")
            return pd.DataFrame()

        df = df.reset_index()
        # Standardize column names
        rename_map = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
            "Stock Splits": "splits",
            "Dividends": "dividends",
        }
        df = df.rename(columns=rename_map)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        if "adj_close" not in df.columns and "close" in df.columns:
            df["adj_close"] = df["close"]

        # Calculate turnover and VWAP estimates
        if "close" in df.columns and "volume" in df.columns:
            df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0
            df["turnover"] = df["vwap"] * df["volume"]
        else:
            df["vwap"] = None
            df["turnover"] = None

        df["deliverable_qty"] = None
        df["delivery_pct"] = None
        df["symbol"] = symbol
        df["ticker"] = ticker
        df["exchange"] = exchange
        df["provider"] = "yfinance"
        df["ingestion_timestamp"] = pd.Timestamp.now("UTC").isoformat()

        req_cols = [
            "date", "symbol", "ticker", "exchange", "open", "high", "low", "close",
            "adj_close", "volume", "turnover", "vwap", "deliverable_qty", "delivery_pct",
            "provider", "ingestion_timestamp"
        ]
        existing_cols = [c for c in req_cols if c in df.columns]
        return df[existing_cols]

    def get_corporate_actions(
        self, symbol: str, ticker: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        def fetch():
            t = yf.Ticker(ticker)
            actions = t.actions
            return actions

        actions = self._retry_fetch(fetch)
        if actions is None or actions.empty:
            return pd.DataFrame(columns=["date", "symbol", "ticker", "dividends", "splits"])

        df = actions.reset_index().rename(columns={"Date": "date", "Dividends": "dividends", "Stock Splits": "splits"})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df["symbol"] = symbol
        df["ticker"] = ticker
        if start_date and end_date:
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        return df

    def get_fundamental_data(self, symbol: str, ticker: str) -> Dict[str, Any]:
        def fetch():
            t = yf.Ticker(ticker)
            return t.info

        info = self._retry_fetch(fetch)
        if not info or not isinstance(info, dict):
            return {"symbol": symbol, "ticker": ticker, "available": False}

        return {
            "symbol": symbol,
            "ticker": ticker,
            "available": True,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "eps": info.get("trailingEps"),
            "roe": info.get("returnOnEquity"),
            "roce": info.get("returnOnAssets"), # Proxy if ROCE not directly exposed
            "debt_to_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_margins": info.get("profitMargins"),
            "gross_margins": info.get("grossMargins"),
            "ebitda_margins": info.get("ebitdaMargins"),
            "dividend_yield": info.get("dividendYield"),
            "free_cashflow": info.get("freeCashflow"),
            "held_percent_insiders": info.get("heldPercentInsiders"),
            "held_percent_institutions": info.get("heldPercentInstitutions"),
            "retrieval_timestamp": pd.Timestamp.now("UTC").isoformat(),
            "provider": "yfinance"
        }
