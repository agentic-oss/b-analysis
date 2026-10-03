import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    """Abstract interface for stock market data providers."""

    @abstractmethod
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, period: str = "3y") -> pd.DataFrame:
        """Fetch historical price data (OHLCV)."""
        pass

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        """Fetch dividends and stock splits."""
        pass

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch key fundamental metrics."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Implementation of MarketDataProvider using yfinance with retry & rate limiting."""

    def __init__(self, retries: int = 3, delay_sec: float = 1.0, timeout: int = 15):
        self.retries = retries
        self.delay_sec = delay_sec
        self.timeout = timeout

    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, period: str = "3y") -> pd.DataFrame:
        for attempt in range(1, self.retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                if start_date and end_date:
                    df = ticker.history(start=start_date, end=end_date, auto_adjust=False, timeout=self.timeout)
                elif start_date:
                    df = ticker.history(start=start_date, auto_adjust=False, timeout=self.timeout)
                else:
                    df = ticker.history(period=period, auto_adjust=False, timeout=self.timeout)

                if df.empty:
                    logger.warning(f"No historical data returned for {symbol} (attempt {attempt}/{self.retries})")
                    if attempt < self.retries:
                        time.sleep(self.delay_sec * attempt)
                        continue
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
                    "Dividends": "dividends",
                    "Stock Splits": "splits"
                }
                df = df.rename(columns=rename_map)

                if "adj_close" not in df.columns:
                    df["adj_close"] = df["close"]

                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")

                cols = [c for c in ["date", "open", "high", "low", "close", "adj_close", "volume", "dividends", "splits"] if c in df.columns]
                return df[cols]

            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol} (attempt {attempt}/{self.retries}): {e}")
                if attempt < self.retries:
                    time.sleep(self.delay_sec * attempt)

        return pd.DataFrame()

    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        for attempt in range(1, self.retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                actions = ticker.actions
                if actions is None or actions.empty:
                    return pd.DataFrame(columns=["date", "dividends", "splits"])
                actions = actions.reset_index()
                actions = actions.rename(columns={"Date": "date", "Dividends": "dividends", "Stock Splits": "splits"})
                actions["date"] = pd.to_datetime(actions["date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                return actions[["date", "dividends", "splits"]]
            except Exception as e:
                logger.error(f"Error fetching corporate actions for {symbol}: {e}")
                if attempt < self.retries:
                    time.sleep(self.delay_sec * attempt)
        return pd.DataFrame(columns=["date", "dividends", "splits"])

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        for attempt in range(1, self.retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info or {}
                return {
                    "market_cap": info.get("marketCap"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "pb_ratio": info.get("priceToBook"),
                    "eps": info.get("trailingEps"),
                    "roe": info.get("returnOnEquity"),
                    "roce": info.get("returnOnAssets"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "profit_margins": info.get("profitMargins"),
                    "ebitda_margins": info.get("ebitdaMargins"),
                    "dividend_yield": info.get("dividendYield"),
                    "free_cash_flow": info.get("freeCashflow"),
                    "promoter_holding": info.get("heldPercentInsiders"),
                    "institutional_holding": info.get("heldPercentInstitutions"),
                    "data_provider": "yfinance"
                }
            except Exception as e:
                logger.error(f"Error fetching fundamentals for {symbol}: {e}")
                if attempt < self.retries:
                    time.sleep(self.delay_sec * attempt)
        return {}
