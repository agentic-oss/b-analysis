"""
Fundamental metrics loader and fundamental score evaluator.
"""
import datetime
import logging
from typing import Dict, Any, Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Retrieves and scores fundamental metrics where available."""

    @staticmethod
    def fetch_and_evaluate(symbol: str) -> Dict[str, Any]:
        """
        Fetches fundamental indicators via Yahoo Finance info dict.
        Returns metrics dictionary and normalized fundamental score (0-100).
        """
        data = {
            "symbol": symbol,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "market_cap": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "roe": None,
            "roce": None,
            "debt_to_equity": None,
            "profit_margins": None,
            "dividend_yield": None,
            "score": 50.0,  # Neutral default
            "data_available": False,
        }

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or not isinstance(info, dict):
                return data

            data["market_cap"] = info.get("marketCap")
            data["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE")
            data["pb_ratio"] = info.get("priceToBook")
            data["roe"] = info.get("returnOnEquity")
            data["debt_to_equity"] = info.get("debtToEquity")
            data["profit_margins"] = info.get("profitMargins")
            data["dividend_yield"] = info.get("dividendYield")
            data["data_available"] = True

            # Calculate fundamental score based on valuation & profitability
            score_components = []

            # P/E Score
            pe = data["pe_ratio"]
            if pe is not None and pe > 0:
                if pe < 15:
                    score_components.append(90)
                elif pe < 30:
                    score_components.append(70)
                elif pe < 50:
                    score_components.append(50)
                else:
                    score_components.append(30)

            # ROE Score
            roe = data["roe"]
            if roe is not None:
                if roe > 0.20:
                    score_components.append(90)
                elif roe > 0.12:
                    score_components.append(70)
                elif roe > 0.05:
                    score_components.append(50)
                else:
                    score_components.append(20)

            # Profit Margin Score
            pm = data["profit_margins"]
            if pm is not None:
                if pm > 0.20:
                    score_components.append(90)
                elif pm > 0.10:
                    score_components.append(70)
                elif pm > 0.0:
                    score_components.append(50)
                else:
                    score_components.append(20)

            if score_components:
                data["score"] = round(sum(score_components) / len(score_components), 2)

        except Exception as e:
            logger.warning(f"Could not fetch fundamentals for {symbol}: {e}")

        return data
