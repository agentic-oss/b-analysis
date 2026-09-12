import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class FundamentalAnalyzer:
    """Evaluates fundamental data metrics and returns fundamental scores and insights."""

    @staticmethod
    def evaluate(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates optional fundamental dictionary.
        Returns score (0-100) and metric assessments.
        """
        if not fundamentals:
            return {
                "fundamental_score": 50.0,
                "valuation_status": "Neutral",
                "profitability_status": "Neutral",
                "growth_status": "Neutral",
                "has_data": False,
                "metrics": {}
            }

        scores = []

        # 1. Valuation (P/E, P/B)
        pe = fundamentals.get("pe_ratio")
        val_score = 50.0
        if pe is not None and not np.isnan(pe):
            if pe < 15:
                val_score = 80.0
                val_status = "Undervalued"
            elif pe <= 30:
                val_score = 60.0
                val_status = "Fairly Valued"
            else:
                val_score = 35.0
                val_status = "Overvalued"
        else:
            val_status = "Unknown"
        scores.append(val_score)

        # 2. Profitability (ROE)
        roe = fundamentals.get("roe")
        prof_score = 50.0
        if roe is not None and not np.isnan(roe):
            roe_pct = roe * 100 if roe <= 1.0 else roe
            if roe_pct >= 20:
                prof_score = 85.0
                prof_status = "High Profitability"
            elif roe_pct >= 12:
                prof_score = 65.0
                prof_status = "Moderate Profitability"
            else:
                prof_score = 35.0
                prof_status = "Low Profitability"
        else:
            prof_status = "Unknown"
        scores.append(prof_score)

        # 3. Growth (Revenue/Profit Growth)
        rev_growth = fundamentals.get("revenue_growth")
        profit_growth = fundamentals.get("profit_growth")
        growth_score = 50.0
        g = rev_growth if rev_growth is not None else profit_growth
        if g is not None and not np.isnan(g):
            g_pct = g * 100 if abs(g) <= 1.0 else g
            if g_pct >= 15:
                growth_score = 85.0
                growth_status = "High Growth"
            elif g_pct >= 5:
                growth_score = 65.0
                growth_status = "Moderate Growth"
            else:
                growth_score = 35.0
                growth_status = "Low / Negative Growth"
        else:
            growth_status = "Unknown"
        scores.append(growth_score)

        # 4. Financial Health (Debt to Equity)
        de = fundamentals.get("debt_to_equity")
        health_score = 50.0
        if de is not None and not np.isnan(de):
            if de <= 50:
                health_score = 85.0
            elif de <= 100:
                health_score = 60.0
            else:
                health_score = 30.0
        scores.append(health_score)

        final_score = float(np.mean(scores))

        return {
            "fundamental_score": round(final_score, 2),
            "valuation_status": val_status,
            "profitability_status": prof_status,
            "growth_status": growth_status,
            "has_data": True,
            "metrics": {
                "pe_ratio": pe,
                "pb_ratio": fundamentals.get("pb_ratio"),
                "roe": roe,
                "debt_to_equity": de,
                "revenue_growth": rev_growth,
                "profit_growth": profit_growth,
                "source": fundamentals.get("source", "N/A"),
                "timestamp": fundamentals.get("timestamp", "N/A")
            }
        }
