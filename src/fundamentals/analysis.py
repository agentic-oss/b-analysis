"""
Fundamental Analysis module for evaluating fundamental metrics, growth,
profitability, valuation, and balance sheet quality.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def analyze_fundamentals(symbol: str, raw_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses and evaluates fundamental indicators for a stock.
    Returns fundamental metrics and calculated fundamental score (0-100).
    """
    if not raw_info:
        return {
            "symbol": symbol,
            "available": False,
            "fundamental_score": None,
            "metrics": {},
            "source": "None",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    m_cap = raw_info.get("marketCap")
    pe = raw_info.get("trailingPE") or raw_info.get("forwardPE")
    pb = raw_info.get("priceToBook")
    roe = raw_info.get("returnOnEquity")
    debt_to_equity = raw_info.get("debtToEquity")
    revenue_growth = raw_info.get("revenueGrowth")
    profit_growth = raw_info.get("earningsGrowth")
    div_yield = raw_info.get("dividendYield")

    # Score sub-components (0-100 scale)
    val_score = 50.0
    if pe is not None:
        if 0 < pe < 15:
            val_score += 25.0
        elif 15 <= pe <= 30:
            val_score += 10.0
        elif pe > 50:
            val_score -= 20.0

    profit_score = 50.0
    if roe is not None:
        if roe >= 0.20:
            profit_score += 30.0
        elif roe >= 0.12:
            profit_score += 15.0
        elif roe < 0.05:
            profit_score -= 20.0

    growth_score = 50.0
    if revenue_growth is not None:
        if revenue_growth >= 0.15:
            growth_score += 25.0
        elif revenue_growth < 0:
            growth_score -= 20.0

    health_score = 50.0
    if debt_to_equity is not None:
        if debt_to_equity <= 50.0:
            health_score += 25.0
        elif debt_to_equity > 150.0:
            health_score -= 25.0

    fundamental_score = round(
        (val_score * 0.25) + (profit_score * 0.35) + (growth_score * 0.25) + (health_score * 0.15), 1
    )
    fundamental_score = max(0.0, min(100.0, fundamental_score))

    metrics = {
        "market_cap": m_cap,
        "pe_ratio": round(pe, 2) if pe else None,
        "pb_ratio": round(pb, 2) if pb else None,
        "roe_pct": round(roe * 100, 2) if roe else None,
        "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else None,
        "revenue_growth_pct": round(revenue_growth * 100, 2) if revenue_growth else None,
        "profit_growth_pct": round(profit_growth * 100, 2) if profit_growth else None,
        "dividend_yield_pct": round(div_yield * 100, 2) if div_yield else None
    }

    return {
        "symbol": symbol,
        "available": True,
        "fundamental_score": fundamental_score,
        "metrics": metrics,
        "source": raw_info.get("provider", "yfinance"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
