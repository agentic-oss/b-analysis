import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple


class TechnicalIndicators:
    """
    Calculates deterministic technical indicators and price structure parameters.
    """

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 5:
            return df

        res = df.copy()

        # Sort chronologically by date
        if "Date" in res.columns:
            res["Date"] = pd.to_datetime(res["Date"])
            res = res.sort_values("Date").reset_index(drop=True)
            res["Date"] = res["Date"].dt.strftime("%Y-%m-%d")

        close = res["close"]
        high = res["high"]
        low = res["low"]
        open_p = res["open"]
        volume = res["volume"]

        # 1. Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            res[f"sma_{p}"] = close.rolling(p, min_periods=1).mean()

        for p in [9, 20, 50, 200]:
            res[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()

        # 2. Momentum
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
        rs = gain / (loss.replace(0, 1e-9))
        res["rsi_14"] = 100 - (100 / (1 + rs))

        # Stochastic RSI
        rsi_min = res["rsi_14"].rolling(14, min_periods=1).min()
        rsi_max = res["rsi_14"].rolling(14, min_periods=1).max()
        rsi_range = (rsi_max - rsi_min).replace(0, 1e-9)
        res["stoch_rsi"] = (res["rsi_14"] - rsi_min) / rsi_range

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        res["macd"] = ema12 - ema26
        res["macd_signal"] = res["macd"].ewm(span=9, adjust=False).mean()
        res["macd_hist"] = res["macd"] - res["macd_signal"]

        # ROC & Momentum
        res["roc_12"] = close.pct_change(12) * 100
        res["momentum_10"] = close - close.shift(10)

        # 3. Volatility
        # ATR 14
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["atr_14"] = tr.rolling(14, min_periods=1).mean()

        # Historical Volatility 20d (annualized)
        log_ret = np.log(close / close.shift(1))
        res["volatility_20d"] = log_ret.rolling(20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        bb_middle = res["sma_20"]
        bb_std = close.rolling(20, min_periods=1).std()
        res["bollinger_upper"] = bb_middle + (bb_std * 2)
        res["bollinger_lower"] = bb_middle - (bb_std * 2)
        bb_range = (res["bollinger_upper"] - res["bollinger_lower"]).replace(0, 1e-9)
        res["bollinger_width"] = bb_range / bb_middle

        # Volatility Regime
        vol_mean = res["volatility_20d"].rolling(60, min_periods=1).mean()
        res["volatility_regime"] = np.where(res["volatility_20d"] > vol_mean * 1.25, "High",
                                   np.where(res["volatility_20d"] < vol_mean * 0.75, "Low", "Normal"))

        # 4. Volume Indicators
        res["volume_sma_20"] = volume.rolling(20, min_periods=1).mean()
        res["relative_volume"] = volume / res["volume_sma_20"].replace(0, 1e-9)
        res["volume_change"] = volume.pct_change()

        # OBV
        obv_direction = np.sign(close.diff()).fillna(0)
        res["obv"] = (obv_direction * volume).cumsum()

        # Accumulation / Distribution
        clv = (((close - low) - (high - close)) / (high - low).replace(0, 1e-9))
        res["acc_dist"] = (clv * volume).fillna(0).cumsum()

        # 5. Price Structure
        res["return_1d"] = close.pct_change()
        res["return_5d"] = close.pct_change(5)
        res["return_20d"] = close.pct_change(20)

        res["gap_pct"] = (open_p - close.shift(1)) / close.shift(1)
        res["intraday_range_pct"] = (high - low) / open_p

        res["dist_sma_20"] = (close - res["sma_20"]) / res["sma_20"]
        res["dist_sma_50"] = (close - res["sma_50"]) / res["sma_50"]
        res["dist_sma_200"] = (close - res["sma_200"]) / res["sma_200"]

        # 52-Week High / Low Distance
        w52_high = high.rolling(252, min_periods=1).max()
        w52_low = low.rolling(252, min_periods=1).min()
        res["dist_52w_high"] = (close - w52_high) / w52_high
        res["dist_52w_low"] = (close - w52_low) / w52_low

        # Signals / Technical Events
        res["golden_cross"] = (res["sma_50"] > res["sma_200"]) & (res["sma_50"].shift(1) <= res["sma_200"].shift(1))
        res["death_cross"] = (res["sma_50"] < res["sma_200"]) & (res["sma_50"].shift(1) >= res["sma_200"].shift(1))

        # Breakouts / Breakdowns (20-day high/low)
        high_20 = high.shift(1).rolling(20, min_periods=1).max()
        low_20 = low.shift(1).rolling(20, min_periods=1).min()
        res["breakout_20d"] = close > high_20
        res["breakdown_20d"] = close < low_20

        # Support & Resistance levels (Pivot points / 20-day high-low)
        res["support_20d"] = low_20
        res["resistance_20d"] = high_20

        return res
