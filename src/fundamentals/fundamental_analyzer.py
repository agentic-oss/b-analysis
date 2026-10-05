"""
Fundamental Analysis Collector and Scoring Engine (Optional/Extensible).
"""

from typing import Dict, Any, Optional, Tuple
import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Collects and scores fundamental metrics for stocks when available."""

    @staticmethod
    def get_fundamentals(ticker: str) -> Dict[str, Any]:
        """Fetches key fundamental ratios from Yahoo Finance."""
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info or {}

            return {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
                "dividend_yield": info.get("dividendYield"),
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margins": info.get("profitMargins"),
                "promoter_holding": info.get("heldPercentInsiders"),
                "institutional_holding": info.get("heldPercentInstitutions"),
                "source": "yfinance",
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.warning(f"Could not fetch fundamentals for {ticker}: {e}")
            return {"source": "unavailable", "error": str(e)}

    @staticmethod
    def calculate_fundamental_score(data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Computes transparent fundamental composite score (0 to 100).
        Returns (score, breakdown_dict).
        """
        if not data or data.get("source") == "unavailable":
            return 50.0, {"note": "Fundamental data unavailable; neutral default applied."}

        score = 50.0
        breakdown = {}

        # ROE scoring
        roe = data.get("roe")
        if roe is not None:
            if roe > 0.20:
                score += 15
                breakdown["roe"] = "High ROE > 20% (+15)"
            elif roe > 0.12:
                score += 10
                breakdown["roe"] = "Moderate ROE > 12% (+10)"
            elif roe < 0:
                score -= 15
                breakdown["roe"] = "Negative ROE (-15)"

        # P/E valuation check
        pe = data.get("pe_ratio")
        if pe is not None:
            if 0 < pe < 25:
                score += 10
                breakdown["pe"] = "Reasonable P/E < 25 (+10)"
            elif pe > 60:
                score -= 10
                breakdown["pe"] = "High P/E > 60 (-10)"

        # Profit Margins
        margins = data.get("profit_margins")
        if margins is not None:
            if margins > 0.15:
                score += 10
                breakdown["margins"] = "Healthy margins > 15% (+10)"
            elif margins < 0:
                score -= 10
                breakdown["margins"] = "Negative margins (-10)"

        # Revenue Growth
        growth = data.get("revenue_growth")
        if growth is not None:
            if growth > 0.10:
                score += 15
                breakdown["growth"] = "Strong revenue growth > 10% (+15)"
            elif growth < 0:
                score -= 10
                breakdown["growth"] = "Negative revenue growth (-10)"

        score = max(0.0, min(100.0, score))
        return round(score, 1), breakdown
