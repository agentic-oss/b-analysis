"""
Fundamental Analysis Module for Indian Stock Equities.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Parses and computes fundamental health metrics and fundamental scores."""

    def analyze(self, raw_fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fundamental dictionary and calculate fundamental rating/score (0-100)."""
        if not raw_fundamentals or "error" in raw_fundamentals:
            return {
                "fundamental_score": 50.0,
                "label": "Neutral",
                "available": False,
                "metrics": raw_fundamentals or {}
            }

        pe = raw_fundamentals.get("pe_ratio")
        pb = raw_fundamentals.get("pb_ratio")
        roe = raw_fundamentals.get("roe")
        debt_to_equity = raw_fundamentals.get("debt_to_equity")
        profit_growth = raw_fundamentals.get("profit_growth")
        revenue_growth = raw_fundamentals.get("revenue_growth")

        score_components = []

        # Valuation Score
        if pe is not None and pe > 0:
            if pe < 15:
                score_components.append(85)
            elif pe < 30:
                score_components.append(65)
            elif pe < 50:
                score_components.append(45)
            else:
                score_components.append(30)

        # Return on Equity Score
        if roe is not None:
            if roe > 0.20:
                score_components.append(90)
            elif roe > 0.12:
                score_components.append(70)
            elif roe > 0.05:
                score_components.append(50)
            else:
                score_components.append(30)

        # Debt to Equity Score
        if debt_to_equity is not None:
            # debt_to_equity in yfinance is often given as percentage (e.g. 50.0 for 0.5)
            de_ratio = debt_to_equity / 100.0 if debt_to_equity > 5 else debt_to_equity
            if de_ratio < 0.5:
                score_components.append(90)
            elif de_ratio < 1.0:
                score_components.append(70)
            elif de_ratio < 2.0:
                score_components.append(45)
            else:
                score_components.append(25)

        # Earnings & Growth Score
        if profit_growth is not None:
            if profit_growth > 0.15:
                score_components.append(85)
            elif profit_growth > 0.0:
                score_components.append(60)
            else:
                score_components.append(35)

        final_score = float(sum(score_components) / len(score_components)) if score_components else 50.0

        label = "Very Strong" if final_score >= 80 else \
                "Strong" if final_score >= 65 else \
                "Neutral" if final_score >= 50 else \
                "Weak" if final_score >= 35 else "Very Weak"

        return {
            "fundamental_score": round(final_score, 2),
            "label": label,
            "available": True,
            "metrics": raw_fundamentals
        }
