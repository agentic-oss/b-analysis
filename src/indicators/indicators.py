"""
Technical Indicators Calculation Engine.
Calculates trend, momentum, volatility, volume, price structure, and technical pattern events.
All calculations are deterministic and reproducible.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd


class TechnicalAnalysisEngine:
    """Computes technical indicators and identifies pattern signals on price DataFrames."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for time series DataFrame.
        Expected columns: ['date', 'open', 'high', 'low', 'close', 'volume']
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy()
        df = df.sort_values("date").reset_index(drop=True)

        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_p = df["open"]
        volume = df["volume"]

        # --- Daily Return & Gap % & Intraday Range ---
        df["daily_return"] = close.pct_change()
        df["prev_close"] = close.shift(1)
        df["gap_pct"] = np.where(df["prev_close"] > 0, ((open_p - df["prev_close"]) / df["prev_close"]) * 100, 0.0)
        df["intraday_range"] = np.where(close > 0, ((high - low) / close) * 100, 0.0)

        # --- Moving Averages (Trend) ---
        for period in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{period}"] = close.rolling(window=period, min_periods=1).mean()

        for period in [9, 20, 50, 200]:
            df[f"ema_{period}"] = close.ewm(span=period, adjust=False, min_periods=1).mean()

        # MA Distances (%)
        for period in [20, 50, 200]:
            df[f"dist_sma_{period}"] = ((close - df[f"sma_{period}"]) / df[f"sma_{period}"]) * 100

        # --- Momentum Indicators ---
        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["rsi_14"] = df["rsi_14"].fillna(50.0)

        # Stochastic RSI
        rsi = df["rsi_14"]
        rsi_min = rsi.rolling(window=14, min_periods=1).min()
        rsi_max = rsi.rolling(window=14, min_periods=1).max()
        stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
        df["stoch_rsi"] = stoch_rsi.fillna(0.5) * 100

        # MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False, min_periods=1).mean()
        ema_26 = close.ewm(span=26, adjust=False, min_periods=1).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False, min_periods=1).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ROC (10) & Momentum (10)
        df["roc_10"] = ((close - close.shift(10)) / close.shift(10).replace(0, np.nan)) * 100
        df["roc_10"] = df["roc_10"].fillna(0.0)
        df["momentum_10"] = close - close.shift(10)
        df["momentum_10"] = df["momentum_10"].fillna(0.0)

        # --- Volatility Indicators ---
        # ATR (14)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.ewm(alpha=1/14, min_periods=1, adjust=False).mean()

        # Historical Volatility (20-day annualized std dev of log returns)
        log_ret = np.log(close / close.shift(1))
        df["volatility_20d"] = log_ret.rolling(window=20, min_periods=1).std() * np.sqrt(252) * 100
        df["volatility_20d"] = df["volatility_20d"].fillna(0.0)

        # Bollinger Bands (20, 2)
        sma_20 = df["sma_20"]
        std_20 = close.rolling(window=20, min_periods=1).std().fillna(0.0)
        df["bb_upper"] = sma_20 + (2.0 * std_20)
        df["bb_lower"] = sma_20 - (2.0 * std_20)
        df["bb_width"] = np.where(sma_20 > 0, ((df["bb_upper"] - df["bb_lower"]) / sma_20) * 100, 0.0)

        # Volatility Regime
        vol_med = df["volatility_20d"].rolling(60, min_periods=10).median()
        df["volatility_regime"] = np.where(df["volatility_20d"] > vol_med * 1.2, "High",
                                  np.where(df["volatility_20d"] < vol_med * 0.8, "Low", "Normal"))

        # --- Volume Indicators ---
        df["volume_sma_20"] = volume.rolling(window=20, min_periods=1).mean()
        df["relative_volume"] = np.where(df["volume_sma_20"] > 0, volume / df["volume_sma_20"], 1.0)
        df["volume_change_pct"] = volume.pct_change().fillna(0.0) * 100

        # OBV
        direction = np.sign(close.diff().fillna(0))
        df["obv"] = (direction * volume).cumsum()

        # Accumulation / Distribution (A/D)
        mf_multiplier = np.where((high - low) > 0, ((close - low) - (high - close)) / (high - low), 0.0)
        mf_volume = mf_multiplier * volume
        df["ad_line"] = mf_volume.cumsum()

        # --- 52-Week High/Low Distances ---
        rolling_52w_high = high.rolling(window=252, min_periods=10).max()
        rolling_52w_low = low.rolling(window=252, min_periods=10).min()

        df["dist_52w_high"] = np.where(rolling_52w_high > 0, ((close - rolling_52w_high) / rolling_52w_high) * 100, 0.0)
        df["dist_52w_low"] = np.where(rolling_52w_low > 0, ((close - rolling_52w_low) / rolling_52w_low) * 100, 0.0)

        # Drop temporary helper column
        if "prev_close" in df.columns:
            df = df.drop(columns=["prev_close"])

        return df

    def extract_latest_events(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract pattern events, crosses, breakouts, support/resistance for the latest date in DataFrame."""
        if df.empty or len(df) < 5:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest

        # Golden / Death Cross (50 DMA crossing 200 DMA)
        golden_cross = (prev["sma_50"] <= prev["sma_200"]) and (latest["sma_50"] > latest["sma_200"])
        death_cross = (prev["sma_50"] >= prev["sma_200"]) and (latest["sma_50"] < latest["sma_200"])

        # Breakouts / Breakdowns (closing above 20-day high or below 20-day low)
        lookback_df = df.iloc[-21:-1] if len(df) >= 21 else df.iloc[:-1]
        high_20d = lookback_df["high"].max() if not lookback_df.empty else latest["high"]
        low_20d = lookback_df["low"].min() if not lookback_df.empty else latest["low"]

        breakout = latest["close"] > high_20d
        breakdown = latest["close"] < low_20d

        # Support and Resistance levels (pivot levels based on recent 20 days)
        pivot = (latest["high"] + latest["low"] + latest["close"]) / 3.0
        r1 = (2 * pivot) - latest["low"]
        s1 = (2 * pivot) - latest["high"]
        r2 = pivot + (latest["high"] - latest["low"])
        s2 = pivot - (latest["high"] - latest["low"])

        # Unusual Volume (> 2.0x 20-day average)
        unusual_volume = latest["relative_volume"] >= 2.0

        return {
            "date": latest["date"],
            "golden_cross": bool(golden_cross),
            "death_cross": bool(death_cross),
            "breakout_20d": bool(breakout),
            "breakdown_20d": bool(breakdown),
            "unusual_volume": bool(unusual_volume),
            "support_level_1": round(float(s1), 2),
            "support_level_2": round(float(s2), 2),
            "resistance_level_1": round(float(r1), 2),
            "resistance_level_2": round(float(r2), 2),
            "rsi_14": round(float(latest["rsi_14"]), 2),
            "macd_hist": round(float(latest["macd_hist"]), 4),
            "relative_volume": round(float(latest["relative_volume"]), 2),
            "volatility_regime": latest.get("volatility_regime", "Normal")
        }
