"""
Fundamental Analysis Module.
Optional module to fetch and analyze company fundamental metrics (PE, PB, ROE, Debt/Equity, etc.).
Includes source tracking and retrieval timestamping.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Collects and evaluates stock fundamental metrics."""

    def __init__(self, provider_name: str = "yfinance"):
        self.provider_name = provider_name

    def get_fundamentals(self, symbol: str, exchange: str = "NSE", ticker_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches fundamental metrics for a stock.
        Returns a dict of metrics or empty fallback if unavailable.
        """
        ticker_str = ticker_override or f"{symbol}.NS"
        try:
            t = yf.Ticker(ticker_str)
            info = t.info or {}
        except Exception as e:
            logger.warning(f"Could not fetch fundamental info for {symbol}: {e}")
            info = {}

        timestamp = datetime.now(timezone.utc).isoformat()

        metrics = {
            "symbol": symbol,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "eps": info.get("trailingEps"),
            "roe": info.get("returnOnEquity"),
            "roce": info.get("returnOnAssets"),  # Proxy when ROCE not explicitly in yfinance
            "debt_to_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_growth": info.get("earningsGrowth"),
            "ebitda_margins": info.get("ebitdaMargins"),
            "net_margins": info.get("profitMargins"),
            "dividend_yield": info.get("dividendYield"),
            "free_cashflow": info.get("freeCashflow"),
            "promoter_holding": None,  # Not provided directly by yfinance
            "institutional_holding": info.get("heldPercentInstitutions"),
            "source": self.provider_name,
            "timestamp": timestamp,
        }

        # Calculate a transparent Fundamental Score (0 - 100)
        score = self._calculate_fundamental_score(metrics)
        metrics["fundamental_score"] = score

        return metrics

    def _calculate_fundamental_score(self, m: Dict[str, Any]) -> float:
        """Transparent scoring rule based on valuation, profitability, and debt."""
        score = 50.0  # Neutral baseline

        # ROE bonus
        roe = m.get("roe")
        if roe is not None:
            if roe > 0.20:
                score += 15
            elif roe > 0.12:
                score += 10
            elif roe < 0:
                score -= 15

        # P/E sanity check
        pe = m.get("pe_ratio")
        if pe is not None:
            if 0 < pe <= 25:
                score += 10
            elif pe > 60:
                score -= 10

        # Debt to Equity
        dte = m.get("debt_to_equity")
        if dte is not None:
            if dte < 50:  # < 0.5 in ratio terms
                score += 10
            elif dte > 150:
                score -= 10

        # Profit growth
        pg = m.get("profit_growth")
        if pg is not None:
            if pg > 0.15:
                score += 15
            elif pg < 0:
                score -= 10

        return max(0.0, min(100.0, float(score)))
