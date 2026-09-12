import numpy as np
import pandas as pd
from typing import Dict, Any, List

class TechnicalIndicators:
    """Calculates deterministic technical indicators on stock price DataFrames."""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Expects df to be sorted by date ascending for a single ticker.
        Columns: date, open, high, low, close, volume, (optional: adj_close)
        Returns df with appended technical indicator columns.
        """
        if df.empty or len(df) == 0:
            return df

        df = df.copy()

        # Ensure numerical types
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # 1. Trend Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{p}"] = close.rolling(window=p, min_periods=1).mean()

        for p in [9, 20, 50, 200]:
            df[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()

        # 2. Momentum
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["rsi_14"] = df["rsi_14"].fillna(50.0)

        # Stochastic RSI
        rsi = df["rsi_14"]
        rsi_min = rsi.rolling(window=14, min_periods=1).min()
        rsi_max = rsi.rolling(window=14, min_periods=1).max()
        stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
        df["stoch_rsi"] = stoch_rsi.fillna(0.5)

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ROC (Rate of Change 12) & Momentum (10)
        df["roc_12"] = close.pct_change(periods=12) * 100
        df["momentum_10"] = close - close.shift(10)

        # 3. Volatility
        # ATR 14
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized std of returns)
        log_ret = np.log(close / close.shift(1))
        df["volatility_20d"] = log_ret.rolling(window=20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2.0)
        sma20 = df["sma_20"]
        std20 = close.rolling(window=20, min_periods=1).std()
        df["bollinger_upper"] = sma20 + (std20 * 2.0)
        df["bollinger_lower"] = sma20 - (std20 * 2.0)
        df["bollinger_bandwidth"] = (df["bollinger_upper"] - df["bollinger_lower"]) / sma20.replace(0, np.nan)

        # Volatility Regime
        vol_mean = df["volatility_20d"].rolling(window=100, min_periods=1).mean()
        df["volatility_regime"] = np.where(df["volatility_20d"] > vol_mean * 1.25, "High",
                                  np.where(df["volatility_20d"] < vol_mean * 0.75, "Low", "Normal"))

        # 4. Volume Indicators
        df["volume_sma_20"] = volume.rolling(window=20, min_periods=1).mean()
        df["relative_volume"] = volume / df["volume_sma_20"].replace(0, np.nan)
        df["volume_change"] = volume.pct_change()

        # OBV (On-Balance Volume)
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        df["obv"] = obv

        # Accumulation / Distribution (A/D)
        mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
        mfm = mfm.fillna(0)
        mfv = mfm * volume
        df["accumulation_distribution"] = mfv.cumsum()

        # 5. Price Structure
        df["daily_return"] = close.pct_change()
        df["gap_pct"] = (df["open"] - close.shift(1)) / close.shift(1).replace(0, np.nan)
        df["intraday_range_pct"] = (high - low) / low.replace(0, np.nan)

        # Distances from Moving Averages
        df["dist_sma_20"] = (close - df["sma_20"]) / df["sma_20"].replace(0, np.nan)
        df["dist_sma_50"] = (close - df["sma_50"]) / df["sma_50"].replace(0, np.nan)
        df["dist_sma_200"] = (close - df["sma_200"]) / df["sma_200"].replace(0, np.nan)

        # 52-week High / Low distance (approx 252 trading days)
        high_252 = high.rolling(window=252, min_periods=1).max()
        low_252 = low.rolling(window=252, min_periods=1).min()
        df["distance_52w_high"] = (close - high_252) / high_252.replace(0, np.nan)
        df["distance_52w_low"] = (close - low_252) / low_252.replace(0, np.nan)

        return df
