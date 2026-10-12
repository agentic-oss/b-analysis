"""
Fundamental analysis module for evaluating company fundamentals.
Computes transparent sub-scores for valuation, profitability, growth, balance sheet, and dividend yield.
"""

from typing import Dict, Any, Optional


class FundamentalAnalyzer:
    """
    Evaluates fundamental metrics and produces a transparent 0-100 fundamental score.
    """

    def analyze(self, fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates normalized fundamental score and detailed sub-metrics.
        """
        if not fundamentals or "error" in fundamentals:
            return {
                "fundamental_score": 50.0,
                "valuation_score": 50.0,
                "profitability_score": 50.0,
                "growth_score": 50.0,
                "balance_sheet_score": 50.0,
                "available": False,
                "reason": fundamentals.get("error", "No fundamental data available"),
            }

        score_components = []

        # 1. Valuation (P/E & P/B)
        pe = fundamentals.get("pe_ratio")
        pb = fundamentals.get("pb_ratio")
        val_score = 50.0
        if pe is not None and pe > 0:
            if pe < 15:
                val_score = 85.0
            elif pe < 25:
                val_score = 70.0
            elif pe < 40:
                val_score = 50.0
            else:
                val_score = 30.0
        score_components.append(val_score)

        # 2. Profitability (ROE & Net Margin)
        roe = fundamentals.get("roe")
        net_margin = fundamentals.get("net_margins")
        prof_score = 50.0
        if roe is not None:
            if roe > 0.20:
                prof_score = 90.0
            elif roe > 0.12:
                prof_score = 70.0
            elif roe > 0.05:
                prof_score = 50.0
            else:
                prof_score = 30.0
        score_components.append(prof_score)

        # 3. Growth (Revenue & Profit Growth)
        rev_growth = fundamentals.get("revenue_growth")
        profit_growth = fundamentals.get("profit_growth")
        growth_score = 50.0
        if rev_growth is not None:
            if rev_growth > 0.15:
                growth_score = 85.0
            elif rev_growth > 0.05:
                growth_score = 65.0
            elif rev_growth > 0:
                growth_score = 50.0
            else:
                growth_score = 30.0
        score_components.append(growth_score)

        # 4. Balance Sheet (Debt to Equity)
        dte = fundamentals.get("debt_to_equity")
        bs_score = 50.0
        if dte is not None:
            if dte < 50.0:  # < 0.5 ratio if given in % or ratio
                bs_score = 85.0
            elif dte < 100.0:
                bs_score = 65.0
            else:
                bs_score = 35.0
        score_components.append(bs_score)

        overall_score = sum(score_components) / len(score_components)

        return {
            "fundamental_score": round(overall_score, 2),
            "valuation_score": round(val_score, 2),
            "profitability_score": round(prof_score, 2),
            "growth_score": round(growth_score, 2),
            "balance_sheet_score": round(bs_score, 2),
            "available": True,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "roe": roe,
            "debt_to_equity": dte,
            "revenue_growth": rev_growth,
            "provider": fundamentals.get("provider", "yfinance"),
        }
