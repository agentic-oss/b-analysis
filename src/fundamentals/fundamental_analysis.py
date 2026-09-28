import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("fundamentals.fundamental_analysis")

class FundamentalAnalyzer:
    """Analyzes company financial metrics, growth, profitability, valuation, and balance sheet quality."""

    @staticmethod
    def evaluate_fundamentals(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes fundamental metrics and computes a fundamental score (0-100).
        Handles optional/missing fundamental metrics gracefully.
        """
        if not data or "error" in data:
            return {
                "fundamental_score": 50.0,
                "label": "Neutral",
                "available": False,
                "metrics": {},
                "source": data.get("provider", "yfinance") if data else "N/A"
            }

        pe = data.get("pe_ratio")
        pb = data.get("pb_ratio")
        roe = data.get("roe")
        roce = data.get("roce")
        de = data.get("debt_to_equity")
        profit_margin = data.get("profit_margins")
        rev_growth = data.get("revenue_growth")

        score = 50.0
        factors = 0

        # Valuation (PE & PB)
        if pe is not None and pe > 0:
            if pe < 15: score += 10
            elif pe < 30: score += 5
            elif pe > 60: score -= 10
            factors += 1

        if pb is not None and pb > 0:
            if pb < 3: score += 5
            elif pb > 10: score -= 5
            factors += 1

        # Profitability (ROE & Profit Margin)
        if roe is not None:
            if roe > 0.20: score += 15
            elif roe > 0.12: score += 8
            elif roe < 0.05: score -= 10
            factors += 1

        if profit_margin is not None:
            if profit_margin > 0.15: score += 10
            elif profit_margin < 0.03: score -= 5
            factors += 1

        # Growth & Solvency (Revenue growth & Debt/Equity)
        if rev_growth is not None:
            if rev_growth > 0.15: score += 10
            elif rev_growth < 0: score -= 10
            factors += 1

        if de is not None:
            if de < 50: score += 10 # yfinance D/E often percentage (e.g., 50%)
            elif de > 150: score -= 10
            factors += 1

        final_score = max(0.0, min(100.0, score))

        label = "Very Strong" if final_score >= 80 else ("Strong" if final_score >= 65 else ("Neutral" if final_score >= 50 else ("Weak" if final_score >= 35 else "Very Weak")))

        return {
            "fundamental_score": round(final_score, 2),
            "label": label,
            "available": True if factors > 0 else False,
            "metrics": {
                "pe_ratio": pe,
                "pb_ratio": pb,
                "roe": roe,
                "profit_margins": profit_margin,
                "revenue_growth": rev_growth,
                "debt_to_equity": de
            },
            "source": data.get("provider", "yfinance")
        }
