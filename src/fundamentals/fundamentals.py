import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Processes and scores optional fundamental financial metrics."""

    @staticmethod
    def analyze_fundamentals(fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a fundamental health score (0-100) based on valuation,
        profitability, solvency, and growth metrics.
        """
        if not fundamental_data or not fundamental_data.get("available", False):
            return {
                "available": False,
                "fundamental_score": 50.0,
                "metrics": {},
                "summary": "Fundamental data unavailable"
            }

        score = 50.0  # Base neutral score
        metrics = {}

        # 1. Valuation
        pe = fundamental_data.get("pe_ratio")
        pb = fundamental_data.get("pb_ratio")
        if pe is not None and isinstance(pe, (int, float)) and pe > 0:
            metrics["pe_ratio"] = round(pe, 2)
            if pe < 15:
                score += 10.0
            elif pe > 40:
                score -= 10.0

        if pb is not None and isinstance(pb, (int, float)) and pb > 0:
            metrics["pb_ratio"] = round(pb, 2)
            if pb < 3:
                score += 5.0
            elif pb > 10:
                score -= 5.0

        # 2. Profitability
        roe = fundamental_data.get("roe")
        margins = fundamental_data.get("profit_margins")
        if roe is not None and isinstance(roe, (int, float)):
            metrics["roe"] = round(roe * 100, 2)
            if roe > 0.15:
                score += 10.0
            elif roe < 0:
                score -= 10.0

        if margins is not None and isinstance(margins, (int, float)):
            metrics["profit_margins"] = round(margins * 100, 2)
            if margins > 0.15:
                score += 5.0
            elif margins < 0:
                score -= 5.0

        # 3. Solvency & Growth
        de = fundamental_data.get("debt_to_equity")
        rev_growth = fundamental_data.get("revenue_growth")
        if de is not None and isinstance(de, (int, float)):
            metrics["debt_to_equity"] = round(de, 2)
            if de < 50:  # yfinance de is often percentage (e.g. 50 = 0.5)
                score += 5.0
            elif de > 150:
                score -= 10.0

        if rev_growth is not None and isinstance(rev_growth, (int, float)):
            metrics["revenue_growth"] = round(rev_growth * 100, 2)
            if rev_growth > 0.10:
                score += 10.0
            elif rev_growth < 0:
                score -= 5.0

        final_score = max(0.0, min(100.0, score))

        return {
            "available": True,
            "fundamental_score": round(final_score, 2),
            "market_cap": fundamental_data.get("market_cap"),
            "dividend_yield": fundamental_data.get("dividend_yield"),
            "metrics": metrics,
            "provider": fundamental_data.get("provider", "yfinance"),
            "retrieval_timestamp": fundamental_data.get("retrieval_timestamp")
        }
