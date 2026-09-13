import yfinance as yf
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class FundamentalsCollector:
    """
    Collects fundamental metrics for Indian stocks where available.
    """

    @staticmethod
    def get_fundamentals(symbol: str) -> Dict[str, Any]:
        result = {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_cap": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "eps": None,
            "roe": None,
            "debt_to_equity": None,
            "profit_margins": None,
            "revenue_growth": None,
            "dividend_yield": None,
            "promoter_holding": None,
            "institutional_ownership": None,
            "source": "yfinance"
        }

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info:
                result["market_cap"] = info.get("marketCap")
                result["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE")
                result["pb_ratio"] = info.get("priceToBook")
                result["eps"] = info.get("trailingEps")
                result["roe"] = info.get("returnOnEquity")
                result["debt_to_equity"] = info.get("debtToEquity")
                result["profit_margins"] = info.get("profitMargins")
                result["revenue_growth"] = info.get("revenueGrowth")
                result["dividend_yield"] = info.get("dividendYield")
                result["promoter_holding"] = info.get("heldPercentInsiders")
                result["institutional_ownership"] = info.get("heldPercentInstitutions")
        except Exception as e:
            logger.warning(f"Failed to fetch fundamentals for {symbol}: {str(e)}")

        return result
