"""
Market Regime Analyzer module.
Evaluates market-wide metrics (NIFTY trend, BANK NIFTY trend, breadth, DMAs, highs/lows)
and classifies environment (Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish).
"""
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MarketRegimeAnalyzer:
    """
    Classifies market regime transparently using rule-based criteria.
    """

    @staticmethod
    def analyze(
        nifty_df: pd.DataFrame,
        banknifty_df: pd.DataFrame,
        stocks_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Analyzes current market breadth and regime across NIFTY, BANK NIFTY, and tracked stock universe.
        """
        if nifty_df.empty:
            return {
                "market_regime": "Neutral",
                "confidence": 50,
                "summary": "Insufficient market benchmark data",
                "details": {}
            }

        nifty_latest = nifty_df.iloc[-1]
        nifty_close = nifty_latest.get("close", 0)
        nifty_sma20 = nifty_latest.get("sma_20", nifty_close)
        nifty_sma50 = nifty_latest.get("sma_50", nifty_close)
        nifty_sma200 = nifty_latest.get("sma_200", nifty_close)
        nifty_rsi = nifty_latest.get("rsi_14", 50)
        nifty_vol = nifty_latest.get("volatility_20d", 0.15)

        banknifty_close = 0
        banknifty_sma50 = 0
        if not banknifty_df.empty:
            bank_latest = banknifty_df.iloc[-1]
            banknifty_close = bank_latest.get("close", 0)
            banknifty_sma50 = bank_latest.get("sma_50", banknifty_close)

        # Market Breadth across universe
        total_stocks = len(stocks_dfs)
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        new_highs_20d = 0
        new_lows_20d = 0
        advances = 0
        declines = 0

        for symbol, df in stocks_dfs.items():
            if df.empty or len(df) < 2:
                continue
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            c = latest.get("close", 0)
            ret = (c - prev.get("close", c))

            if ret > 0:
                advances += 1
            elif ret < 0:
                declines += 1

            if c > latest.get("sma_20", c):
                above_20dma += 1
            if c > latest.get("sma_50", c):
                above_50dma += 1
            if c > latest.get("sma_200", c):
                above_200dma += 1

            if latest.get("breakout_20d", False):
                new_highs_20d += 1
            if latest.get("breakdown_20d", False):
                new_lows_20d += 1

        pct_above_20dma = (above_20dma / total_stocks * 100) if total_stocks > 0 else 50
        pct_above_50dma = (above_50dma / total_stocks * 100) if total_stocks > 0 else 50
        pct_above_200dma = (above_200dma / total_stocks * 100) if total_stocks > 0 else 50
        ad_ratio = (advances / max(declines, 1))

        # Rule-based scoring for Market Regime classification
        regime_score = 0  # Range -10 to +10

        # Criterion 1: NIFTY price vs SMAs
        if nifty_close > nifty_sma20 and nifty_sma20 > nifty_sma50 and nifty_sma50 > nifty_sma200:
            regime_score += 3
        elif nifty_close > nifty_sma50:
            regime_score += 1.5
        elif nifty_close < nifty_sma20 and nifty_sma20 < nifty_sma50 and nifty_sma50 < nifty_sma200:
            regime_score -= 3
        elif nifty_close < nifty_sma50:
            regime_score -= 1.5

        # Criterion 2: Market Breadth (% above 50 DMA)
        if pct_above_50dma >= 70:
            regime_score += 3
        elif pct_above_50dma >= 50:
            regime_score += 1
        elif pct_above_50dma <= 30:
            regime_score -= 3
        else:
            regime_score -= 1

        # Criterion 3: Advance/Decline ratio
        if ad_ratio >= 1.5:
            regime_score += 2
        elif ad_ratio <= 0.67:
            regime_score -= 2

        # Criterion 4: Bank NIFTY confirmation
        if banknifty_close > banknifty_sma50:
            regime_score += 1
        else:
            regime_score -= 1

        # Classification mapping
        if regime_score >= 6:
            regime = "Strong Bullish"
            confidence = min(100, int(60 + regime_score * 4))
        elif regime_score >= 2:
            regime = "Bullish"
            confidence = int(50 + regime_score * 5)
        elif regime_score <= -6:
            regime = "Strong Bearish"
            confidence = min(100, int(60 + abs(regime_score) * 4))
        elif regime_score <= -2:
            regime = "Bearish"
            confidence = int(50 + abs(regime_score) * 5)
        else:
            regime = "Neutral"
            confidence = 50

        return {
            "market_regime": regime,
            "confidence": confidence,
            "regime_score": regime_score,
            "details": {
                "nifty_close": float(nifty_close),
                "nifty_rsi_14": float(nifty_rsi),
                "nifty_volatility_20d": float(nifty_vol),
                "total_stocks_analyzed": total_stocks,
                "advances": advances,
                "declines": declines,
                "advance_decline_ratio": round(float(ad_ratio), 2),
                "pct_above_20dma": round(float(pct_above_20dma), 2),
                "pct_above_50dma": round(float(pct_above_50dma), 2),
                "pct_above_200dma": round(float(pct_above_200dma), 2),
                "new_highs_20d": new_highs_20d,
                "new_lows_20d": new_lows_20d
            }
        }
