"""
Technical Indicators & Signal Detection Module.
Calculates trend, momentum, volatility, volume, and price structure indicators.
Identifies technical signals (crosses, breakouts, support/resistance, volume spikes).
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculates deterministic technical indicators on price time-series."""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all standard technical indicators on a stock/index DataFrame.
        Requires columns: ['open', 'high', 'low', 'close', 'volume'].
        DataFrame must be sorted by date ascending.
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy()

        # 1. Trend Indicators
        for period in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{period}"] = df["close"].rolling(window=period, min_periods=1).mean()

        for period in [9, 20, 50, 200]:
            df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()

        # 2. Momentum Indicators
        # RSI 14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["rsi_14"] = df["rsi_14"].fillna(50.0)

        # Stochastic RSI
        rsi_min = df["rsi_14"].rolling(window=14, min_periods=1).min()
        rsi_max = df["rsi_14"].rolling(window=14, min_periods=1).max()
        stoch_rsi = (df["rsi_14"] - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
        df["stoch_rsi"] = stoch_rsi.fillna(0.5)

        # MACD (12, 26, 9)
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # Rate of Change (ROC 12)
        df["roc_12"] = df["close"].pct_change(periods=12) * 100
        df["momentum"] = df["close"].diff(periods=10)

        # 3. Volatility Indicators
        # ATR 14
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(df["close"] / df["close"].shift(1))
        df["volatility_20d"] = log_ret.rolling(window=20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        sma_20 = df["sma_20"]
        rolling_std = df["close"].rolling(window=20, min_periods=1).std()
        df["bb_upper"] = sma_20 + (rolling_std * 2)
        df["bb_lower"] = sma_20 - (rolling_std * 2)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / sma_20.replace(0, np.nan)

        # Volatility Regime Label
        vol_median = df["volatility_20d"].rolling(window=250, min_periods=20).median()
        df["volatility_regime"] = np.where(
            df["volatility_20d"] > vol_median * 1.3, "High",
            np.where(df["volatility_20d"] < vol_median * 0.7, "Low", "Normal")
        )

        # 4. Volume Indicators
        if "volume" in df.columns and (df["volume"] > 0).any():
            df["volume_sma_20"] = df["volume"].rolling(window=20, min_periods=1).mean()
            df["relative_volume"] = df["volume"] / df["volume_sma_20"].replace(0, np.nan)
            df["volume_change"] = df["volume"].pct_change()

            # OBV (On-Balance Volume)
            obv_direction = np.sign(df["close"].diff().fillna(0))
            df["obv"] = (obv_direction * df["volume"]).cumsum()

            # Accumulation / Distribution (A/D)
            mf_multiplier = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]).replace(0, np.nan)
            mf_multiplier = mf_multiplier.fillna(0)
            mf_volume = mf_multiplier * df["volume"]
            df["ad_line"] = mf_volume.cumsum()
        else:
            df["volume_sma_20"] = 0.0
            df["relative_volume"] = 1.0
            df["volume_change"] = 0.0
            df["obv"] = 0.0
            df["ad_line"] = 0.0

        # 5. Price Structure & Returns
        df["daily_return"] = df["close"].pct_change().fillna(0)
        df["gap_pct"] = ((df["open"] - df["close"].shift(1)) / df["close"].shift(1)).fillna(0) * 100
        df["intraday_range_pct"] = ((df["high"] - df["low"]) / df["low"]).fillna(0) * 100

        # MA Distance %
        df["dist_sma_20"] = ((df["close"] - df["sma_20"]) / df["sma_20"]) * 100
        df["dist_sma_50"] = ((df["close"] - df["sma_50"]) / df["sma_50"]) * 100
        df["dist_sma_200"] = ((df["close"] - df["sma_200"]) / df["sma_200"]) * 100

        # 52-Week High/Low Distance
        high_52w = df["high"].rolling(window=250, min_periods=10).max()
        low_52w = df["low"].rolling(window=250, min_periods=10).min()
        df["dist_52w_high"] = ((df["close"] - high_52w) / high_52w) * 100
        df["dist_52w_low"] = ((df["close"] - low_52w) / low_52w) * 100

        return df

    @staticmethod
    def detect_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects actionable technical signals on the latest row of the DataFrame.
        """
        if df.empty or len(df) < 2:
            return {
                "golden_cross": False,
                "death_cross": False,
                "breakout": False,
                "breakdown": False,
                "unusual_volume": False,
                "support_level": None,
                "resistance_level": None,
                "trend_state": "Neutral",
                "signals_list": [],
            }

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signals = []

        # 1. Golden Cross & Death Cross (SMA 50 vs SMA 200)
        golden_cross = (prev["sma_50"] <= prev["sma_200"]) and (latest["sma_50"] > latest["sma_200"])
        death_cross = (prev["sma_50"] >= prev["sma_200"]) and (latest["sma_50"] < latest["sma_200"])

        if golden_cross:
            signals.append("Golden Cross (50 DMA crossed above 200 DMA)")
        if death_cross:
            signals.append("Death Cross (50 DMA crossed below 200 DMA)")

        # 2. Breakouts & Breakdowns (20-day high/low)
        high_20d_prev = df["high"].iloc[:-1].tail(20).max()
        low_20d_prev = df["low"].iloc[:-1].tail(20).min()

        breakout = latest["close"] > high_20d_prev
        breakdown = latest["close"] < low_20d_prev

        if breakout:
            signals.append("20-Day High Breakout")
        if breakdown:
            signals.append("20-Day Low Breakdown")

        # 3. Unusual Volume (> 2.0x 20-day SMA volume)
        rel_vol = latest.get("relative_volume", 1.0)
        unusual_volume = bool(rel_vol > 2.0)
        if unusual_volume:
            signals.append(f"Unusual Volume Spike ({rel_vol:.1f}x 20-day average)")

        # 4. Support & Resistance (Pivot levels over last 50 days)
        window_50 = df.tail(50)
        support_level = float(window_50["low"].min())
        resistance_level = float(window_50["high"].max())

        # 5. Trend State
        if latest["close"] > latest["sma_20"] > latest["sma_50"] > latest["sma_200"]:
            trend_state = "Strong Uptrend"
        elif latest["close"] > latest["sma_50"]:
            trend_state = "Uptrend"
        elif latest["close"] < latest["sma_20"] < latest["sma_50"] < latest["sma_200"]:
            trend_state = "Strong Downtrend"
        elif latest["close"] < latest["sma_50"]:
            trend_state = "Downtrend"
        else:
            trend_state = "Sideways / Neutral"

        return {
            "golden_cross": bool(golden_cross),
            "death_cross": bool(death_cross),
            "breakout": bool(breakout),
            "breakdown": bool(breakdown),
            "unusual_volume": unusual_volume,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "trend_state": trend_state,
            "signals_list": signals,
        }
