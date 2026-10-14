import numpy as np
import pandas as pd
from typing import Dict, Any, List

class TechnicalIndicators:
    """Computes deterministic technical indicators and price patterns."""

    @staticmethod
    def compute_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes trend, momentum, volatility, volume, and structural price indicators on df.
        Requires columns: Date, open, high, low, close, volume.
        Returns modified DataFrame with indicator columns added.
        """
        if df.empty or len(df) < 5:
            return df

        res = df.copy().sort_values("Date").reset_index(drop=True)

        # 1. Trend Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            res[f"sma_{p}"] = res["close"].rolling(window=p, min_periods=1).mean()
        for p in [9, 20, 50, 200]:
            res[f"ema_{p}"] = res["close"].ewm(span=p, adjust=False).mean()

        # 2. Daily Returns & Price Structure
        res["return_1d"] = res["close"].pct_change()
        res["return_5d"] = res["close"].pct_change(5)
        res["return_20d"] = res["close"].pct_change(20)
        res["gap_pct"] = (res["open"] - res["close"].shift(1)) / res["close"].shift(1)
        res["intraday_range"] = (res["high"] - res["low"]) / res["open"]

        # Distances from Moving Averages
        res["dist_sma_20"] = (res["close"] - res["sma_20"]) / res["sma_20"]
        res["dist_sma_50"] = (res["close"] - res["sma_50"]) / res["sma_50"]
        res["dist_sma_200"] = (res["close"] - res["sma_200"]) / res["sma_200"]

        # 52-Week High/Low Distance (252 trading days)
        rolling_52w_high = res["high"].rolling(window=252, min_periods=20).max()
        rolling_52w_low = res["low"].rolling(window=252, min_periods=20).min()
        res["dist_52w_high"] = (res["close"] - rolling_52w_high) / rolling_52w_high
        res["dist_52w_low"] = (res["close"] - rolling_52w_low) / rolling_52w_low

        # 3. Momentum
        # RSI 14
        delta = res["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss.replace(0, 1e-9))
        res["rsi_14"] = 100 - (100 / (1 + rs))

        # Stochastic RSI
        min_rsi = res["rsi_14"].rolling(window=14, min_periods=1).min()
        max_rsi = res["rsi_14"].rolling(window=14, min_periods=1).max()
        res["stoch_rsi"] = (res["rsi_14"] - min_rsi) / (max_rsi - min_rsi + 1e-9)

        # MACD (12, 26, 9)
        ema_12 = res["close"].ewm(span=12, adjust=False).mean()
        ema_26 = res["close"].ewm(span=26, adjust=False).mean()
        res["macd"] = ema_12 - ema_26
        res["macd_signal"] = res["macd"].ewm(span=9, adjust=False).mean()
        res["macd_hist"] = res["macd"] - res["macd_signal"]

        # ROC & Momentum
        res["roc_10"] = ((res["close"] - res["close"].shift(10)) / res["close"].shift(10)) * 100
        res["momentum_10"] = res["close"] - res["close"].shift(10)

        # 4. Volatility
        # ATR 14
        prev_close = res["close"].shift(1)
        tr1 = res["high"] - res["low"]
        tr2 = (res["high"] - prev_close).abs()
        tr3 = (res["low"] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["atr_14"] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized std dev of daily returns)
        res["volatility_20d"] = res["return_1d"].rolling(window=20, min_periods=5).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        bb_std = res["close"].rolling(window=20, min_periods=1).std()
        res["bollinger_upper"] = res["sma_20"] + (bb_std * 2)
        res["bollinger_lower"] = res["sma_20"] - (bb_std * 2)
        res["bollinger_bandwidth"] = (res["bollinger_upper"] - res["bollinger_lower"]) / res["sma_20"]

        # 5. Volume Indicators
        res["volume_sma_20"] = res["volume"].rolling(window=20, min_periods=1).mean()
        res["relative_volume"] = res["volume"] / (res["volume_sma_20"] + 1e-9)
        res["volume_change"] = res["volume"].pct_change()

        # On-Balance Volume (OBV)
        obv = [0]
        close_vals = res["close"].values
        vol_vals = res["volume"].values
        for i in range(1, len(res)):
            if close_vals[i] > close_vals[i-1]:
                obv.append(obv[-1] + vol_vals[i])
            elif close_vals[i] < close_vals[i-1]:
                obv.append(obv[-1] - vol_vals[i])
            else:
                obv.append(obv[-1])
        res["obv"] = obv

        # Accumulation/Distribution
        mfm = ((res["close"] - res["low"]) - (res["high"] - res["close"])) / (res["high"] - res["low"] + 1e-9)
        mfv = mfm * res["volume"]
        res["ad_line"] = mfv.cumsum()

        # 6. Technical Events
        res["golden_cross"] = (res["sma_50"] > res["sma_200"]) & (res["sma_50"].shift(1) <= res["sma_200"].shift(1))
        res["death_cross"] = (res["sma_50"] < res["sma_200"]) & (res["sma_50"].shift(1) >= res["sma_200"].shift(1))
        res["unusual_volume"] = res["relative_volume"] >= 2.0

        # Breakout / Breakdown (20-day high/low)
        rolling_20_high = res["high"].shift(1).rolling(window=20, min_periods=5).max()
        rolling_20_low = res["low"].shift(1).rolling(window=20, min_periods=5).min()
        res["breakout_20d"] = res["close"] > rolling_20_high
        res["breakdown_20d"] = res["close"] < rolling_20_low

        return res
