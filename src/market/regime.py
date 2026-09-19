"""
Market Regime Classification Engine.
Calculates market breadth, DMA distributions, advance/decline ratios,
and classifies environment into Strong Bullish, Bullish, Neutral, Bearish, or Strong Bearish.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class MarketRegimeAnalyzer:
    """Classifies overall Indian market regime using transparent rule-based metrics."""

    def analyze_regime(
        self, index_df: pd.DataFrame, stocks_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze benchmark index (e.g. NIFTY 50) and universe stock data.

        Rules used for classification:
        1. Benchmark Index Trend (NIFTY Close vs 20, 50, 200 SMA)
        2. Market Breadth (% of stocks above 20 DMA, 50 DMA, 200 DMA)
        3. Advance / Decline Ratio (Percentage of stocks with positive daily return)
        4. New Highs vs New Lows (20-day high/low comparison)
        """
        if index_df.empty or len(index_df) < 20:
            return {
                "regime": "Neutral",
                "score": 50.0,
                "confidence": 50.0,
                "breadth": {},
                "summary": "Insufficient benchmark history for market regime analysis."
            }

        latest_index = index_df.iloc[-1]
        index_close = latest_index["close"]

        # 1. Benchmark Trend Score (0 - 100)
        sma_20 = latest_index.get("sma_20", index_close)
        sma_50 = latest_index.get("sma_50", index_close)
        sma_200 = latest_index.get("sma_200", index_close)

        trend_score = 50.0
        if index_close > sma_20: trend_score += 15.0
        if index_close > sma_50: trend_score += 15.0
        if index_close > sma_200: trend_score += 20.0
        if sma_20 > sma_50: trend_score += 10.0
        if sma_50 > sma_200: trend_score += 10.0

        # 2. Market Breadth calculation across stock universe
        above_20_count = 0
        above_50_count = 0
        above_200_count = 0
        advances = 0
        declines = 0
        new_highs = 0
        new_lows = 0
        total_valid = 0

        for ticker, df in stocks_dfs.items():
            if df.empty or len(df) < 5:
                continue
            st_latest = df.iloc[-1]
            st_close = st_latest["close"]
            total_valid += 1

            if st_close > st_latest.get("sma_20", st_close): above_20_count += 1
            if st_close > st_latest.get("sma_50", st_close): above_50_count += 1
            if st_close > st_latest.get("sma_200", st_close): above_200_count += 1

            ret = st_latest.get("daily_return", 0.0)
            if ret > 0: advances += 1
            elif ret < 0: declines += 1

            if st_latest.get("breakout_20d", False): new_highs += 1
            if st_latest.get("breakdown_20d", False): new_lows += 1

        if total_valid > 0:
            pct_above_20 = (above_20_count / total_valid) * 100
            pct_above_50 = (above_50_count / total_valid) * 100
            pct_above_200 = (above_200_count / total_valid) * 100
            ad_ratio = advances / max(declines, 1)
        else:
            pct_above_20 = pct_above_50 = pct_above_200 = 50.0
            ad_ratio = 1.0

        breadth_score = (pct_above_20 * 0.3) + (pct_above_50 * 0.3) + (pct_above_200 * 0.4)

        # Composite Regime Score (50% Index Trend + 50% Universe Breadth)
        composite_score = (trend_score * 0.5) + (breadth_score * 0.5)

        if composite_score >= 75.0:
            regime = "Strong Bullish"
        elif composite_score >= 60.0:
            regime = "Bullish"
        elif composite_score >= 40.0:
            regime = "Neutral"
        elif composite_score >= 25.0:
            regime = "Bearish"
        else:
            regime = "Strong Bearish"

        return {
            "regime": regime,
            "regime_score": round(float(composite_score), 2),
            "benchmark_trend_score": round(float(trend_score), 2),
            "breadth_score": round(float(breadth_score), 2),
            "pct_above_20dma": round(float(pct_above_20), 2),
            "pct_above_50dma": round(float(pct_above_50), 2),
            "pct_above_200dma": round(float(pct_above_200), 2),
            "advances": advances,
            "declines": declines,
            "advance_decline_ratio": round(float(ad_ratio), 2),
            "new_highs_20d": new_highs,
            "new_lows_20d": new_lows,
            "total_tracked_stocks": total_valid
        }
