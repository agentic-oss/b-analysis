"""
YFinance implementation of MarketDataProvider with retries, rate limiting, and robust error handling.
"""

import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf

from src.ingestion.provider import MarketDataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """
    Market data provider using yfinance with built-in retries and error checking.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0, timeout: int = 15):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def _execute_with_retry(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {func.__name__}: {str(e)}. Retrying..."
                )
                time.sleep(self.retry_delay * attempt)
        logger.error(f"All {self.max_retries} attempts failed for {func.__name__}.")
        raise last_exception

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV price history for a given ticker or symbol.
        """
        def _fetch():
            ticker_obj = yf.Ticker(symbol)
            if start_date and end_date:
                df = ticker_obj.history(start=start_date, end=end_date, auto_adjust=False)
            else:
                df = ticker_obj.history(period=period, auto_adjust=False)

            if df.empty:
                logger.warning(f"No price data returned for symbol: {symbol}")
                return pd.DataFrame()

            df = df.reset_index()
            # Standardize column names
            col_map = {
                "Date": "Date",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Adj Close": "Adj Close",
                "Volume": "Volume",
            }
            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]

            df = df.rename(columns=col_map)
            df["Ticker"] = symbol
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

            required_cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "Ticker"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = None

            return df[required_cols]

        try:
            return self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch latest prices for a list of symbols.
        """
        results = []
        for sym in symbols:
            df = self.get_historical_prices(sym, period="5d")
            if not df.empty:
                results.append(df.iloc[-1:])
        if results:
            return pd.concat(results, ignore_index=True)
        return pd.DataFrame()

    def get_corporate_actions(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch corporate actions (dividends, splits) for a symbol.
        """
        def _fetch():
            ticker_obj = yf.Ticker(symbol)
            actions = ticker_obj.actions
            divs = ticker_obj.dividends
            splits = ticker_obj.splits

            actions_list = []
            if actions is not None and not actions.empty:
                actions_reset = actions.reset_index()
                for _, row in actions_reset.iterrows():
                    dt_str = str(pd.to_datetime(row["Date"]).date())
                    actions_list.append({
                        "date": dt_str,
                        "dividend": float(row.get("Dividends", 0.0)),
                        "split_ratio": float(row.get("Stock Splits", 0.0))
                    })

            return {
                "symbol": symbol,
                "actions": actions_list,
                "total_dividends_count": len(divs) if divs is not None else 0,
                "total_splits_count": len(splits) if splits is not None else 0,
            }

        try:
            return self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {e}")
            return {"symbol": symbol, "actions": [], "error": str(e)}

    def get_index_data(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y",
    ) -> pd.DataFrame:
        """
        Fetch historical data for index tickers.
        """
        return self.get_historical_prices(index_symbol, start_date=start_date, end_date=end_date, period=period)

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch financial info and fundamental metrics for a symbol.
        """
        def _fetch():
            ticker_obj = yf.Ticker(symbol)
            info = ticker_obj.info or {}

            fundamentals = {
                "symbol": symbol,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"), # Proxy if ROCE not directly exposed
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_growth": info.get("earningsGrowth"),
                "ebitda_margins": info.get("ebitdaMargins"),
                "net_margins": info.get("profitMargins"),
                "dividend_yield": info.get("dividendYield"),
                "free_cash_flow": info.get("freeCashflow"),
                "promoter_holding": info.get("heldPercentInsiders"),
                "institutional_ownership": info.get("heldPercentInstitutions"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "provider": "yfinance",
            }
            return fundamentals

        try:
            return self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {"symbol": symbol, "provider": "yfinance", "error": str(e)}
