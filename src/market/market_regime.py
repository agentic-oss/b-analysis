import pandas as pd
import numpy as np
from typing import Dict, Any, List

class MarketRegimeAnalyzer:
    """
    Analyzes overall market regime using index trends (NIFTY 50, NIFTY Bank),
    market breadth (% stocks above 20/50/200 DMA, advance/decline ratio, new highs/lows),
    and classifies environment into: Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish.
    """

    def analyze_market_regime(
        self,
        nifty_df: pd.DataFrame,
        bank_nifty_df: pd.DataFrame,
        all_stocks_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Calculates market-wide metrics and rule-based regime classification.
        """
        # NIFTY metrics
        nifty_latest = nifty_df.iloc[-1] if not nifty_df.empty else {}
        nifty_close = nifty_latest.get('close', 0.0)
        nifty_sma_20 = nifty_latest.get('sma_20', nifty_close)
        nifty_sma_50 = nifty_latest.get('sma_50', nifty_close)
        nifty_sma_200 = nifty_latest.get('sma_200', nifty_close)
        nifty_return_1d = nifty_latest.get('daily_return', 0.0)
        nifty_vol = nifty_latest.get('volatility_20d', 0.15)

        # Bank NIFTY metrics
        bank_latest = bank_nifty_df.iloc[-1] if not bank_nifty_df.empty else {}
        bank_close = bank_latest.get('close', 0.0)
        bank_sma_50 = bank_latest.get('sma_50', bank_close)

        # Market Breadth across all tracked stock DataFrames
        total_stocks = 0
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        advances = 0
        declines = 0
        new_highs = 0
        new_lows = 0

        for symbol, df in all_stocks_dfs.items():
            if df.empty or len(df) < 5:
                continue
            total_stocks += 1
            latest = df.iloc[-1]
            c = latest.get('close', 0.0)
            ret = latest.get('daily_return', 0.0)

            if ret > 0:
                advances += 1
            elif ret < 0:
                declines += 1

            if c > latest.get('sma_20', c):
                above_20dma += 1
            if c > latest.get('sma_50', c):
                above_50dma += 1
            if c > latest.get('sma_200', c):
                above_200dma += 1

            dist_high = latest.get('dist_52w_high', -1.0)
            dist_low = latest.get('dist_52w_low', 1.0)
            if dist_high >= -0.02:
                new_highs += 1
            if dist_low <= 0.02:
                new_lows += 1

        pct_above_20dma = (above_20dma / total_stocks * 100) if total_stocks > 0 else 50.0
        pct_above_50dma = (above_50dma / total_stocks * 100) if total_stocks > 0 else 50.0
        pct_above_200dma = (above_200dma / total_stocks * 100) if total_stocks > 0 else 50.0
        ad_ratio = (advances / declines) if declines > 0 else (float(advances) if advances > 0 else 1.0)

        # Transparent rule-based classification score
        score = 50.0

        # Trend component (up to +30 / -30)
        if nifty_close > nifty_sma_20 > nifty_sma_50 > nifty_sma_200:
            score += 30.0
        elif nifty_close > nifty_sma_50:
            score += 15.0
        elif nifty_close < nifty_sma_20 < nifty_sma_50 < nifty_sma_200:
            score -= 30.0
        elif nifty_close < nifty_sma_50:
            score -= 15.0

        # Breadth component (up to +20 / -20)
        if pct_above_50dma >= 70.0:
            score += 20.0
        elif pct_above_50dma >= 50.0:
            score += 10.0
        elif pct_above_50dma <= 30.0:
            score -= 20.0
        elif pct_above_50dma <= 50.0:
            score -= 10.0

        score = max(0.0, min(100.0, score))

        # Map score to Transparent Regime Labels
        if score >= 80.0:
            regime = "Strong Bullish"
        elif score >= 60.0:
            regime = "Bullish"
        elif score >= 40.0:
            regime = "Neutral"
        elif score >= 20.0:
            regime = "Bearish"
        else:
            regime = "Strong Bearish"

        return {
            "regime": regime,
            "regime_score": round(score, 2),
            "nifty_close": round(float(nifty_close), 2),
            "nifty_return_1d": round(float(nifty_return_1d), 4),
            "nifty_volatility_20d": round(float(nifty_vol), 4),
            "bank_nifty_close": round(float(bank_close), 2),
            "market_breadth": {
                "total_tracked": total_stocks,
                "advances": advances,
                "declines": declines,
                "advance_decline_ratio": round(float(ad_ratio), 2),
                "pct_above_20dma": round(float(pct_above_20dma), 2),
                "pct_above_50dma": round(float(pct_above_50dma), 2),
                "pct_above_200dma": round(float(pct_above_200dma), 2),
                "new_52w_highs": new_highs,
                "new_52w_lows": new_lows
            },
            "rules_description": "Regime based on NIFTY moving averages alignment (50%) and market breadth (% stocks > 50DMA, advance/decline ratio) (50%)."
        }
