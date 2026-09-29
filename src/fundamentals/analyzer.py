"""
Fundamental Data Parsing and Analysis module.
Optional/graceful handling for valuation, growth, and profitability metrics.
"""
import time
import logging
from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Parses valuation, financial performance, and ownership data for stocks with source & timestamp logging.
    """

    @staticmethod
    def get_fundamentals(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Fetches fundamentals using yfinance ticker.info with graceful fallback if unavailable.
        """
        yf_symbol = symbol if symbol.startswith("^") else (f"{symbol}.NS" if exchange.upper() == "NSE" else f"{symbol}.BO")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info or {}

            pe = info.get("trailingPE", info.get("forwardPE", None))
            pb = info.get("priceToBook", None)
            mcap = info.get("marketCap", None)
            eps = info.get("trailingEps", None)
            roe = info.get("returnOnEquity", None)
            if roe is not None:
                roe = roe * 100  # express as percentage
            debt_to_equity = info.get("debtToEquity", None)
            rev_growth = info.get("revenueGrowth", None)
            if rev_growth is not None:
                rev_growth = rev_growth * 100
            profit_growth = info.get("earningsGrowth", None)
            if profit_growth is not None:
                profit_growth = profit_growth * 100
            div_yield = info.get("dividendYield", None)
            if div_yield is not None:
                div_yield = div_yield * 100

            ebitda_margin = info.get("ebitdaMargins", None)
            if ebitda_margin is not None:
                ebitda_margin = ebitda_margin * 100
            net_margin = info.get("profitMargins", None)
            if net_margin is not None:
                net_margin = net_margin * 100

            # Compute transparent fundamental score (0-100) if metrics exist
            score_components = []

            # PE valuation score
            if pe is not None and pe > 0:
                if pe < 15:
                    score_components.append(85)
                elif pe < 30:
                    score_components.append(65)
                elif pe < 50:
                    score_components.append(50)
                else:
                    score_components.append(35)

            # ROE profitability score
            if roe is not None:
                if roe > 20:
                    score_components.append(90)
                elif roe > 12:
                    score_components.append(70)
                elif roe > 0:
                    score_components.append(50)
                else:
                    score_components.append(25)

            # Debt-to-Equity safety score
            if debt_to_equity is not None:
                if debt_to_equity < 50:
                    score_components.append(85)
                elif debt_to_equity < 100:
                    score_components.append(60)
                else:
                    score_components.append(35)

            # Revenue Growth score
            if rev_growth is not None:
                if rev_growth > 15:
                    score_components.append(85)
                elif rev_growth > 5:
                    score_components.append(65)
                elif rev_growth > 0:
                    score_components.append(50)
                else:
                    score_components.append(30)

            fundamental_score = float(sum(score_components) / len(score_components)) if score_components else 50.0

            return {
                "symbol": symbol,
                "data_source": "yfinance",
                "retrieved_timestamp": timestamp,
                "available": True if len(score_components) > 0 else False,
                "market_cap": mcap,
                "pe_ratio": pe,
                "pb_ratio": pb,
                "eps": eps,
                "roe_pct": roe,
                "debt_to_equity": debt_to_equity,
                "revenue_growth_pct": rev_growth,
                "profit_growth_pct": profit_growth,
                "dividend_yield_pct": div_yield,
                "ebitda_margin_pct": ebitda_margin,
                "net_margin_pct": net_margin,
                "fundamental_score": round(fundamental_score, 2)
            }

        except Exception as e:
            logger.warning(f"Could not fetch fundamental data for {symbol}: {e}")
            return {
                "symbol": symbol,
                "data_source": "yfinance",
                "retrieved_timestamp": timestamp,
                "available": False,
                "fundamental_score": 50.0
            }
