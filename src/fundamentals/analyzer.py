from typing import Dict, Any, Optional

class FundamentalAnalyzer:
    """Analyzes optional fundamental company metrics and scores fundamental health (0-100)."""

    @staticmethod
    def analyze_fundamentals(fundamental_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates growth, profitability, valuation, and balance sheet strength.
        Returns metrics and a 0-100 fundamental score.
        """
        if not fundamental_data:
            return {
                "score": 50, # Neutral default if data not available
                "available": False,
                "valuation_status": "Unknown",
                "profitability_status": "Unknown",
                "growth_status": "Unknown"
            }

        pe = fundamental_data.get("pe_ratio")
        pb = fundamental_data.get("price_to_book")
        roe = fundamental_data.get("roe")
        rev_growth = fundamental_data.get("revenue_growth")
        profit_growth = fundamental_data.get("profit_growth")
        de = fundamental_data.get("debt_to_equity")

        score_components = []

        # 1. Valuation (P/E)
        if pe is not None and pe > 0:
            if pe < 15:
                score_components.append(85)
            elif pe < 25:
                score_components.append(70)
            elif pe < 40:
                score_components.append(50)
            else:
                score_components.append(30)
            valuation_status = "Cheap" if pe < 15 else ("Moderate" if pe < 30 else "Expensive")
        else:
            valuation_status = "Unknown"

        # 2. Profitability (ROE)
        if roe is not None:
            if roe > 0.20:
                score_components.append(90)
            elif roe > 0.12:
                score_components.append(70)
            elif roe > 0:
                score_components.append(50)
            else:
                score_components.append(20)
            profitability_status = "Strong" if roe > 0.15 else "Weak"
        else:
            profitability_status = "Unknown"

        # 3. Growth (Revenue or Profit)
        if rev_growth is not None:
            if rev_growth > 0.15:
                score_components.append(85)
            elif rev_growth > 0.05:
                score_components.append(65)
            elif rev_growth > 0:
                score_components.append(50)
            else:
                score_components.append(25)
            growth_status = "High Growth" if rev_growth > 0.15 else "Moderate Growth"
        else:
            growth_status = "Unknown"

        # 4. Financial Health (Debt to Equity)
        if de is not None:
            if de < 50: # Assuming % or ratio < 0.5
                score_components.append(85)
            elif de < 100:
                score_components.append(65)
            else:
                score_components.append(35)

        final_score = int(sum(score_components) / len(score_components)) if score_components else 50

        return {
            "score": max(0, min(100, final_score)),
            "available": True,
            "valuation_status": valuation_status,
            "profitability_status": profitability_status,
            "growth_status": growth_status,
            "raw_data": fundamental_data
        }
