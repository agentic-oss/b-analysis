import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class MarketRegimeAnalyzer:
    """
    Evaluates market regime using transparent rule-based indicators across NIFTY 50,
    BANK NIFTY, and market-wide breadth statistics.
    """

    def analyze(self, nifty_df: pd.DataFrame, bank_nifty_df: pd.DataFrame, stock_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Classifies market regime into one of:
        'Strong Bullish', 'Bullish', 'Neutral', 'Bearish', 'Strong Bearish'.
        """
        result = {
            "regime": "Neutral",
            "score": 50,
            "nifty_trend": "Neutral",
            "bank_nifty_trend": "Neutral",
            "nifty_return_1d": 0.0,
            "nifty_return_20d": 0.0,
            "market_breadth": {
                "advance_decline_ratio": 1.0,
                "pct_above_20dma": 50.0,
                "pct_above_50dma": 50.0,
                "pct_above_200dma": 50.0,
                "new_20d_highs": 0,
                "new_20d_lows": 0
            },
            "rules_triggered": []
        }

        if nifty_df.empty:
            return result

        nifty_latest = nifty_df.iloc[-1]
        result["nifty_return_1d"] = float(nifty_latest.get("return_1d", 0.0) or 0.0)
        result["nifty_return_20d"] = float(nifty_latest.get("return_20d", 0.0) or 0.0)

        # 1. Evaluate NIFTY trend
        close = nifty_latest.get("close", 0)
        sma20 = nifty_latest.get("sma_20", close)
        sma50 = nifty_latest.get("sma_50", close)
        sma200 = nifty_latest.get("sma_200", close)

        if close > sma20 > sma50 > sma200:
            result["nifty_trend"] = "Strong Bullish"
        elif close > sma50:
            result["nifty_trend"] = "Bullish"
        elif close < sma20 < sma50 < sma200:
            result["nifty_trend"] = "Strong Bearish"
        elif close < sma50:
            result["nifty_trend"] = "Bearish"

        # 2. Evaluate Bank NIFTY trend
        if not bank_nifty_df.empty:
            b_latest = bank_nifty_df.iloc[-1]
            b_close = b_latest.get("close", 0)
            b_sma50 = b_latest.get("sma_50", b_close)
            if b_close > b_sma50:
                result["bank_nifty_trend"] = "Bullish"
            else:
                result["bank_nifty_trend"] = "Bearish"

        # 3. Market Breadth across stock universe
        if stock_dfs:
            advances = 0
            declines = 0
            above_20 = 0
            above_50 = 0
            above_200 = 0
            new_highs = 0
            new_lows = 0
            total_stocks = len(stock_dfs)

            for sym, sdf in stock_dfs.items():
                if sdf.empty:
                    continue
                s_latest = sdf.iloc[-1]
                s_close = s_latest.get("close", 0)
                s_ret = s_latest.get("return_1d", 0) or 0

                if s_ret > 0:
                    advances += 1
                elif s_ret < 0:
                    declines += 1

                if s_close > s_latest.get("sma_20", s_close):
                    above_20 += 1
                if s_close > s_latest.get("sma_50", s_close):
                    above_50 += 1
                if s_close > s_latest.get("sma_200", s_close):
                    above_200 += 1

                if s_latest.get("breakout_20d", False):
                    new_highs += 1
                if s_latest.get("breakdown_20d", False):
                    new_lows += 1

            ad_ratio = advances / (declines if declines > 0 else 1)
            result["market_breadth"]["advance_decline_ratio"] = round(float(ad_ratio), 2)
            result["market_breadth"]["pct_above_20dma"] = round(float(above_20 / total_stocks * 100), 2)
            result["market_breadth"]["pct_above_50dma"] = round(float(above_50 / total_stocks * 100), 2)
            result["market_breadth"]["pct_above_200dma"] = round(float(above_200 / total_stocks * 100), 2)
            result["market_breadth"]["new_20d_highs"] = new_highs
            result["market_breadth"]["new_20d_lows"] = new_lows

        # 4. Score formulation (0 to 100)
        score = 50
        if result["nifty_trend"] == "Strong Bullish":
            score += 25
            result["rules_triggered"].append("NIFTY in Strong Bullish MA alignment (+25)")
        elif result["nifty_trend"] == "Bullish":
            score += 15
            result["rules_triggered"].append("NIFTY above 50 DMA (+15)")
        elif result["nifty_trend"] == "Bearish":
            score -= 15
            result["rules_triggered"].append("NIFTY below 50 DMA (-15)")
        elif result["nifty_trend"] == "Strong Bearish":
            score -= 25
            result["rules_triggered"].append("NIFTY in Strong Bearish MA alignment (-25)")

        pct_50 = result["market_breadth"]["pct_above_50dma"]
        if pct_50 >= 70:
            score += 20
            result["rules_triggered"].append(">70% stocks above 50 DMA (+20)")
        elif pct_50 <= 30:
            score -= 20
            result["rules_triggered"].append("<30% stocks above 50 DMA (-20)")

        score = max(0, min(100, score))
        result["score"] = score

        if score >= 80:
            result["regime"] = "Strong Bullish"
        elif score >= 60:
            result["regime"] = "Bullish"
        elif score >= 40:
            result["regime"] = "Neutral"
        elif score >= 20:
            result["regime"] = "Bearish"
        else:
            result["regime"] = "Strong Bearish"

        return result
