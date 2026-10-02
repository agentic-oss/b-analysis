"""
Market Regime Analysis Module.
Analyzes market index trends, volatility, and breadth metrics across tracked stocks
to produce transparent rule-based market classifications.
"""

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketRegimeAnalyzer:
    """Analyzes overall market conditions, breadth, and regime classification."""

    CLASSIFICATIONS = [
        "Strong Bullish",
        "Bullish",
        "Neutral",
        "Bearish",
        "Strong Bearish",
    ]

    def __init__(self, benchmark_symbol: str = "^NSEI"):
        self.benchmark_symbol = benchmark_symbol

    def analyze_regime(
        self,
        index_dfs: Dict[str, pd.DataFrame],
        stock_dfs: Dict[str, pd.DataFrame],
        date_str: str,
    ) -> Dict[str, Any]:
        """
        Analyzes market conditions on date_str using NIFTY, BANK NIFTY, and stock breadth.
        """
        nifty_df = index_dfs.get(self.benchmark_symbol, pd.DataFrame())
        banknifty_df = index_dfs.get("^NSEBANK", pd.DataFrame())

        # Benchmark Trend & Volatility
        nifty_trend = "Unknown"
        nifty_vol = 0.0
        nifty_close = 0.0
        nifty_return_1d = 0.0

        if not nifty_df.empty:
            nifty_sub = nifty_df[nifty_df["date"] <= date_str]
            if not nifty_sub.empty:
                latest = nifty_sub.iloc[-1]
                nifty_close = float(latest["close"])
                nifty_return_1d = float(latest.get("daily_return", 0.0))
                nifty_vol = float(latest.get("volatility_20d", 0.0))

                sma_20 = latest.get("sma_20", nifty_close)
                sma_50 = latest.get("sma_50", nifty_close)
                sma_200 = latest.get("sma_200", nifty_close)

                if nifty_close > sma_20 > sma_50 > sma_200:
                    nifty_trend = "Strong Uptrend"
                elif nifty_close > sma_50:
                    nifty_trend = "Uptrend"
                elif nifty_close < sma_20 < sma_50 < sma_200:
                    nifty_trend = "Strong Downtrend"
                elif nifty_close < sma_50:
                    nifty_trend = "Downtrend"
                else:
                    nifty_trend = "Neutral"

        # Bank Nifty Trend
        banknifty_trend = "Unknown"
        if not banknifty_df.empty:
            bn_sub = banknifty_df[banknifty_df["date"] <= date_str]
            if not bn_sub.empty:
                latest_bn = bn_sub.iloc[-1]
                bn_close = float(latest_bn["close"])
                bn_sma_50 = latest_bn.get("sma_50", bn_close)
                banknifty_trend = "Uptrend" if bn_close > bn_sma_50 else "Downtrend"

        # Market Breadth Calculation across tracked stocks
        advances = 0
        declines = 0
        unchanged = 0
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        new_highs = 0
        new_lows = 0
        total_stocks = 0

        for symbol, s_df in stock_dfs.items():
            s_sub = s_df[s_df["date"] <= date_str]
            if s_sub.empty:
                continue
            total_stocks += 1
            latest_s = s_sub.iloc[-1]
            ret = latest_s.get("daily_return", 0.0)
            if ret > 0.0005:
                advances += 1
            elif ret < -0.0005:
                declines += 1
            else:
                unchanged += 1

            c = latest_s["close"]
            if c > latest_s.get("sma_20", c):
                above_20dma += 1
            if c > latest_s.get("sma_50", c):
                above_50dma += 1
            if c > latest_s.get("sma_200", c):
                above_200dma += 1

            if latest_s.get("breakout", False):
                new_highs += 1
            if latest_s.get("breakdown", False):
                new_lows += 1

        ad_ratio = float(advances / max(declines, 1))
        pct_above_20dma = float((above_20dma / max(total_stocks, 1)) * 100)
        pct_above_50dma = float((above_50dma / max(total_stocks, 1)) * 100)
        pct_above_200dma = float((above_200dma / max(total_stocks, 1)) * 100)

        # Classification Framework Rules:
        # Score components: 0-10 points total
        # Points based on Nifty trend, Bank Nifty, % above 50 DMA, A/D ratio
        regime_score = 0
        if nifty_trend in ["Strong Uptrend", "Uptrend"]:
            regime_score += 3
        if banknifty_trend == "Uptrend":
            regime_score += 2
        if pct_above_50dma > 60:
            regime_score += 3
        elif pct_above_50dma > 40:
            regime_score += 1.5
        if ad_ratio > 1.2:
            regime_score += 2
        elif ad_ratio > 0.8:
            regime_score += 1

        if regime_score >= 8.5:
            regime_label = "Strong Bullish"
        elif regime_score >= 6.0:
            regime_label = "Bullish"
        elif regime_score >= 4.0:
            regime_label = "Neutral"
        elif regime_score >= 2.0:
            regime_label = "Bearish"
        else:
            regime_label = "Strong Bearish"

        result = {
            "date": date_str,
            "regime": regime_label,
            "regime_score": round(regime_score, 2),
            "nifty_close": nifty_close,
            "nifty_return_1d": nifty_return_1d,
            "nifty_trend": nifty_trend,
            "nifty_volatility": nifty_vol,
            "banknifty_trend": banknifty_trend,
            "breadth": {
                "total_stocks": total_stocks,
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "advance_decline_ratio": round(ad_ratio, 2),
                "above_20_dma_pct": round(pct_above_20dma, 1),
                "above_50_dma_pct": round(pct_above_50dma, 1),
                "above_200_dma_pct": round(pct_above_200dma, 1),
                "new_highs_count": new_highs,
                "new_lows_count": new_lows,
            },
            "classification_rules": (
                "Score calculated from NIFTY trend (0-3), Bank NIFTY trend (0-2), "
                "breadth > 50 DMA (0-3), and Advance/Decline ratio (0-2). "
                "Labels: Strong Bullish (>=8.5), Bullish (>=6.0), Neutral (>=4.0), Bearish (>=2.0), Strong Bearish (<2.0)."
            ),
        }

        return result
