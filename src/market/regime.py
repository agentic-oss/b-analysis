"""
Market Regime Classification and Market Breadth Analysis.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class MarketRegimeAnalyzer:
    """Analyzes market-wide regime, trend, volatility, and market breadth."""

    @staticmethod
    def analyze_market_regime(
        nifty_df: pd.DataFrame,
        bank_nifty_df: pd.DataFrame,
        stock_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Determines market regime classification based on benchmark trends, volatility,
        and stock universe breadth (% above 20, 50, 200 DMA, advance/decline ratio).
        """
        if nifty_df.empty or len(nifty_df) < 50:
            return {"regime": "Neutral", "confidence": 50, "rules_triggered": ["Insufficient data for benchmark"]}

        latest_nifty = nifty_df.iloc[-1]
        close_nifty = latest_nifty["close"]

        # 1. Benchmark Moving Average Trends
        sma20 = latest_nifty.get("sma_20", close_nifty)
        sma50 = latest_nifty.get("sma_50", close_nifty)
        sma200 = latest_nifty.get("sma_200", close_nifty)

        above_20d = close_nifty > sma20
        above_50d = close_nifty > sma50
        above_200d = close_nifty > sma200

        # Bank Nifty Trend
        bn_trend = "Neutral"
        if not bank_nifty_df.empty:
            bn_latest = bank_nifty_df.iloc[-1]
            bn_close = bn_latest["close"]
            bn_sma50 = bn_latest.get("sma_50", bn_close)
            bn_trend = "Bullish" if bn_close > bn_sma50 else "Bearish"

        # 2. Market Breadth across universe
        total_stocks = 0
        above_20_count = 0
        above_50_count = 0
        above_200_count = 0
        advances = 0
        declines = 0
        new_highs = 0
        new_lows = 0

        for ticker, df in stock_dfs.items():
            if df.empty or len(df) < 20:
                continue
            total_stocks += 1
            st_latest = df.iloc[-1]
            st_close = st_latest["close"]

            # Advances / Declines
            if len(df) >= 2:
                prev_close = df.iloc[-2]["close"]
                if st_close > prev_close:
                    advances += 1
                elif st_close < prev_close:
                    declines += 1

            if st_close > st_latest.get("sma_20", st_close):
                above_20_count += 1
            if st_close > st_latest.get("sma_50", st_close):
                above_50_count += 1
            if st_close > st_latest.get("sma_200", st_close):
                above_200_count += 1

            # Highs / Lows (20-day)
            high_20 = df["high"].iloc[-21:-1].max() if len(df) >= 21 else None
            low_20 = df["low"].iloc[-21:-1].min() if len(df) >= 21 else None
            if high_20 and st_close > high_20:
                new_highs += 1
            if low_20 and st_close < low_20:
                new_lows += 1

        pct_above_20 = (above_20_count / total_stocks * 100) if total_stocks > 0 else 50
        pct_above_50 = (above_50_count / total_stocks * 100) if total_stocks > 0 else 50
        pct_above_200 = (above_200_count / total_stocks * 100) if total_stocks > 0 else 50
        ad_ratio = (advances / declines) if declines > 0 else advances

        # 3. Transparent Rule-Based Regime Score (-100 to +100)
        score = 0
        rules = []

        if above_200d:
            score += 30
            rules.append("NIFTY above 200 DMA (+30)")
        else:
            score -= 30
            rules.append("NIFTY below 200 DMA (-30)")

        if above_50d:
            score += 20
            rules.append("NIFTY above 50 DMA (+20)")
        else:
            score -= 20
            rules.append("NIFTY below 50 DMA (-20)")

        if pct_above_50 > 60:
            score += 25
            rules.append(f"Market Breadth (>60% above 50 DMA: {pct_above_50:.1f}%) (+25)")
        elif pct_above_50 < 40:
            score -= 25
            rules.append(f"Market Breadth (<40% above 50 DMA: {pct_above_50:.1f}%) (-25)")

        if ad_ratio >= 1.5:
            score += 15
            rules.append(f"Strong Advance/Decline Ratio ({ad_ratio:.2f}) (+15)")
        elif ad_ratio <= 0.67:
            score -= 15
            rules.append(f"Weak Advance/Decline Ratio ({ad_ratio:.2f}) (-15)")

        if bn_trend == "Bullish":
            score += 10
            rules.append("Bank NIFTY in Bullish Trend (+10)")
        else:
            score -= 10
            rules.append("Bank NIFTY in Bearish Trend (-10)")

        # Classification mapping
        if score >= 60:
            regime = "Strong Bullish"
        elif score >= 20:
            regime = "Bullish"
        elif score > -20:
            regime = "Neutral"
        elif score > -60:
            regime = "Bearish"
        else:
            regime = "Strong Bearish"

        volatility = latest_nifty.get("volatility_20d", 0.15)

        return {
            "regime": regime,
            "score": score,
            "confidence": min(100, abs(score) + 30),
            "rules_triggered": rules,
            "nifty_trend": "Above 200 DMA" if above_200d else "Below 200 DMA",
            "nifty_volatility_annualized": round(volatility * 100, 2) if pd.notna(volatility) else 0,
            "bank_nifty_trend": bn_trend,
            "breadth": {
                "total_tracked": total_stocks,
                "advances": advances,
                "declines": declines,
                "advance_decline_ratio": round(ad_ratio, 2),
                "pct_above_20_dma": round(pct_above_20, 1),
                "pct_above_50_dma": round(pct_above_50, 1),
                "pct_above_200_dma": round(pct_above_200, 1),
                "new_highs_20d": new_highs,
                "new_lows_20d": new_lows
            }
        }
