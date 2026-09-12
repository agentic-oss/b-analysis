import numpy as np
import pandas as pd
from typing import Dict, Any, List

class TechnicalEvents:
    """Identifies technical setups and chart patterns like Golden/Death Crosses, Breakouts, Support/Resistance."""

    @staticmethod
    def identify_events(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes a DataFrame containing calculated technical indicators.
        Returns a dictionary summarizing recent events (on latest row).
        """
        if df.empty or len(df) < 2:
            return {
                "golden_cross": False,
                "death_cross": False,
                "breakout_20d": False,
                "breakdown_20d": False,
                "unusual_volume": False,
                "support_level": None,
                "resistance_level": None,
                "trend_state": "Neutral"
            }

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # 1. Moving Average Crosses (50 vs 200 SMA)
        golden_cross = False
        death_cross = False
        if "sma_50" in df.columns and "sma_200" in df.columns:
            if prev["sma_50"] <= prev["sma_200"] and latest["sma_50"] > latest["sma_200"]:
                golden_cross = True
            elif prev["sma_50"] >= prev["sma_200"] and latest["sma_50"] < latest["sma_200"]:
                death_cross = True

        # 2. Breakouts / Breakdowns (20-day high/low)
        high_20_prev = df["high"].iloc[:-1].tail(20).max() if len(df) > 20 else df["high"].max()
        low_20_prev = df["low"].iloc[:-1].tail(20).min() if len(df) > 20 else df["low"].min()

        breakout_20d = latest["close"] > high_20_prev
        breakdown_20d = latest["close"] < low_20_prev

        # 3. Unusual Volume (> 2.0x 20-day average volume)
        rel_vol = latest.get("relative_volume", 1.0)
        unusual_volume = rel_vol >= 2.0

        # 4. Support and Resistance Levels (recent swing lows/highs)
        recent_window = df.tail(60)
        support_level = float(recent_window["low"].min())
        resistance_level = float(recent_window["high"].max())

        # 5. Trend State
        close = latest["close"]
        sma_50 = latest.get("sma_50", close)
        sma_200 = latest.get("sma_200", close)

        if close > sma_50 and sma_50 > sma_200:
            trend_state = "Uptrend"
        elif close < sma_50 and sma_50 < sma_200:
            trend_state = "Downtrend"
        else:
            trend_state = "Sideways / Consolidation"

        return {
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "breakout_20d": bool(breakout_20d),
            "breakdown_20d": bool(breakdown_20d),
            "unusual_volume": bool(unusual_volume),
            "support_level": round(support_level, 2),
            "resistance_level": round(resistance_level, 2),
            "trend_state": trend_state
        }
