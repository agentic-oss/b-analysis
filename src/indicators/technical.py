import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculates comprehensive deterministic technical indicators and detects price events."""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates trend, momentum, volatility, volume, and price structure indicators.
        Input DataFrame must be sorted by date ascending and contain ['open', 'high', 'low', 'close', 'volume'].
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy()

        # Ensure numeric types
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]
        open_p = df["open"]

        # 1. Daily Returns & Intraday Range
        df["return_1d"] = close.pct_change(1)
        df["return_5d"] = close.pct_change(5)
        df["return_20d"] = close.pct_change(20)
        df["gap_pct"] = (open_p - close.shift(1)) / close.shift(1)
        df["intraday_range"] = (high - low) / open_p

        # 2. Trend Moving Averages
        smas = [5, 10, 20, 50, 100, 200]
        for p in smas:
            df[f"sma_{p}"] = close.rolling(window=p, min_periods=1).mean()
            df[f"dist_sma_{p}"] = (close - df[f"sma_{p}"]) / df[f"sma_{p}"]

        emas = [9, 20, 50, 200]
        for p in emas:
            df[f"ema_{p}"] = close.ewm(span=p, adjust=False, min_periods=1).mean()
            df[f"dist_ema_{p}"] = (close - df[f"ema_{p}"]) / df[f"ema_{p}"]

        # 3. Momentum Indicators
        # RSI 14
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(com=13, adjust=False, min_periods=1).mean()
        avg_loss = loss.ewm(com=13, adjust=False, min_periods=1).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
        df["rsi_14"] = df["rsi_14"].fillna(50.0)

        # Stochastic RSI
        rsi_min = df["rsi_14"].rolling(14, min_periods=1).min()
        rsi_max = df["rsi_14"].rolling(14, min_periods=1).max()
        stoch_rsi = (df["rsi_14"] - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
        df["stoch_rsi_k"] = stoch_rsi.rolling(3, min_periods=1).mean() * 100.0
        df["stoch_rsi_d"] = df["stoch_rsi_k"].rolling(3, min_periods=1).mean()

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False, min_periods=1).mean()
        ema26 = close.ewm(span=26, adjust=False, min_periods=1).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False, min_periods=1).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ROC & Momentum
        df["roc_10"] = close.pct_change(10) * 100.0
        df["momentum_10"] = close - close.shift(10)

        # 4. Volatility Indicators
        # ATR 14
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.ewm(com=13, adjust=False, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(close / close.shift(1))
        df["volatility_20d"] = log_ret.rolling(20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        bb_middle = df["sma_20"]
        bb_std = close.rolling(20, min_periods=1).std()
        df["bb_upper"] = bb_middle + (bb_std * 2)
        df["bb_lower"] = bb_middle - (bb_std * 2)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / bb_middle.replace(0, np.nan)

        # Volatility Regime
        vol_mean = df["volatility_20d"].rolling(252, min_periods=1).mean()
        df["volatility_regime"] = np.where(df["volatility_20d"] > vol_mean * 1.25, "High",
                                  np.where(df["volatility_20d"] < vol_mean * 0.75, "Low", "Normal"))

        # 5. Volume Indicators
        df["volume_sma_20"] = volume.rolling(20, min_periods=1).mean()
        df["relative_volume"] = volume / df["volume_sma_20"].replace(0, np.nan)
        df["volume_change"] = volume.pct_change(1)

        # On-Balance Volume (OBV)
        obv = (np.sign(close.diff().fillna(0)) * volume).cumsum()
        df["obv"] = obv

        # Accumulation / Distribution (A/D)
        mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
        mfm = mfm.fillna(0)
        mfv = mfm * volume
        df["accumulation_distribution"] = mfv.cumsum()

        # 6. Price Structure & 52-Week High / Low
        high_52w = high.rolling(252, min_periods=1).max()
        low_52w = low.rolling(252, min_periods=1).min()
        df["dist_52w_high"] = (close - high_52w) / high_52w
        df["dist_52w_low"] = (close - low_52w) / low_52w

        # 7. Events (Golden Cross, Death Cross, Unusual Volume, Breakouts)
        df["golden_cross"] = (df["sma_50"] > df["sma_200"]) & (df["sma_50"].shift(1) <= df["sma_200"].shift(1))
        df["death_cross"] = (df["sma_50"] < df["sma_200"]) & (df["sma_50"].shift(1) >= df["sma_200"].shift(1))
        df["unusual_volume"] = df["relative_volume"] >= 2.0

        # Support & Resistance (20-day high/low)
        df["resistance_20d"] = high.rolling(20, min_periods=1).max().shift(1)
        df["support_20d"] = low.rolling(20, min_periods=1).min().shift(1)
        df["breakout"] = close > df["resistance_20d"]
        df["breakdown"] = close < df["support_20d"]

        return df

    @staticmethod
    def get_latest_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """Extracts key signals and metrics from the most recent row."""
        if df.empty:
            return {}

        latest = df.iloc[-1].to_dict()

        events = []
        if latest.get("golden_cross"):
            events.append("Golden Cross (50 DMA crossed above 200 DMA)")
        if latest.get("death_cross"):
            events.append("Death Cross (50 DMA crossed below 200 DMA)")
        if latest.get("breakout"):
            events.append("20-Day High Breakout")
        if latest.get("breakdown"):
            events.append("20-Day Low Breakdown")
        if latest.get("unusual_volume"):
            events.append(f"Unusual Volume ({latest.get('relative_volume', 0):.2f}x 20-DMA)")

        return {
            "date": latest.get("date"),
            "close": latest.get("close"),
            "return_1d": latest.get("return_1d"),
            "rsi_14": latest.get("rsi_14"),
            "macd": latest.get("macd"),
            "macd_signal": latest.get("macd_signal"),
            "macd_hist": latest.get("macd_hist"),
            "atr_14": latest.get("atr_14"),
            "volatility_20d": latest.get("volatility_20d"),
            "volatility_regime": latest.get("volatility_regime"),
            "relative_volume": latest.get("relative_volume"),
            "dist_sma_20": latest.get("dist_sma_20"),
            "dist_sma_50": latest.get("dist_sma_50"),
            "dist_sma_200": latest.get("dist_sma_200"),
            "dist_52w_high": latest.get("dist_52w_high"),
            "dist_52w_low": latest.get("dist_52w_low"),
            "events": events
        }
