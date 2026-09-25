"""Deterministic Technical Indicator Calculations."""

import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculates comprehensive technical analysis indicators for OHLCV data."""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators on given OHLCV DataFrame."""
        if df.empty or len(df) < 2:
            return df

        df = df.copy().sort_values("Date").reset_index(drop=True)

        # Ensure numeric columns
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df.get("Volume", pd.Series(np.nan, index=df.index))

        # --- 1. Daily Return & Gaps ---
        df["return_1d"] = close.pct_change()
        df["prev_close"] = close.shift(1)
        df["gap_pct"] = ((df["Open"] - df["prev_close"]) / df["prev_close"]) * 100.0
        df["intraday_range_pct"] = ((high - low) / low) * 100.0

        # --- 2. Trend Moving Averages ---
        for period in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{period}"] = close.rolling(window=period, min_periods=1).mean()
            df[f"dist_sma_{period}_pct"] = ((close - df[f"sma_{period}"]) / df[f"sma_{period}"]) * 100.0

        for period in [9, 20, 50, 200]:
            df[f"ema_{period}"] = close.ewm(span=period, adjust=False, min_periods=1).mean()
            df[f"dist_ema_{period}_pct"] = ((close - df[f"ema_{period}"]) / df[f"ema_{period}"]) * 100.0

        # --- 3. Momentum Indicators ---
        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False, min_periods=1).mean()
        avg_loss = loss.ewm(com=13, adjust=False, min_periods=1).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
        df["rsi_14"] = df["rsi_14"].fillna(50.0)

        # Stochastic RSI 14
        rsi = df["rsi_14"]
        min_rsi = rsi.rolling(window=14, min_periods=1).min()
        max_rsi = rsi.rolling(window=14, min_periods=1).max()
        rsi_range = (max_rsi - min_rsi).replace(0, np.nan)
        df["stoch_rsi"] = ((rsi - min_rsi) / rsi_range) * 100.0
        df["stoch_rsi"] = df["stoch_rsi"].fillna(50.0)

        # MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False, min_periods=1).mean()
        ema_26 = close.ewm(span=26, adjust=False, min_periods=1).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False, min_periods=1).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ROC & Momentum
        df["roc_10"] = close.pct_change(periods=10) * 100.0
        df["momentum_10"] = close - close.shift(10)

        # --- 4. Volatility Indicators ---
        # ATR 14
        prev_close_series = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close_series).abs()
        tr3 = (low - prev_close_series).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.ewm(span=14, adjust=False, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(close / close.shift(1))
        df["volatility_20d"] = log_ret.rolling(window=20, min_periods=2).std() * np.sqrt(252) * 100.0
        df["volatility_20d"] = df["volatility_20d"].fillna(0.0)

        # Bollinger Bands (20, 2 std)
        bb_sma = df["sma_20"]
        bb_std = close.rolling(window=20, min_periods=1).std()
        df["bb_upper"] = bb_sma + (bb_std * 2.0)
        df["bb_lower"] = bb_sma - (bb_std * 2.0)
        df["bb_width"] = ((df["bb_upper"] - df["bb_lower"]) / bb_sma) * 100.0

        # Volatility Regime
        vol_median = df["volatility_20d"].rolling(window=252, min_periods=20).median()
        df["volatility_regime"] = "Normal"
        df.loc[df["volatility_20d"] > 1.3 * vol_median, "volatility_regime"] = "High"
        df.loc[df["volatility_20d"] < 0.7 * vol_median, "volatility_regime"] = "Low"

        # --- 5. Volume Indicators ---
        df["volume_sma_20"] = volume.rolling(window=20, min_periods=1).mean()
        df["relative_volume"] = volume / df["volume_sma_20"].replace(0, np.nan)
        df["relative_volume"] = df["relative_volume"].fillna(1.0)
        df["volume_change"] = volume.pct_change()

        # OBV (On-Balance Volume)
        price_diff = close.diff()
        direction = np.where(price_diff > 0, 1, np.where(price_diff < 0, -1, 0))
        df["obv"] = (direction * volume.fillna(0)).cumsum()

        # Accumulation / Distribution (A/D)
        hl_diff = (high - low).replace(0, np.nan)
        clv = ((close - low) - (high - close)) / hl_diff
        clv = clv.fillna(0)
        df["ad_line"] = (clv * volume.fillna(0)).cumsum()

        # --- 6. 52-Week High/Low & Price Structure ---
        df["high_52w"] = high.rolling(window=252, min_periods=1).max()
        df["low_52w"] = low.rolling(window=252, min_periods=1).min()
        df["dist_52w_high_pct"] = ((close - df["high_52w"]) / df["high_52w"]) * 100.0
        df["dist_52w_low_pct"] = ((close - df["low_52w"]) / df["low_52w"]) * 100.0

        # Support & Resistance (rolling 20-day min/max)
        df["support_20d"] = low.rolling(window=20, min_periods=1).min()
        df["resistance_20d"] = high.rolling(window=20, min_periods=1).max()

        # --- 7. Technical Signal Detection ---
        # Golden Cross & Death Cross (SMA 50 vs SMA 200)
        sma50_prev = df["sma_50"].shift(1)
        sma200_prev = df["sma_200"].shift(1)
        df["golden_cross"] = (sma50_prev <= sma200_prev) & (df["sma_50"] > df["sma_200"])
        df["death_cross"] = (sma50_prev >= sma200_prev) & (df["sma_50"] < df["sma_200"])

        # Breakouts & Breakdowns
        prev_res = df["resistance_20d"].shift(1)
        prev_sup = df["support_20d"].shift(1)
        df["breakout"] = close > prev_res
        df["breakdown"] = close < prev_sup

        # Unusual Volume
        df["unusual_volume"] = df["relative_volume"] >= 2.0

        return df

    @staticmethod
    def get_latest_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Extract latest technical analysis summary dictionary from calculated DataFrame."""
        if df.empty:
            return {}

        latest = df.iloc[-1]
        return {
            "date": str(pd.to_datetime(latest["Date"]).date()),
            "close": float(latest["Close"]),
            "return_1d": float(latest.get("return_1d", 0.0)),
            "sma_20": float(latest.get("sma_20", 0.0)),
            "sma_50": float(latest.get("sma_50", 0.0)),
            "sma_200": float(latest.get("sma_200", 0.0)),
            "ema_20": float(latest.get("ema_20", 0.0)),
            "rsi_14": float(latest.get("rsi_14", 50.0)),
            "stoch_rsi": float(latest.get("stoch_rsi", 50.0)),
            "macd": float(latest.get("macd", 0.0)),
            "macd_signal": float(latest.get("macd_signal", 0.0)),
            "macd_hist": float(latest.get("macd_hist", 0.0)),
            "atr_14": float(latest.get("atr_14", 0.0)),
            "volatility_20d": float(latest.get("volatility_20d", 0.0)),
            "relative_volume": float(latest.get("relative_volume", 1.0)),
            "dist_52w_high_pct": float(latest.get("dist_52w_high_pct", 0.0)),
            "dist_52w_low_pct": float(latest.get("dist_52w_low_pct", 0.0)),
            "golden_cross": bool(latest.get("golden_cross", False)),
            "death_cross": bool(latest.get("death_cross", False)),
            "breakout": bool(latest.get("breakout", False)),
            "breakdown": bool(latest.get("breakdown", False)),
            "unusual_volume": bool(latest.get("unusual_volume", False))
        }
