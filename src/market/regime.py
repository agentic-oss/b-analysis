"""
Rule-based market regime detector for Indian equities and benchmark indices.
"""
from typing import Dict, Any, List
import pandas as pd


class MarketRegimeDetector:
    """
    Analyzes market benchmark (e.g. NIFTY 50) and universe breadth to determine market regime:
    - Strong Bullish
    - Bullish
    - Neutral
    - Bearish
    - Strong Bearish
    """

    @staticmethod
    def analyze_regime(
        nifty_df: pd.DataFrame, stock_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        if nifty_df.empty or len(nifty_df) < 50:
            return {
                "regime": "Neutral",
                "score": 50.0,
                "confidence": 50.0,
                "nifty_trend": "Unknown",
                "breadth_above_20dma_pct": 50.0,
                "breadth_above_50dma_pct": 50.0,
                "breadth_above_200dma_pct": 50.0,
                "advance_decline_ratio": 1.0,
                "rules_applied": ["Insufficient historical benchmark data"],
            }

        latest_nifty = nifty_df.iloc[-1]
        close = latest_nifty["Close"]
        sma20 = latest_nifty.get("sma_20", close)
        sma50 = latest_nifty.get("sma_50", close)
        sma200 = latest_nifty.get("sma_200", close)
        vola20 = latest_nifty.get("volatility_20d", 0.15)

        # Calculate NIFTY trend
        if close > sma20 > sma50 > sma200:
            nifty_trend = "Strong Uptrend"
            nifty_score = 90
        elif close > sma50 and close > sma200:
            nifty_trend = "Uptrend"
            nifty_score = 70
        elif close < sma20 < sma50 < sma200:
            nifty_trend = "Strong Downtrend"
            nifty_score = 10
        elif close < sma50 and close < sma200:
            nifty_trend = "Downtrend"
            nifty_score = 30
        else:
            nifty_trend = "Sideways / Neutral"
            nifty_score = 50

        # Calculate market breadth across tracked stock universe
        tot_stocks = 0
        above_20 = 0
        above_50 = 0
        above_200 = 0
        advances = 0
        declines = 0

        for sym, df in stock_dfs.items():
            if df.empty or len(df) < 2:
                continue
            tot_stocks += 1
            row = df.iloc[-1]
            prev_row = df.iloc[-2]

            c = row["Close"]
            if c > row.get("sma_20", c):
                above_20 += 1
            if c > row.get("sma_50", c):
                above_50 += 1
            if c > row.get("sma_200", c):
                above_200 += 1

            if c > prev_row["Close"]:
                advances += 1
            elif c < prev_row["Close"]:
                declines += 1

        pct_20 = (above_20 / tot_stocks * 100) if tot_stocks > 0 else 50.0
        pct_50 = (above_50 / tot_stocks * 100) if tot_stocks > 0 else 50.0
        pct_200 = (above_200 / tot_stocks * 100) if tot_stocks > 0 else 50.0
        ad_ratio = (advances / max(declines, 1)) if tot_stocks > 0 else 1.0

        # Composite score calculation
        breadth_score = (pct_20 * 0.4) + (pct_50 * 0.4) + (pct_200 * 0.2)
        composite_score = (nifty_score * 0.5) + (breadth_score * 0.5)

        if composite_score >= 80:
            regime = "Strong Bullish"
        elif composite_score >= 62.5:
            regime = "Bullish"
        elif composite_score >= 37.5:
            regime = "Neutral"
        elif composite_score >= 20:
            regime = "Bearish"
        else:
            regime = "Strong Bearish"

        rules = [
            f"NIFTY Trend: {nifty_trend} (Price: {close:.2f}, 50DMA: {sma50:.2f}, 200DMA: {sma200:.2f})",
            f"Market Breadth: {pct_50:.1f}% stocks above 50DMA",
            f"Advance/Decline Ratio: {ad_ratio:.2f}",
            f"20-Day Annualized Benchmark Volatility: {vola20 * 100:.1f}%",
        ]

        return {
            "regime": regime,
            "score": round(composite_score, 2),
            "confidence": 85.0 if tot_stocks > 10 else 60.0,
            "nifty_trend": nifty_trend,
            "breadth_above_20dma_pct": round(pct_20, 2),
            "breadth_above_50dma_pct": round(pct_50, 2),
            "breadth_above_200dma_pct": round(pct_200, 2),
            "advance_decline_ratio": round(ad_ratio, 2),
            "rules_applied": rules,
        }
