import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

class MarketRegimeAnalyzer:
    """Analyzes market-wide health, index trends, breadth, and classifies regime."""

    @staticmethod
    def analyze_regime(nifty_df: pd.DataFrame, bank_nifty_df: pd.DataFrame, stock_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        if nifty_df.empty or len(nifty_df) < 20:
            return {
                "regime": "Neutral",
                "confidence": 50,
                "nifty_trend": "Unknown",
                "bank_nifty_trend": "Unknown",
                "breadth": {},
                "rules_applied": "Insufficient historical index data"
            }

        nifty_latest = nifty_df.iloc[-1]
        nifty_close = nifty_latest["close"]
        nifty_sma20 = nifty_latest.get("sma_20", nifty_close)
        nifty_sma50 = nifty_latest.get("sma_50", nifty_close)
        nifty_sma200 = nifty_latest.get("sma_200", nifty_close)

        # NIFTY trend classification
        if nifty_close > nifty_sma20 > nifty_sma50:
            nifty_trend = "Bullish"
        elif nifty_close < nifty_sma20 < nifty_sma50:
            nifty_trend = "Bearish"
        else:
            nifty_trend = "Neutral"

        # Bank NIFTY trend classification
        bank_trend = "Neutral"
        if not bank_nifty_df.empty and len(bank_nifty_df) >= 20:
            bn_latest = bank_nifty_df.iloc[-1]
            bn_close = bn_latest["close"]
            bn_sma20 = bn_latest.get("sma_20", bn_close)
            if bn_close > bn_sma20:
                bank_trend = "Bullish"
            elif bn_close < bn_sma20:
                bank_trend = "Bearish"

        # Market breadth calculations across stock universe
        total_stocks = len(stock_dfs)
        advances = 0
        declines = 0
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        new_highs = 0
        new_lows = 0

        for ticker, df in stock_dfs.items():
            if df.empty or len(df) < 2:
                continue
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            ret = latest.get("return_1d", 0)
            if ret > 0:
                advances += 1
            elif ret < 0:
                declines += 1

            c = latest["close"]
            if c > latest.get("sma_20", c):
                above_20dma += 1
            if c > latest.get("sma_50", c):
                above_50dma += 1
            if c > latest.get("sma_200", c):
                above_200dma += 1

            if latest.get("dist_52w_high", -1) >= -0.01:
                new_highs += 1
            if latest.get("dist_52w_low", 1) <= 0.01:
                new_lows += 1

        ad_ratio = advances / max(declines, 1)
        pct_above_20dma = (above_20dma / max(total_stocks, 1)) * 100
        pct_above_50dma = (above_50dma / max(total_stocks, 1)) * 100
        pct_above_200dma = (above_200dma / max(total_stocks, 1)) * 100

        # Regime score evaluation (0-100)
        score = 50
        if nifty_close > nifty_sma20: score += 10
        if nifty_close > nifty_sma50: score += 10
        if nifty_close > nifty_sma200: score += 10
        if ad_ratio > 1.2: score += 10
        elif ad_ratio < 0.8: score -= 10
        if pct_above_20dma > 60: score += 10
        elif pct_above_20dma < 40: score -= 10

        score = max(0, min(100, score))

        if score >= 80:
            regime = "Strong Bullish"
        elif score >= 60:
            regime = "Bullish"
        elif score >= 40:
            regime = "Neutral"
        elif score >= 20:
            regime = "Bearish"
        else:
            regime = "Strong Bearish"

        rules_doc = "Regime rules: Evaluates NIFTY close vs 20/50/200 DMAs, Advance/Decline ratio, and % stocks above DMAs."

        return {
            "regime": regime,
            "score": score,
            "nifty_trend": nifty_trend,
            "bank_nifty_trend": bank_trend,
            "breadth": {
                "total_stocks": total_stocks,
                "advances": advances,
                "declines": declines,
                "ad_ratio": round(ad_ratio, 2),
                "pct_above_20dma": round(pct_above_20dma, 1),
                "pct_above_50dma": round(pct_above_50dma, 1),
                "pct_above_200dma": round(pct_above_200dma, 1),
                "new_highs": new_highs,
                "new_lows": new_lows
            },
            "rules_applied": rules_doc
        }
