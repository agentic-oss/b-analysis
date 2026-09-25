"""Fundamental Analysis Module."""

import datetime
import logging
from typing import Dict, Any, Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Collects and evaluates fundamental metrics for equities."""

    @staticmethod
    def fetch_fundamentals(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Fetch fundamental metric dictionary from provider with timestamps and fallbacks."""
        ticker_str = f"{symbol}.NS" if exchange.upper() == "NSE" and not symbol.startswith("^") else symbol

        try:
            ticker = yf.Ticker(ticker_str)
            info = ticker.info or {}
        except Exception as e:
            logger.warning(f"Could not fetch fundamental info for {symbol}: {e}")
            info = {}

        fetch_time = datetime.datetime.now().isoformat()

        pe = info.get("trailingPE") or info.get("forwardPE")
        pb = info.get("priceToBook")
        roe = info.get("returnOnEquity")
        roce = info.get("returnOnAssets")  # Fallback for ROCE if not present
        debt_to_equity = info.get("debtToEquity")
        rev_growth = info.get("revenueGrowth")
        profit_growth = info.get("earningsGrowth")
        ebitda_margin = info.get("ebitdaMargins")
        net_margin = info.get("profitMargins")
        div_yield = info.get("dividendYield")
        market_cap = info.get("marketCap")
        inst_ownership = info.get("heldPercentInstitutions")

        return {
            "symbol": symbol,
            "provider": "yfinance",
            "retrieved_at": fetch_time,
            "market_cap": float(market_cap) if market_cap else None,
            "pe_ratio": float(pe) if pe else None,
            "pb_ratio": float(pb) if pb else None,
            "roe": float(roe) * 100.0 if roe else None,
            "roce": float(roce) * 100.0 if roce else None,
            "debt_to_equity": float(debt_to_equity) if debt_to_equity else None,
            "revenue_growth_pct": float(rev_growth) * 100.0 if rev_growth else None,
            "profit_growth_pct": float(profit_growth) * 100.0 if profit_growth else None,
            "ebitda_margin_pct": float(ebitda_margin) * 100.0 if ebitda_margin else None,
            "net_margin_pct": float(net_margin) * 100.0 if net_margin else None,
            "dividend_yield_pct": float(div_yield) * 100.0 if div_yield else None,
            "inst_ownership_pct": float(inst_ownership) * 100.0 if inst_ownership else None
        }

    @staticmethod
    def calculate_fundamental_score(data: Dict[str, Any]) -> float:
        """Calculate a transparent fundamental score (0 - 100)."""
        if not data or all(v is None for k, v in data.items() if k not in ["symbol", "provider", "retrieved_at"]):
            return 50.0  # Neutral default if fundamental data is unavailable

        score = 50.0

        # ROE (>15% is strong)
        roe = data.get("roe")
        if roe is not None:
            if roe > 20.0:
                score += 15.0
            elif roe > 12.0:
                score += 8.0
            elif roe < 0:
                score -= 15.0

        # Debt to Equity (<1.0 is healthy, <0.5 is very safe)
        de = data.get("debt_to_equity")
        if de is not None:
            if de < 50.0:  # yfinance returns debt to equity as percentage or ratio
                score += 10.0
            elif de > 150.0:
                score -= 15.0

        # Profit Growth (>10% is solid)
        pg = data.get("profit_growth_pct")
        if pg is not None:
            if pg > 15.0:
                score += 15.0
            elif pg > 5.0:
                score += 5.0
            elif pg < -10.0:
                score -= 15.0

        # Net Margins (>10% is healthy)
        nm = data.get("net_margin_pct")
        if nm is not None:
            if nm > 15.0:
                score += 10.0
            elif nm < 0:
                score -= 10.0

        return max(0.0, min(100.0, score))
