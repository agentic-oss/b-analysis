from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """
    Analyzes optional fundamental data (Market Cap, P/E, P/B, EPS, ROE, Debt/Equity, Growth, Margins).
    Provides structured qualitative assessment.
    """

    def analyze_fundamentals(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data or "error" in data:
            return {
                "available": False,
                "summary": "Fundamental data unavailable",
                "metrics": {}
            }

        pe = data.get('pe_ratio')
        pb = data.get('pb_ratio')
        roe = data.get('roe')
        d_e = data.get('debt_to_equity')
        rev_growth = data.get('revenue_growth')
        profit_growth = data.get('profit_growth')

        # Qualitative assessment
        valuation = "Fair"
        if pe:
            if pe < 15: valuation = "Undervalued / Value"
            elif pe > 40: valuation = "High Valuation"

        profitability = "Moderate"
        if roe:
            if roe > 0.20: profitability = "High Profitability"
            elif roe < 0.05: profitability = "Low Profitability"

        solvency = "Healthy"
        if d_e:
            if d_e > 1.5: solvency = "High Leverage"
            elif d_e < 0.5: solvency = "Low Debt"

        return {
            "available": True,
            "valuation_assessment": valuation,
            "profitability_assessment": profitability,
            "solvency_assessment": solvency,
            "metrics": {
                "market_cap": data.get('market_cap'),
                "pe_ratio": pe,
                "pb_ratio": pb,
                "eps": data.get('eps'),
                "roe": roe,
                "debt_to_equity": d_e,
                "revenue_growth": rev_growth,
                "profit_growth": profit_growth,
                "promoter_holding": data.get('promoter_holding'),
                "institutional_ownership": data.get('institutional_ownership')
            },
            "source": data.get('provider', 'unknown'),
            "timestamp": data.get('timestamp')
        }
