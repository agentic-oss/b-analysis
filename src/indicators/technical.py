"""
Technical Indicator Calculations for Stock Analysis.
Calculates trend, momentum, volatility, volume, and price structure indicators.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


class TechnicalAnalyzer:
    """Calculates deterministic technical indicators and identifies signals."""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all technical indicators on a historical OHLCV dataframe.
        Expects columns: ['date', 'open', 'high', 'low', 'close', 'volume']
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy().sort_values("date").reset_index(drop=True)

        # 1. Simple Moving Averages (SMA)
        for period in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{period}"] = df["close"].rolling(window=period).mean()

        # 2. Exponential Moving Averages (EMA)
        for period in [9, 20, 50, 200]:
            df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()

        # 3. RSI 14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, np.nan))
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["rsi_14"] = df["rsi_14"].fillna(50)

        # 4. Stochastic RSI (14)
        rsi_min = df["rsi_14"].rolling(window=14).min()
        rsi_max = df["rsi_14"].rolling(window=14).max()
        stoch_rsi = (df["rsi_14"] - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
        df["stoch_rsi"] = stoch_rsi.fillna(0.5)
        df["stoch_rsi_k"] = df["stoch_rsi"].rolling(window=3).mean().fillna(0.5)
        df["stoch_rsi_d"] = df["stoch_rsi_k"].rolling(window=3).mean().fillna(0.5)

        # 5. MACD (12, 26, 9)
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # 6. Rate of Change (ROC 12) & Momentum
        df["roc_12"] = df["close"].pct_change(periods=12) * 100
        df["momentum_10"] = df["close"] - df["close"].shift(10)

        # 7. Average True Range (ATR 14)
        high_low = df["high"] - df["low"]
        high_prev_close = (df["high"] - df["close"].shift(1)).abs()
        low_prev_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14).mean()

        # 8. Historical Volatility (20-day annualized)
        log_ret = np.log(df["close"] / df["close"].shift(1))
        df["volatility_20d"] = log_ret.rolling(window=20).std() * np.sqrt(252)

        # 9. Bollinger Bands (20, 2)
        df["bb_middle"] = df["sma_20"]
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (2 * bb_std)
        df["bb_lower"] = df["bb_middle"] - (2 * bb_std)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"].replace(0, np.nan)

        # Volatility regime
        vol_med = df["volatility_20d"].rolling(window=100, min_periods=20).median()
        df["volatility_regime"] = np.where(df["volatility_20d"] > vol_med * 1.2, "High Volatility",
                                  np.where(df["volatility_20d"] < vol_med * 0.8, "Low Volatility", "Normal Volatility"))

        # 10. Volume Indicators
        df["volume_sma_20"] = df["volume"].rolling(window=20).mean()
        df["relative_volume"] = df["volume"] / df["volume_sma_20"].replace(0, np.nan)
        df["volume_change"] = df["volume"].pct_change()

        # On-Balance Volume (OBV)
        obv = [0]
        close_vals = df["close"].values
        vol_vals = df["volume"].values
        for i in range(1, len(df)):
            if close_vals[i] > close_vals[i - 1]:
                obv.append(obv[-1] + vol_vals[i])
            elif close_vals[i] < close_vals[i - 1]:
                obv.append(obv[-1] - vol_vals[i])
            else:
                obv.append(obv[-1])
        df["obv"] = obv

        # Accumulation / Distribution Line (A/D)
        clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]).replace(0, np.nan)
        df["ad_line"] = (clv.fillna(0) * df["volume"]).cumsum()

        # 11. Price Returns & Structure
        df["return_1d"] = df["close"].pct_change(1)
        df["return_5d"] = df["close"].pct_change(5)
        df["return_20d"] = df["close"].pct_change(20)
        df["gap_pct"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1).replace(0, np.nan) * 100
        df["intraday_range_pct"] = (df["high"] - df["low"]) / df["open"].replace(0, np.nan) * 100

        # Moving average distances
        df["dist_sma_20"] = (df["close"] - df["sma_20"]) / df["sma_20"].replace(0, np.nan) * 100
        df["dist_sma_50"] = (df["close"] - df["sma_50"]) / df["sma_50"].replace(0, np.nan) * 100
        df["dist_sma_200"] = (df["close"] - df["sma_200"]) / df["sma_200"].replace(0, np.nan) * 100

        # 52-week high / low distance
        high_52w = df["high"].rolling(window=252, min_periods=20).max()
        low_52w = df["low"].rolling(window=252, min_periods=20).min()
        df["dist_52w_high"] = (df["close"] - high_52w) / high_52w.replace(0, np.nan) * 100
        df["dist_52w_low"] = (df["close"] - low_52w) / low_52w.replace(0, np.nan) * 100

        return df

    @staticmethod
    def identify_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """Identifies technical signals on the latest row of processed dataframe."""
        if df.empty or len(df) < 2:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signals = []

        # Moving Average Crossovers
        if pd.notna(latest.get("sma_50")) and pd.notna(latest.get("sma_200")):
            if prev["sma_50"] <= prev["sma_200"] and latest["sma_50"] > latest["sma_200"]:
                signals.append("Golden Cross (50 DMA crossed above 200 DMA)")
            elif prev["sma_50"] >= prev["sma_200"] and latest["sma_50"] < latest["sma_200"]:
                signals.append("Death Cross (50 DMA crossed below 200 DMA)")

        # Breakouts / Breakdowns (20-day high/low)
        high_20 = df["high"].iloc[-21:-1].max() if len(df) >= 21 else None
        low_20 = df["low"].iloc[-21:-1].min() if len(df) >= 21 else None

        if high_20 and latest["close"] > high_20:
            signals.append("20-Day High Breakout")
        elif low_20 and latest["close"] < low_20:
            signals.append("20-Day Low Breakdown")

        # Unusual Volume
        if pd.notna(latest.get("relative_volume")) and latest["relative_volume"] >= 2.0:
            signals.append(f"Unusual Volume ({latest['relative_volume']:.1f}x 20-day avg)")

        # RSI Overbought / Oversold
        rsi = latest.get("rsi_14", 50)
        if rsi >= 70:
            signals.append(f"Overbought RSI ({rsi:.1f})")
        elif rsi <= 30:
            signals.append(f"Oversold RSI ({rsi:.1f})")

        # Support & Resistance levels (Pivot Points)
        pivot = (latest["high"] + latest["low"] + latest["close"]) / 3.0
        r1 = (2 * pivot) - latest["low"]
        s1 = (2 * pivot) - latest["high"]

        return {
            "signals": signals,
            "support_resistance": {
                "pivot": round(pivot, 2),
                "r1": round(r1, 2),
                "s1": round(s1, 2)
            }
        }
