import numpy as np
import pandas as pd
from typing import Dict, Any, List

class TechnicalIndicators:
    """Calculates deterministic technical indicators and price action patterns."""

    @staticmethod
    def compute_all(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 5:
            return df

        df = df.copy()

        # Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{p}"] = df["close"].rolling(window=p, min_periods=1).mean()

        for p in [9, 20, 50, 200]:
            df[f"ema_{p}"] = df["close"].ewm(span=p, adjust=False).mean()

        # Returns
        df["return_1d"] = df["close"].pct_change(1)
        df["return_5d"] = df["close"].pct_change(5)
        df["return_20d"] = df["close"].pct_change(20)

        # RSI (14)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss.replace(0, 1e-9))
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # Stochastic RSI
        min_rsi = df["rsi_14"].rolling(14, min_periods=1).min()
        max_rsi = df["rsi_14"].rolling(14, min_periods=1).max()
        stoch_denom = (max_rsi - min_rsi).replace(0, 1e-9)
        df["stoch_rsi"] = (df["rsi_14"] - min_rsi) / stoch_denom

        # MACD (12, 26, 9)
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        # ROC & Momentum
        df["roc_10"] = df["close"].pct_change(10) * 100
        df["momentum_10"] = df["close"] - df["close"].shift(10)

        # Volatility: ATR & Historical Volatility (20d)
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14, min_periods=1).mean()
        df["volatility_20d"] = df["return_1d"].rolling(window=20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        sma20 = df["sma_20"]
        std20 = df["close"].rolling(20, min_periods=1).std()
        df["bollinger_upper"] = sma20 + (2.0 * std20)
        df["bollinger_lower"] = sma20 - (2.0 * std20)
        df["bollinger_width"] = (df["bollinger_upper"] - df["bollinger_lower"]) / sma20.replace(0, 1e-9)

        # Volume Indicators
        df["volume_sma_20"] = df["volume"].rolling(20, min_periods=1).mean()
        df["relative_volume"] = df["volume"] / df["volume_sma_20"].replace(0, 1e-9)
        df["volume_change"] = df["volume"].pct_change()

        # On Balance Volume (OBV)
        obv_change = np.where(df["close"] > df["close"].shift(1), df["volume"],
                     np.where(df["close"] < df["close"].shift(1), -df["volume"], 0))
        df["obv"] = np.cumsum(np.nan_to_num(obv_change))

        # Accumulation/Distribution Line
        mfv = np.where((df["high"] - df["low"]) == 0, 0,
                       ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]))
        df["acc_dist"] = np.cumsum(mfv * df["volume"])

        # Price structure & Distances
        df["gap_pct"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1).replace(0, 1e-9)
        df["intraday_range"] = (df["high"] - df["low"]) / df["open"].replace(0, 1e-9)

        rolling_52w_high = df["high"].rolling(252, min_periods=1).max()
        rolling_52w_low = df["low"].rolling(252, min_periods=1).min()

        df["dist_52w_high"] = (df["close"] - rolling_52w_high) / rolling_52w_high.replace(0, 1e-9)
        df["dist_52w_low"] = (df["close"] - rolling_52w_low) / rolling_52w_low.replace(0, 1e-9)

        df["dist_sma_20"] = (df["close"] - df["sma_20"]) / df["sma_20"].replace(0, 1e-9)
        df["dist_sma_50"] = (df["close"] - df["sma_50"]) / df["sma_50"].replace(0, 1e-9)
        df["dist_sma_200"] = (df["close"] - df["sma_200"]) / df["sma_200"].replace(0, 1e-9)

        return df

    @staticmethod
    def detect_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """Detects latest pattern signals like Golden Cross, Breakouts, etc."""
        if df.empty or len(df) < 2:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        golden_cross = bool(prev["sma_50"] < prev["sma_200"] and latest["sma_50"] >= latest["sma_200"])
        death_cross = bool(prev["sma_50"] > prev["sma_200"] and latest["sma_50"] <= latest["sma_200"])

        lookback_20 = df.iloc[-21:-1] if len(df) >= 21 else df.iloc[:-1]
        high_20 = lookback_20["high"].max() if not lookback_20.empty else latest["high"]
        low_20 = lookback_20["low"].min() if not lookback_20.empty else latest["low"]

        breakout = bool(latest["close"] > high_20)
        breakdown = bool(latest["close"] < low_20)

        unusual_volume = bool(latest["relative_volume"] > 2.0)

        return {
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "breakout": breakout,
            "breakdown": breakdown,
            "unusual_volume": unusual_volume,
            "support_level": float(low_20),
            "resistance_level": float(high_20)
        }
