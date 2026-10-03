import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """Analyzes company financial health and valuation metrics if available."""

    @staticmethod
    def evaluate(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        if not fundamentals:
            return {
                "score": 50,
                "valuation_status": "Unknown",
                "profitability_status": "Unknown",
                "data_available": False
            }

        score = 50
        pe = fundamentals.get("pe_ratio")
        pb = fundamentals.get("pb_ratio")
        roe = fundamentals.get("roe")
        profit_margin = fundamentals.get("profit_margins")
        debt_to_equity = fundamentals.get("debt_to_equity")

        if pe is not None:
            if 0 < pe < 25: score += 10
            elif pe > 50: score -= 10

        if roe is not None:
            if roe > 0.15: score += 15
            elif roe < 0.05: score -= 10

        if profit_margin is not None:
            if profit_margin > 0.10: score += 10

        if debt_to_equity is not None:
            if debt_to_equity < 1.0: score += 15
            elif debt_to_equity > 2.0: score -= 15

        score = max(0, min(100, score))

        return {
            "score": score,
            "valuation_status": "Fair" if 0 < (pe or 0) < 30 else "High",
            "profitability_status": "Strong" if (roe or 0) > 0.12 else "Moderate",
            "data_available": True,
            "metrics": fundamentals
        }
