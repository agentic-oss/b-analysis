import pandas as pd
import numpy as np
from typing import Dict, Any, List

class PatternEngine:
    """
    Detects technical events (crossovers, breakouts, unusual volume, support/resistance).
    """

    @staticmethod
    def detect_events(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Expects single stock DataFrame sorted by date ascending with calculated technical indicators.
        Returns dictionary of detected events and key technical levels.
        """
        events = []
        support_levels = []
        resistance_levels = []

        if df.empty or len(df) < 20:
            return {
                "events": events,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels
            }

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # 1. Crossovers (Golden Cross & Death Cross)
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            if prev['sma_50'] <= prev['sma_200'] and latest['sma_50'] > latest['sma_200']:
                events.append("Golden Cross (SMA 50 crossed above SMA 200)")
            elif prev['sma_50'] >= prev['sma_200'] and latest['sma_50'] < latest['sma_200']:
                events.append("Death Cross (SMA 50 crossed below SMA 200)")

        # 2. Breakouts / Breakdowns (20-day high/low)
        high_20 = df['high'].iloc[-21:-1].max() if len(df) >= 21 else df['high'].max()
        low_20 = df['low'].iloc[-21:-1].min() if len(df) >= 21 else df['low'].min()

        if latest['close'] > high_20:
            events.append("20-Day High Breakout")
        elif latest['close'] < low_20:
            events.append("20-Day Low Breakdown")

        # 3. Unusual Volume
        rel_vol = latest.get('relative_volume', 1.0)
        if rel_vol >= 2.5:
            events.append(f"Unusual Volume Spike ({rel_vol:.1f}x 20-day average)")

        # 4. Momentum / Overbought / Oversold
        rsi = latest.get('rsi_14', 50.0)
        if rsi >= 70:
            events.append("RSI Overbought (>=70)")
        elif rsi <= 30:
            events.append("RSI Oversold (<=30)")

        # 5. Support & Resistance Levels (Recent 60 days percentiles)
        recent = df.tail(60)
        sup1 = np.percentile(recent['low'], 10)
        sup2 = np.percentile(recent['low'], 25)
        res1 = np.percentile(recent['high'], 75)
        res2 = np.percentile(recent['high'], 90)

        support_levels = sorted(list(set([round(float(sup1), 2), round(float(sup2), 2)])))
        resistance_levels = sorted(list(set([round(float(res1), 2), round(float(res2), 2)])))

        return {
            "events": events,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels
        }
