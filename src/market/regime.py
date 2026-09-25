"""Market Regime Analysis Module."""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketRegimeDetector:
    """Analyzes market-wide trend, breadth, and volatility to classify the regime."""

    @staticmethod
    def analyze_regime(
        nifty_df: pd.DataFrame,
        bank_nifty_df: Optional[pd.DataFrame] = None,
        stock_dfs: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, Any]:
        """Classify market regime into Strong Bullish, Bullish, Neutral, Bearish, or Strong Bearish.

        Returns a detailed summary dictionary with classification, rules triggered, and breadth metrics.
        """
        if nifty_df is None or nifty_df.empty or len(nifty_df) < 20:
            return {
                "regime": "Neutral",
                "score": 50.0,
                "confidence": 50,
                "description": "Insufficient NIFTY data available for regime analysis.",
                "breadth": {}
            }

        latest_nifty = nifty_df.iloc[-1]
        nifty_close = float(latest_nifty["Close"])
        sma20 = float(latest_nifty.get("sma_20", nifty_close))
        sma50 = float(latest_nifty.get("sma_50", nifty_close))
        sma200 = float(latest_nifty.get("sma_200", nifty_close))

        # 1. NIFTY trend signals
        above_20d = nifty_close > sma20
        above_50d = nifty_close > sma50
        above_200d = nifty_close > sma200
        sma_aligned_bull = sma20 > sma50 > sma200

        # Bank NIFTY trend signal
        bank_above_50d = True
        if bank_nifty_df is not None and not bank_nifty_df.empty:
            latest_bank = bank_nifty_df.iloc[-1]
            bank_close = float(latest_bank["Close"])
            bank_sma50 = float(latest_bank.get("sma_50", bank_close))
            bank_above_50d = bank_close > bank_sma50

        # 2. Market Breadth analysis
        pct_above_20d = 50.0
        pct_above_50d = 50.0
        pct_above_200d = 50.0
        ad_ratio = 1.0
        new_highs_count = 0
        new_lows_count = 0

        if stock_dfs and len(stock_dfs) > 0:
            above_20_cnt = 0
            above_50_cnt = 0
            above_200_cnt = 0
            advances = 0
            declines = 0
            total_valid = 0

            for sym, s_df in stock_dfs.items():
                if s_df.empty or len(s_df) < 5:
                    continue
                s_latest = s_df.iloc[-1]
                s_close = float(s_latest["Close"])
                s_ret = float(s_latest.get("return_1d", 0.0))

                total_valid += 1
                if s_ret > 0:
                    advances += 1
                elif s_ret < 0:
                    declines += 1

                if s_close > float(s_latest.get("sma_20", s_close)):
                    above_20_cnt += 1
                if s_close > float(s_latest.get("sma_50", s_close)):
                    above_50_cnt += 1
                if s_close > float(s_latest.get("sma_200", s_close)):
                    above_200_cnt += 1

                if bool(s_latest.get("breakout", False)):
                    new_highs_count += 1
                if bool(s_latest.get("breakdown", False)):
                    new_lows_count += 1

            if total_valid > 0:
                pct_above_20d = (above_20_cnt / total_valid) * 100.0
                pct_above_50d = (above_50_cnt / total_valid) * 100.0
                pct_above_200d = (above_200_cnt / total_valid) * 100.0
                ad_ratio = (advances / max(declines, 1))

        # 3. Transparent rule-based regime scoring (0 - 100)
        score = 50.0

        # Trend points (-25 to +25)
        if above_200d:
            score += 10.0
        else:
            score -= 10.0

        if above_50d:
            score += 10.0
        else:
            score -= 10.0

        if above_20d:
            score += 5.0
        else:
            score -= 5.0

        # Breadth points (-25 to +25)
        if pct_above_50d > 70.0:
            score += 15.0
        elif pct_above_50d > 50.0:
            score += 5.0
        elif pct_above_50d < 30.0:
            score -= 15.0
        else:
            score -= 5.0

        if ad_ratio > 1.5:
            score += 10.0
        elif ad_ratio < 0.67:
            score -= 10.0

        # Clamp score between 0 and 100
        score = max(0.0, min(100.0, score))

        # Classification Tiers
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

        breadth_summary = {
            "advance_decline_ratio": round(ad_ratio, 2),
            "pct_above_20dma": round(pct_above_20d, 1),
            "pct_above_50dma": round(pct_above_50d, 1),
            "pct_above_200dma": round(pct_above_200d, 1),
            "new_highs": new_highs_count,
            "new_lows": new_lows_count
        }

        return {
            "date": str(pd.to_datetime(latest_nifty["Date"]).date()),
            "regime": regime,
            "regime_score": round(score, 1),
            "nifty_close": nifty_close,
            "nifty_above_200d": above_200d,
            "nifty_above_50d": above_50d,
            "bank_nifty_above_50d": bank_above_50d,
            "breadth": breadth_summary,
            "rules": [
                f"NIFTY Close ({nifty_close:.2f}) vs 200DMA ({sma200:.2f}): {'Above' if above_200d else 'Below'}",
                f"NIFTY Close vs 50DMA ({sma50:.2f}): {'Above' if above_50d else 'Below'}",
                f"Market Breadth (% stocks above 50DMA): {pct_above_50d:.1f}%",
                f"Advance/Decline Ratio: {ad_ratio:.2f}"
            ]
        }
