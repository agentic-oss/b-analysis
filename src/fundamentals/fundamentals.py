"""Fundamental Analysis Module (Optional fundamental metrics ingestion and evaluation)."""

from typing import Dict, Any, Optional
import datetime

class FundamentalAnalyzer:
    """Collects and processes fundamental metrics when available."""

    def analyze_fundamentals(self, symbol: str, fundamental_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parses available fundamental data, computes quality scores, and records source and timestamp.

        If fundamental_data is None or empty, returns default neutral fundamental metrics.
        """
        now_iso = datetime.datetime.now().isoformat()

        if not fundamental_data:
            return {
                "symbol": symbol,
                "data_available": False,
                "timestamp": now_iso,
                "score": 50.0, # Neutral score when data is unavailable
                "metrics": {
                    "market_cap": None,
                    "pe_ratio": None,
                    "pb_ratio": None,
                    "eps": None,
                    "roe": None,
                    "roce": None,
                    "debt_to_equity": None,
                    "revenue_growth_yoy": None,
                    "profit_growth_yoy": None,
                    "net_margin": None,
                    "dividend_yield": None,
                    "promoter_holding": None,
                    "institutional_ownership": None
                },
                "assessment": "No reliable fundamental data available; defaulted to neutral score."
            }

        m = fundamental_data.get("metrics", {})

        # Calculate transparent Fundamental Score (0-100)
        score_components = []

        # P/E Ratio check (e.g. 10 to 30 is reasonable)
        pe = m.get("pe_ratio")
        if pe is not None and pe > 0:
            if pe < 15: score_components.append(85)
            elif pe < 30: score_components.append(70)
            elif pe < 50: score_components.append(50)
            else: score_components.append(30)

        # ROE check
        roe = m.get("roe")
        if roe is not None:
            if roe > 0.20: score_components.append(90)
            elif roe > 0.12: score_components.append(70)
            elif roe > 0.05: score_components.append(50)
            else: score_components.append(30)

        # Debt to Equity check
        de = m.get("debt_to_equity")
        if de is not None:
            if de < 0.5: score_components.append(90)
            elif de < 1.0: score_components.append(70)
            elif de < 2.0: score_components.append(40)
            else: score_components.append(20)

        # Revenue Growth
        rev_g = m.get("revenue_growth_yoy")
        if rev_g is not None:
            if rev_g > 0.15: score_components.append(85)
            elif rev_g > 0.05: score_components.append(65)
            elif rev_g > 0: score_components.append(50)
            else: score_components.append(30)

        fund_score = round(sum(score_components) / len(score_components), 2) if score_components else 50.0

        return {
            "symbol": symbol,
            "data_available": True,
            "source": fundamental_data.get("source", "financial_statement_ingest"),
            "timestamp": now_iso,
            "score": fund_score,
            "metrics": m,
            "assessment": f"Evaluated based on {len(score_components)} fundamental factors."
        }
