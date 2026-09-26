"""
Data ingestion module with abstract MarketDataProvider interface,
yfinance implementation, and mock data provider.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, date, timedelta
import logging
import time
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract Base Class for Indian stock market data providers."""

    @abstractmethod
    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch historical price data (OHLCV, VWAP, etc.) for a ticker."""
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        """Fetch latest price snapshots for given symbols."""
        pass

    @abstractmethod
    def get_volume_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch volume and delivery data where available."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> Dict[str, Any]:
        """Fetch splits, bonuses, and dividend actions."""
        pass

    @abstractmethod
    def get_index_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch historical data for market or sector indices."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Data provider using Yahoo Finance (yfinance) for Indian stock data."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, timeout: int = 30):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        import yfinance as yf
        self.yf = yf

    def _resolve_yahoo_symbol(self, symbol: str) -> str:
        """Map symbol to Yahoo Finance ticker string."""
        if symbol.startswith("^"):
            return symbol
        if "." in symbol:
            return symbol
        return f"{symbol}.NS"

    def _format_dataframe(self, df: pd.DataFrame, ticker_symbol: str) -> pd.DataFrame:
        """Standardize raw yfinance output DataFrame schema."""
        if df.empty:
            return pd.DataFrame(columns=[
                "Date", "Open", "High", "Low", "Close", "Adj Close",
                "Volume", "VWAP", "Turnover", "Deliverable_Qty", "Delivery_Pct",
                "ticker", "exchange", "data_provider", "ingestion_timestamp"
            ])

        # Reset index if Date is in index
        df = df.reset_index()

        # Handle multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if col[1] == "" else col[0] for col in df.columns]

        # Rename columns to standard names
        col_map = {
            "Date": "Date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Adj Close": "Adj Close",
            "Volume": "Volume"
        }
        df = df.rename(columns=col_map)

        # Ensure Date column is date type / formatted YYYY-MM-DD string
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        # Guarantee Adj Close exists
        if "Adj Close" not in df.columns and "Close" in df.columns:
            df["Adj Close"] = df["Close"]

        # Calculate VWAP estimate: (High + Low + Close) / 3 * Volume / Volume
        if all(col in df.columns for col in ["High", "Low", "Close", "Volume"]):
            tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
            df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum().replace(0, np.nan)
            df["VWAP"] = df["VWAP"].fillna(df["Close"])
            df["Turnover"] = (tp * df["Volume"]).round(2)
        else:
            df["VWAP"] = df.get("Close", np.nan)
            df["Turnover"] = np.nan

        # Delivery metrics are not directly provided by yfinance; mark NaN or estimate
        df["Deliverable_Qty"] = np.nan
        df["Delivery_Pct"] = np.nan

        # Metadata
        df["ticker"] = ticker_symbol
        df["exchange"] = "NSE" if not ticker_symbol.startswith("^") else "INDEX"
        df["data_provider"] = "yfinance"
        df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

        # Sort by Date ascending and drop duplicates
        df = df.sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)
        return df

    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        yf_symbol = self._resolve_yahoo_symbol(symbol)
        logger.info(f"Fetching historical prices for {symbol} ({yf_symbol}) from {start_date} to {end_date}")

        for attempt in range(1, self.max_retries + 1):
            try:
                ticker = self.yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
                if not df.empty:
                    return self._format_dataframe(df, symbol)
                logger.warning(f"Attempt {attempt}: Empty data returned for {yf_symbol}")
            except Exception as e:
                logger.error(f"Attempt {attempt} failed for {yf_symbol}: {e}")
            time.sleep(self.retry_delay * attempt)

        logger.error(f"Failed to fetch historical prices for {symbol} after {self.max_retries} attempts.")
        return self._format_dataframe(pd.DataFrame(), symbol)

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        results = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        start_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        for sym in symbols:
            df = self.get_historical_prices(sym, start_str, today_str)
            if not df.empty:
                latest_row = df.iloc[[-1]].copy()
                results.append(latest_row)

        if results:
            return pd.concat(results, ignore_index=True)
        return pd.DataFrame()

    def get_volume_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date)
        cols = ["Date", "Volume", "Turnover", "Deliverable_Qty", "Delivery_Pct", "ticker"]
        return df[[c for c in cols if c in df.columns]]

    def get_corporate_actions(self, symbol: str) -> Dict[str, Any]:
        yf_symbol = self._resolve_yahoo_symbol(symbol)
        try:
            ticker = self.yf.Ticker(yf_symbol)
            dividends = ticker.dividends
            splits = ticker.splits
            div_dict = dividends.to_dict() if dividends is not None and not dividends.empty else {}
            split_dict = splits.to_dict() if splits is not None and not splits.empty else {}
            return {
                "symbol": symbol,
                "dividends": {str(k.date()): float(v) for k, v in div_dict.items()},
                "splits": {str(k.date()): float(v) for k, v in split_dict.items()},
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to fetch corporate actions for {symbol}: {e}")
            return {"symbol": symbol, "dividends": {}, "splits": {}, "error": str(e)}

    def get_index_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        return self.get_historical_prices(symbol, start_date, end_date)


class MockDataProvider(MarketDataProvider):
    """Deterministic synthetic data provider for offline testing and fast execution."""

    def __init__(self, seed: int = 42):
        self.seed = seed

    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        np.random.seed(abs(hash(symbol) + self.seed) % (2**32 - 1))
        dates = pd.date_range(start=start_date, end=end_date, freq="B")
        if len(dates) == 0:
            dates = pd.date_range(end=end_date, periods=100, freq="B")

        n = len(dates)
        base_price = 1000.0 if symbol != "^NSEI" else 22000.0
        returns = np.random.normal(0.0005, 0.015, n)
        price = base_price * np.exp(np.cumsum(returns))

        high = price * (1 + np.abs(np.random.normal(0, 0.008, n)))
        low = price * (1 - np.abs(np.random.normal(0, 0.008, n)))
        open_price = low + (high - low) * np.random.uniform(0.1, 0.9, n)
        close = low + (high - low) * np.random.uniform(0.1, 0.9, n)
        adj_close = close
        volume = np.random.randint(100000, 5000000, n)
        tp = (high + low + close) / 3.0
        turnover = tp * volume
        deliv_qty = (volume * np.random.uniform(0.3, 0.7, n)).astype(int)
        deliv_pct = (deliv_qty / volume * 100).round(2)

        df = pd.DataFrame({
            "Date": dates.strftime("%Y-%m-%d"),
            "Open": open_price.round(2),
            "High": high.round(2),
            "Low": low.round(2),
            "Close": close.round(2),
            "Adj Close": adj_close.round(2),
            "Volume": volume,
            "VWAP": tp.round(2),
            "Turnover": turnover.round(2),
            "Deliverable_Qty": deliv_qty,
            "Delivery_Pct": deliv_pct,
            "ticker": symbol,
            "exchange": "NSE" if not symbol.startswith("^") else "INDEX",
            "data_provider": "mock",
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat()
        })
        return df

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        results = []
        for sym in symbols:
            df = self.get_historical_prices(sym, start_date, end_date)
            if not df.empty:
                results.append(df.iloc[[-1]])
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

    def get_volume_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date)
        return df[["Date", "Volume", "Turnover", "Deliverable_Qty", "Delivery_Pct", "ticker"]]

    def get_corporate_actions(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "dividends": {"2025-02-15": 10.5},
            "splits": {},
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }

    def get_index_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        return self.get_historical_prices(symbol, start_date, end_date)
