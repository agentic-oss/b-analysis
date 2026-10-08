import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalysis:
    """
    Collects fundamental financial metrics when available (P/E, P/B, EPS, ROE, Market Cap, Debt/Equity, Dividend Yield).
    Attaches source metadata and timestamp.
    """

    @staticmethod
    def get_fundamentals(symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            fundamentals = {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "yfinance",
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "roce": info.get("returnOnAssets"), # Proxy if ROCE unavailable
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margins": info.get("profitMargins"),
                "dividend_yield": info.get("dividendYield"),
                "free_cashflow": info.get("freeCashflow"),
                "promoter_holding": None, # NSE specific field
            }
            return fundamentals
        except Exception as e:
            logger.warning(f"Could not fetch fundamentals for {symbol}: {e}")
            return {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "yfinance",
                "error": str(e)
            }
