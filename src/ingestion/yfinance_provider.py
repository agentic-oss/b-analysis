import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import pandas as pd
import yfinance as yf

from src.ingestion.base import MarketDataProvider

logger = logging.getLogger(__name__)

class YFinanceDataProvider(MarketDataProvider):
    """yfinance implementation of MarketDataProvider for Indian stock market data."""

    def __init__(self, retries: int = 3, backoff_factor: float = 1.5, timeout: int = 15):
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    def _fetch_with_retry(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.retries + 1):
            try:
                res = func(*args, **kwargs)
                if res is not None and not (isinstance(res, pd.DataFrame) and res.empty):
                    return res
                if attempt < self.retries:
                    time.sleep(self.backoff_factor ** attempt)
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed with error: {e}")
                last_exception = e
                if attempt < self.retries:
                    time.sleep(self.backoff_factor ** attempt)
        if last_exception:
            logger.error(f"Failed after {self.retries} attempts: {last_exception}")
        return pd.DataFrame()

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        def _fetch():
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            # Standardize date column
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")

            rename_map = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume"
            }
            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]
            df = df.rename(columns=rename_map)
            df["symbol"] = symbol
            df["provider"] = "yfinance"
            df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
            cols = ["Date", "open", "high", "low", "close", "adj_close", "volume", "symbol", "provider", "ingestion_timestamp"]
            existing_cols = [c for c in cols if c in df.columns]
            return df[existing_cols]

        return self._fetch_with_retry(_fetch)

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        dfs = []
        for sym in symbols:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="5d", auto_adjust=False)
            if not df.empty:
                df = df.reset_index()
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                rename_map = {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}
                if "Adj Close" not in df.columns and "Close" in df.columns:
                    df["Adj Close"] = df["Close"]
                df = df.rename(columns=rename_map)
                df["symbol"] = sym
                df["provider"] = "yfinance"
                df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
                dfs.append(df.iloc[[-1]])
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame()

    def get_volume_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date)
        if df.empty:
            return pd.DataFrame()
        # Add placeholder turnover and delivery columns if unavailable from yfinance
        df["turnover"] = df["close"] * df["volume"]
        df["deliverable_quantity"] = None
        df["delivery_percentage"] = None
        return df[["Date", "symbol", "volume", "turnover", "deliverable_quantity", "delivery_percentage"]]

    def get_corporate_actions(self, symbol: str) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        try:
            actions = ticker.actions
            if actions is not None and not actions.empty:
                actions = actions.reset_index()
                actions["Date"] = pd.to_datetime(actions["Date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                actions["symbol"] = symbol
                return actions
        except Exception as e:
            logger.warning(f"Could not fetch corporate actions for {symbol}: {e}")
        return pd.DataFrame(columns=["Date", "Dividends", "Stock Splits", "symbol"])

    def get_index_data(self, index_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_historical_prices(index_symbol, start_date, end_date)

    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        ticker = yf.Ticker(symbol)
        data = {
            "symbol": symbol,
            "provider": "yfinance",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_cap": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "eps": None,
            "roe": None,
            "roce": None,
            "debt_to_equity": None,
            "revenue_growth": None,
            "profit_growth": None,
            "ebitda_margin": None,
            "net_margin": None,
            "dividend_yield": None,
            "free_cash_flow": None,
            "promoter_holding": None,
            "institutional_ownership": None
        }
        try:
            info = ticker.info
            if info:
                data["market_cap"] = info.get("marketCap")
                data["pe_ratio"] = info.get("trailingPE")
                data["pb_ratio"] = info.get("priceToBook")
                data["eps"] = info.get("trailingEps")
                data["roe"] = info.get("returnOnEquity")
                data["debt_to_equity"] = info.get("debtToEquity")
                data["revenue_growth"] = info.get("revenueGrowth")
                data["ebitda_margin"] = info.get("ebitdaMargins")
                data["net_margin"] = info.get("profitMargins")
                data["dividend_yield"] = info.get("dividendYield")
                data["free_cash_flow"] = info.get("freeCashflow")
                data["institutional_ownership"] = info.get("heldPercentInstitutions")
        except Exception as e:
            logger.warning(f"Error fetching fundamentals for {symbol}: {e}")
        return data
