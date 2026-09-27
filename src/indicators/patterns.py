"""
Technical pattern detector for market events (Crosses, Breakouts, Support/Resistance).
"""
from typing import List, Dict, Any
import pandas as pd


class PatternDetector:
    """Detects technical events such as Golden/Death Cross, Breakouts, and Volume Surges."""

    @staticmethod
    def detect_events(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyzes the latest row(s) in a dataframe with technical indicators
        and returns a list of detected pattern events.
        """
        events = []
        if df.empty or len(df) < 2:
            return events

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        symbol = latest.get("ticker", "UNKNOWN")

        # 1. Golden Cross & Death Cross
        if (prev.get("sma_50", 0) <= prev.get("sma_200", 0)) and (latest.get("sma_50", 0) > latest.get("sma_200", 0)):
            events.append({"type": "Golden Cross", "symbol": symbol, "severity": "High", "bias": "Bullish"})
        elif (prev.get("sma_50", 0) >= prev.get("sma_200", 0)) and (latest.get("sma_50", 0) < latest.get("sma_200", 0)):
            events.append({"type": "Death Cross", "symbol": symbol, "severity": "High", "bias": "Bearish"})

        # 2. 20-day High Breakout / Low Breakdown
        rolling_20_high_prev = df["High"].iloc[:-1].tail(20).max()
        rolling_20_low_prev = df["Low"].iloc[:-1].tail(20).min()

        if latest["Close"] > rolling_20_high_prev:
            events.append({"type": "20-Day High Breakout", "symbol": symbol, "severity": "Medium", "bias": "Bullish"})
        elif latest["Close"] < rolling_20_low_prev:
            events.append({"type": "20-Day Low Breakdown", "symbol": symbol, "severity": "Medium", "bias": "Bearish"})

        # 3. Unusual Volume Surge (> 2.5x 20-day average)
        if latest.get("relative_volume", 0) >= 2.5:
            events.append({"type": "Unusual Volume Surge", "symbol": symbol, "severity": "Medium", "bias": "Neutral", "details": f"Rel Vol: {latest['relative_volume']:.2f}x"})

        # 4. RSI Overbought / Oversold
        if latest.get("rsi_14", 50) >= 70:
            events.append({"type": "RSI Overbought", "symbol": symbol, "severity": "Low", "bias": "Slightly Bearish"})
        elif latest.get("rsi_14", 50) <= 30:
            events.append({"type": "RSI Oversold", "symbol": symbol, "severity": "Low", "bias": "Slightly Bullish"})

        return events
