import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MarketRegimeAnalyzer:
    """Analyzes overall market conditions, breadth, and classifies market regime."""

    REGIME_RULES_DOC = """
    Market Regime Classification Rules:
    1. Strong Bullish: NIFTY > 50 DMA & 200 DMA, 20 DMA > 50 DMA, Breadth (% above 50 DMA) >= 70%.
    2. Bullish: NIFTY > 50 DMA, Breadth (% above 50 DMA) >= 50%.
    3. Neutral: Mixed signals, NIFTY near 50 DMA or Breadth between 40% and 50%.
    4. Bearish: NIFTY < 50 DMA, Breadth (% above 50 DMA) < 40%.
    5. Strong Bearish: NIFTY < 50 DMA & 200 DMA, 20 DMA < 50 DMA, Breadth (% above 50 DMA) < 30%.
    Note: Classifications are rule-based observational summaries and do not guarantee future movement.
    """

    @staticmethod
    def analyze_regime(
        nifty_df: pd.DataFrame,
        banknifty_df: pd.DataFrame,
        stock_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Calculates market regime and breadth metrics across stock universe."""
        if nifty_df.empty:
            return {
                "regime": "Neutral",
                "confidence_score": 50.0,
                "nifty_trend": "Unknown",
                "banknifty_trend": "Unknown",
                "breadth": {},
                "documentation": MarketRegimeAnalyzer.REGIME_RULES_DOC
            }

        nifty_latest = nifty_df.iloc[-1]
        nifty_close = nifty_latest.get("close", 0)
        nifty_sma20 = nifty_latest.get("sma_20", nifty_close)
        nifty_sma50 = nifty_latest.get("sma_50", nifty_close)
        nifty_sma200 = nifty_latest.get("sma_200", nifty_close)
        nifty_volatility = nifty_latest.get("volatility_20d", 0)

        # NIFTY Trend
        if nifty_close > nifty_sma50 and nifty_sma20 > nifty_sma50:
            nifty_trend = "Bullish"
        elif nifty_close < nifty_sma50 and nifty_sma20 < nifty_sma50:
            nifty_trend = "Bearish"
        else:
            nifty_trend = "Neutral"

        # BANK NIFTY Trend
        banknifty_trend = "Neutral"
        if not banknifty_df.empty:
            bn_latest = banknifty_df.iloc[-1]
            bn_close = bn_latest.get("close", 0)
            bn_sma50 = bn_latest.get("sma_50", bn_close)
            if bn_close > bn_sma50:
                banknifty_trend = "Bullish"
            elif bn_close < bn_sma50:
                banknifty_trend = "Bearish"

        # Calculate Market Breadth across stock_dfs
        total_stocks = len(stock_dfs)
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        advances = 0
        declines = 0
        new_highs = 0
        new_lows = 0

        for symbol, df in stock_dfs.items():
            if df.empty or len(df) < 2:
                continue
            latest = df.iloc[-1]
            c = latest.get("close", 0)
            ret_1d = latest.get("return_1d", 0)

            if ret_1d > 0:
                advances += 1
            elif ret_1d < 0:
                declines += 1

            if c > latest.get("sma_20", c):
                above_20dma += 1
            if c > latest.get("sma_50", c):
                above_50dma += 1
            if c > latest.get("sma_200", c):
                above_200dma += 1

            # 52w high/low
            dist_high = latest.get("dist_52w_high", -1)
            dist_low = latest.get("dist_52w_low", 1)
            if dist_high >= -0.01:
                new_highs += 1
            if dist_low <= 0.01:
                new_lows += 1

        pct_above_20 = (above_20dma / total_stocks * 100.0) if total_stocks > 0 else 50.0
        pct_above_50 = (above_50dma / total_stocks * 100.0) if total_stocks > 0 else 50.0
        pct_above_200 = (above_200dma / total_stocks * 100.0) if total_stocks > 0 else 50.0
        ad_ratio = (advances / max(declines, 1)) if total_stocks > 0 else 1.0

        # Classify Market Regime
        if nifty_close > nifty_sma50 and nifty_close > nifty_sma200 and nifty_sma20 > nifty_sma50 and pct_above_50 >= 70:
            regime = "Strong Bullish"
            confidence = 85.0
        elif nifty_close > nifty_sma50 and pct_above_50 >= 50:
            regime = "Bullish"
            confidence = 70.0
        elif nifty_close < nifty_sma50 and nifty_close < nifty_sma200 and nifty_sma20 < nifty_sma50 and pct_above_50 < 30:
            regime = "Strong Bearish"
            confidence = 85.0
        elif nifty_close < nifty_sma50 and pct_above_50 < 40:
            regime = "Bearish"
            confidence = 70.0
        else:
            regime = "Neutral"
            confidence = 50.0

        return {
            "date": nifty_latest.get("date"),
            "regime": regime,
            "confidence_score": confidence,
            "nifty_close": nifty_close,
            "nifty_return_1d": nifty_latest.get("return_1d", 0),
            "nifty_trend": nifty_trend,
            "nifty_volatility": nifty_volatility,
            "banknifty_trend": banknifty_trend,
            "breadth": {
                "total_stocks": total_stocks,
                "advances": advances,
                "declines": declines,
                "advance_decline_ratio": round(ad_ratio, 2),
                "pct_above_20dma": round(pct_above_20, 2),
                "pct_above_50dma": round(pct_above_50, 2),
                "pct_above_200dma": round(pct_above_200, 2),
                "new_52w_highs": new_highs,
                "new_52w_lows": new_lows
            },
            "rules_documentation": MarketRegimeAnalyzer.REGIME_RULES_DOC
        }
