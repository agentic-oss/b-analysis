import pandas as pd
import numpy as np
from typing import Dict, Any, List

class MarketRegimeAnalyzer:
    """Analyzes overall market conditions using NIFTY benchmark, Bank NIFTY, and market breadth."""

    @staticmethod
    def analyze_regime(nifty_df: pd.DataFrame, banknifty_df: pd.DataFrame, stock_dfs: List[pd.DataFrame]) -> Dict[str, Any]:
        """
        Calculates market regime metrics and classifies the market environment.
        Classification options: Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish.
        """
        if nifty_df.empty or len(nifty_df) < 50:
            return {
                "regime": "Neutral",
                "confidence": 50.0,
                "nifty_trend": "Unknown",
                "banknifty_trend": "Unknown",
                "breadth": {},
                "explanation": "Insufficient benchmark history"
            }

        nifty_latest = nifty_df.iloc[-1]
        nifty_close = float(nifty_latest['close'])
        nifty_sma20 = float(nifty_latest.get('sma_20', nifty_close))
        nifty_sma50 = float(nifty_latest.get('sma_50', nifty_close))
        nifty_sma200 = float(nifty_latest.get('sma_200', nifty_close))

        # NIFTY Trend Score (-2 to +2)
        nifty_score = 0
        if nifty_close >= nifty_sma20: nifty_score += 1
        if nifty_close >= nifty_sma50: nifty_score += 1
        if nifty_close >= nifty_sma200: nifty_score += 1
        if nifty_sma50 >= nifty_sma200: nifty_score += 1

        nifty_trend = "Strong Uptrend" if nifty_score >= 3 else ("Uptrend" if nifty_score == 2 else ("Downtrend" if nifty_score == 1 else "Strong Downtrend"))

        # BANK NIFTY Trend
        banknifty_trend = "Neutral"
        if not banknifty_df.empty and len(banknifty_df) >= 20:
            bk_close = float(banknifty_df.iloc[-1]['close'])
            bk_sma50 = float(banknifty_df.iloc[-1].get('sma_50', bk_close))
            banknifty_trend = "Uptrend" if bk_close >= bk_sma50 else "Downtrend"

        # Market Breadth Calculation
        total_stocks = len(stock_dfs)
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        advances = 0
        declines = 0
        new_highs_20d = 0
        new_lows_20d = 0

        for df in stock_dfs:
            if df.empty or len(df) < 20:
                continue
            latest = df.iloc[-1]
            c = latest['close']
            if c >= latest.get('sma_20', c): above_20dma += 1
            if c >= latest.get('sma_50', c): above_50dma += 1
            if c >= latest.get('sma_200', c): above_200dma += 1

            ret = latest.get('return_1d', 0)
            if ret > 0: advances += 1
            elif ret < 0: declines += 1

            high_20 = df['high'].iloc[-21:-1].max() if len(df) >= 21 else df['high'].max()
            low_20 = df['low'].iloc[-21:-1].min() if len(df) >= 21 else df['low'].min()
            if c >= high_20: new_highs_20d += 1
            if c <= low_20: new_lows_20d += 1

        pct_above_20dma = (above_20dma / total_stocks * 100.0) if total_stocks > 0 else 50.0
        pct_above_50dma = (above_50dma / total_stocks * 100.0) if total_stocks > 0 else 50.0
        pct_above_200dma = (above_200dma / total_stocks * 100.0) if total_stocks > 0 else 50.0
        ad_ratio = (advances / (declines + 1e-5)) if declines > 0 else float(advances)

        # Composite Regime Classification Rule
        breadth_score = (pct_above_20dma * 0.4) + (pct_above_50dma * 0.4) + (pct_above_200dma * 0.2)

        if nifty_score >= 3 and breadth_score >= 65:
            regime = "Strong Bullish"
        elif nifty_score >= 2 and breadth_score >= 50:
            regime = "Bullish"
        elif nifty_score <= 1 and breadth_score <= 35:
            regime = "Strong Bearish"
        elif nifty_score <= 1 or breadth_score <= 45:
            regime = "Bearish"
        else:
            regime = "Neutral"

        return {
            "date": str(nifty_latest['date']),
            "market_regime": regime,
            "nifty_close": nifty_close,
            "nifty_trend": nifty_trend,
            "banknifty_trend": banknifty_trend,
            "nifty_volatility_20d": float(nifty_latest.get('volatility_20d', 0.15)),
            "breadth": {
                "total_tracked": total_stocks,
                "pct_above_20dma": round(pct_above_20dma, 2),
                "pct_above_50dma": round(pct_above_50dma, 2),
                "pct_above_200dma": round(pct_above_200dma, 2),
                "advance_decline_ratio": round(ad_ratio, 2),
                "advances": advances,
                "declines": declines,
                "new_highs_20d": new_highs_20d,
                "new_lows_20d": new_lows_20d
            },
            "rules_applied": "Rule-based classification combining NIFTY 20/50/200 DMA alignment with multi-factor market breadth (% stocks above 20/50/200 DMA and Advance/Decline ratio)."
        }
