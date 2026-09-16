from typing import Dict, Any, Optional
import logging
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Collects and analyzes optional fundamental data for stocks.
    Handles missing values gracefully and records data timestamps/sources.
    """

    def fetch_fundamentals(self, symbol: str) -> Dict[str, Any]:
        result = {
            "symbol": symbol,
            "source": "yfinance",
            "timestamp": pd.Timestamp.now().isoformat(),
            "available": False,
            "market_cap": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "eps": None,
            "roe": None,
            "roce": None,
            "debt_to_equity": None,
            "revenue_growth": None,
            "profit_growth": None,
            "ebitda_margin": None,
            "net_margin": None,
            "dividend_yield": None,
            "free_cash_flow": None,
            "promoter_holding": None,
            "institutional_ownership": None,
        }

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info and isinstance(info, dict):
                result["available"] = True
                result["market_cap"] = info.get("marketCap")
                result["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE")
                result["pb_ratio"] = info.get("priceToBook")
                result["eps"] = info.get("trailingEps")
                result["roe"] = info.get("returnOnEquity")
                result["debt_to_equity"] = info.get("debtToEquity")
                result["revenue_growth"] = info.get("revenueGrowth")
                result["profit_growth"] = info.get("earningsGrowth")
                result["ebitda_margin"] = info.get("ebitdaMargins")
                result["net_margin"] = info.get("profitMargins")
                result["dividend_yield"] = info.get("dividendYield")
                result["free_cash_flow"] = info.get("freeCashflow")
                result["institutional_ownership"] = info.get("heldPercentInstitutions")
        except Exception as e:
            logger.warning(f"Could not fetch fundamental data for {symbol}: {e}")

        return result

    def calculate_fundamental_score(self, fundamentals: Dict[str, Any]) -> float:
        """
        Calculates normalized fundamental score (0-100) based on valuation, profitability, and growth metrics.
        Returns baseline neutral 50 if fundamental data is unavailable.
        """
        if not fundamentals.get("available", False):
            return 50.0

        score = 50.0

        # ROE score component
        roe = fundamentals.get("roe")
        if roe is not None:
            if roe > 0.20:
                score += 15
            elif roe > 0.12:
                score += 10
            elif roe < 0.0:
                score -= 15

        # P/E valuation component
        pe = fundamentals.get("pe_ratio")
        if pe is not None and pe > 0:
            if pe < 20:
                score += 15
            elif pe < 35:
                score += 5
            elif pe > 60:
                score -= 10

        # Debt to equity component
        de = fundamentals.get("debt_to_equity")
        if de is not None:
            if de < 50:  # yfinance de is often percentage (50%) or ratio (0.5)
                score += 10
            elif de > 150:
                score -= 10

        # Profit growth component
        pg = fundamentals.get("profit_growth")
        if pg is not None:
            if pg > 0.15:
                score += 10
            elif pg < 0:
                score -= 10

        return float(min(100.0, max(0.0, score)))
