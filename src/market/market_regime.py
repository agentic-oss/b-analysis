from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MarketRegimeAnalyzer:
    """
    Analyzes overall Indian stock market environment (NIFTY 50, Bank NIFTY, Breadth, DMAs).
    Classifies environment into transparent rule-based regimes:
    - Strong Bullish
    - Bullish
    - Neutral
    - Bearish
    - Strong Bearish
    """

    def analyze_market_regime(
        self,
        nifty_df: pd.DataFrame,
        bank_nifty_df: Optional[pd.DataFrame],
        stock_dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        result = {
            "nifty_trend": "Neutral",
            "nifty_close": None,
            "nifty_sma_20": None,
            "nifty_sma_50": None,
            "nifty_sma_200": None,
            "bank_nifty_trend": "Neutral",
            "market_breadth": {
                "total_tracked": len(stock_dfs),
                "advance_decline_ratio": 1.0,
                "pct_above_20dma": 50.0,
                "pct_above_50dma": 50.0,
                "pct_above_200dma": 50.0,
                "new_20d_highs": 0,
                "new_20d_lows": 0,
            },
            "regime": "Neutral",
            "regime_score": 50.0,
            "classification_rules": [
                "Strong Bullish: NIFTY > 20, 50 & 200 DMA + Breadth > 60% above 50 DMA + AD Ratio > 1.2",
                "Bullish: NIFTY > 50 DMA + Breadth > 50% above 50 DMA",
                "Neutral: NIFTY mixed relative to DMAs or mixed breadth (40-60%)",
                "Bearish: NIFTY < 50 DMA + Breadth < 40% above 50 DMA",
                "Strong Bearish: NIFTY < 20, 50 & 200 DMA + Breadth < 30% above 50 DMA + AD Ratio < 0.7"
            ]
        }

        if nifty_df.empty:
            return result

        last_nifty = nifty_df.iloc[-1]
        close = float(last_nifty["close"])
        sma20 = float(last_nifty.get("sma_20", close))
        sma50 = float(last_nifty.get("sma_50", close))
        sma200 = float(last_nifty.get("sma_200", close))

        result["nifty_close"] = close
        result["nifty_sma_20"] = sma20
        result["nifty_sma_50"] = sma50
        result["nifty_sma_200"] = sma200

        if close > sma20 and close > sma50 and close > sma200:
            result["nifty_trend"] = "Strong Bullish"
        elif close > sma50:
            result["nifty_trend"] = "Bullish"
        elif close < sma50 and close < sma200:
            result["nifty_trend"] = "Strong Bearish"
        elif close < sma50:
            result["nifty_trend"] = "Bearish"

        # Bank NIFTY trend
        if bank_nifty_df is not None and not bank_nifty_df.empty:
            b_last = bank_nifty_df.iloc[-1]
            b_close = float(b_last["close"])
            b_sma50 = float(b_last.get("sma_50", b_close))
            result["bank_nifty_trend"] = "Bullish" if b_close >= b_sma50 else "Bearish"

        # Breadth statistics across stock universe
        above_20 = 0
        above_50 = 0
        above_200 = 0
        advances = 0
        declines = 0
        new_highs = 0
        new_lows = 0
        valid_stocks = 0

        for sym, df in stock_dfs.items():
            if df.empty or len(df) < 5:
                continue
            valid_stocks += 1
            row = df.iloc[-1]
            c = float(row["close"])
            s20 = float(row.get("sma_20", c))
            s50 = float(row.get("sma_50", c))
            s200 = float(row.get("sma_200", c))
            ret = float(row.get("return_1d", 0.0))

            if c >= s20:
                above_20 += 1
            if c >= s50:
                above_50 += 1
            if c >= s200:
                above_200 += 1

            if ret > 0:
                advances += 1
            elif ret < 0:
                declines += 1

            if bool(row.get("breakout_20d", False)):
                new_highs += 1
            if bool(row.get("breakdown_20d", False)):
                new_lows += 1

        if valid_stocks > 0:
            pct_20 = (above_20 / valid_stocks) * 100
            pct_50 = (above_50 / valid_stocks) * 100
            pct_200 = (above_200 / valid_stocks) * 100
            ad_ratio = (advances / max(1, declines))

            result["market_breadth"]["total_tracked"] = valid_stocks
            result["market_breadth"]["pct_above_20dma"] = round(pct_20, 2)
            result["market_breadth"]["pct_above_50dma"] = round(pct_50, 2)
            result["market_breadth"]["pct_above_200dma"] = round(pct_200, 2)
            result["market_breadth"]["advance_decline_ratio"] = round(ad_ratio, 2)
            result["market_breadth"]["new_20d_highs"] = new_highs
            result["market_breadth"]["new_20d_lows"] = new_lows

            # Classification rules
            if close > sma50 and close > sma200 and pct_50 >= 60 and ad_ratio >= 1.2:
                result["regime"] = "Strong Bullish"
                result["regime_score"] = 90.0
            elif close > sma50 and pct_50 >= 50:
                result["regime"] = "Bullish"
                result["regime_score"] = 70.0
            elif close < sma50 and close < sma200 and pct_50 <= 30:
                result["regime"] = "Strong Bearish"
                result["regime_score"] = 10.0
            elif close < sma50 or pct_50 < 40:
                result["regime"] = "Bearish"
                result["regime_score"] = 30.0
            else:
                result["regime"] = "Neutral"
                result["regime_score"] = 50.0

        return result
