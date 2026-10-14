import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """Processes optional fundamental metrics into a normalized fundamental score (0-100)."""

    def analyze(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates valuation, growth, profitability, and balance sheet quality.
        Returns detailed sub-scores and an overall fundamental score (0-100).
        """
        result = {
            "score": 50,
            "valuation_score": 50,
            "growth_score": 50,
            "profitability_score": 50,
            "balance_sheet_score": 50,
            "metrics": fundamental_data
        }

        if not fundamental_data:
            return result

        pe = fundamental_data.get("pe_ratio")
        pb = fundamental_data.get("pb_ratio")
        rev_growth = fundamental_data.get("revenue_growth")
        net_margin = fundamental_data.get("net_margin")
        de = fundamental_data.get("debt_to_equity")

        # 1. Valuation
        val_score = 50
        if pe is not None:
            if 0 < pe < 15:
                val_score += 25
            elif 15 <= pe <= 30:
                val_score += 10
            elif pe > 40:
                val_score -= 15
        result["valuation_score"] = max(0, min(100, val_score))

        # 2. Growth
        growth_score = 50
        if rev_growth is not None:
            if rev_growth > 0.20:
                growth_score += 30
            elif rev_growth > 0.10:
                growth_score += 15
            elif rev_growth < 0:
                growth_score -= 20
        result["growth_score"] = max(0, min(100, growth_score))

        # 3. Profitability
        prof_score = 50
        if net_margin is not None:
            if net_margin > 0.15:
                prof_score += 30
            elif net_margin > 0.08:
                prof_score += 15
            elif net_margin < 0:
                prof_score -= 25
        result["profitability_score"] = max(0, min(100, prof_score))

        # 4. Balance Sheet
        bs_score = 50
        if de is not None:
            if de < 50: # Debt/Equity %
                bs_score += 25
            elif de > 150:
                bs_score -= 25
        result["balance_sheet_score"] = max(0, min(100, bs_score))

        # Composite Fundamental Score
        comp = (result["valuation_score"] + result["growth_score"] + result["profitability_score"] + result["balance_sheet_score"]) / 4.0
        result["score"] = round(comp, 2)
        return result
