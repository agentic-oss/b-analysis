"""
Technical indicator calculation engine and pattern recognition detector.
Calculates Trend, Momentum, Volatility, Volume, and Price Structure indicators deterministically.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class TechnicalIndicators:
    """
    Computes technical indicators and technical patterns for OHLCV dataframes.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sma_periods = [5, 10, 20, 50, 100, 200]
        self.ema_periods = [9, 20, 50, 200]
        self.rsi_period = 14
        self.stoch_rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.atr_period = 14
        self.bb_period = 20
        self.bb_std = 2.0
        self.vol_sma_period = 20

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all technical indicators on input DataFrame containing ['Open', 'High', 'Low', 'Close', 'Volume'].
        Returns enriched DataFrame.
        """
        if df is None or df.empty or len(df) < 5:
            return df

        res = df.copy()

        # Ensure numeric types
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in res.columns:
                res[col] = pd.to_numeric(res[col], errors="coerce")

        close = res["Close"]
        high = res["High"]
        low = res["Low"]
        open_p = res["Open"]
        volume = res["Volume"]

        # 1. Trend - SMAs
        for p in self.sma_periods:
            res[f"SMA_{p}"] = close.rolling(p).mean()

        # Trend - EMAs
        for p in self.ema_periods:
            res[f"EMA_{p}"] = close.ewm(span=p, adjust=False).mean()

        # 2. Momentum - RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss.replace(0, np.nan))
        res["RSI_14"] = 100 - (100 / (1 + rs))
        res["RSI_14"] = res["RSI_14"].fillna(50.0)

        # Stochastic RSI
        rsi = res["RSI_14"]
        rsi_min = rsi.rolling(self.stoch_rsi_period).min()
        rsi_max = rsi.rolling(self.stoch_rsi_period).max()
        rsi_range = rsi_max - rsi_min
        res["Stoch_RSI"] = np.where(rsi_range > 0, (rsi - rsi_min) / rsi_range, 0.5)

        # MACD
        ema_fast = close.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.macd_slow, adjust=False).mean()
        res["MACD"] = ema_fast - ema_slow
        res["MACD_Signal"] = res["MACD"].ewm(span=self.macd_signal, adjust=False).mean()
        res["MACD_Hist"] = res["MACD"] - res["MACD_Signal"]

        # ROC & Momentum
        res["ROC_10"] = close.pct_change(10) * 100
        res["Momentum_10"] = close - close.shift(10)

        # 3. Volatility - ATR
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["ATR_14"] = tr.rolling(self.atr_period).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(close / close.shift(1))
        res["Volatility_20d"] = log_ret.rolling(20).std() * np.sqrt(252)

        # Bollinger Bands
        bb_mid = close.rolling(self.bb_period).mean()
        bb_std_val = close.rolling(self.bb_period).std()
        res["BB_Middle"] = bb_mid
        res["BB_Upper"] = bb_mid + (self.bb_std * bb_std_val)
        res["BB_Lower"] = bb_mid - (self.bb_std * bb_std_val)
        bb_denom = res["BB_Middle"].replace(0, np.nan)
        res["BB_Width"] = (res["BB_Upper"] - res["BB_Lower"]) / bb_denom

        # Volatility Regime
        vol_median = res["Volatility_20d"].rolling(100, min_periods=20).median()
        res["Volatility_Regime"] = np.where(
            res["Volatility_20d"] > vol_median * 1.3, "High",
            np.where(res["Volatility_20d"] < vol_median * 0.7, "Low", "Normal")
        )

        # 4. Volume Indicators
        res["Volume_SMA_20"] = volume.rolling(self.vol_sma_period).mean()
        vol_sma_denom = res["Volume_SMA_20"].replace(0, np.nan)
        res["Relative_Volume"] = volume / vol_sma_denom
        res["Volume_Change"] = volume.pct_change()

        # On Balance Volume (OBV)
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        res["OBV"] = obv

        # Accumulation / Distribution (A/D)
        clv_num = (close - low) - (high - close)
        clv_den = (high - low).replace(0, np.nan)
        clv = (clv_num / clv_den).fillna(0)
        res["Accum_Dist"] = (clv * volume).cumsum()

        # 5. Price Structure & Returns
        res["Daily_Return"] = close.pct_change()
        res["Return_5d"] = close.pct_change(5)
        res["Return_20d"] = close.pct_change(20)

        # Gap %
        prev_close = close.shift(1)
        res["Gap_Pct"] = np.where(prev_close > 0, (open_p - prev_close) / prev_close * 100, 0.0)

        # Intraday Range
        res["Intraday_Range_Pct"] = np.where(low > 0, (high - low) / low * 100, 0.0)

        # Distance from Moving Averages (%)
        for ma in ["SMA_20", "SMA_50", "SMA_200"]:
            if ma in res.columns:
                ma_val = res[ma].replace(0, np.nan)
                res[f"Dist_From_{ma}"] = (close - ma_val) / ma_val * 100

        # 52-Week High & Low Distances
        high_52w = high.rolling(252, min_periods=20).max()
        low_52w = low.rolling(252, min_periods=20).min()
        res["High_52W"] = high_52w
        res["Low_52W"] = low_52w
        res["Dist_From_52W_High"] = np.where(high_52w > 0, (close - high_52w) / high_52w * 100, 0.0)
        res["Dist_From_52W_Low"] = np.where(low_52w > 0, (close - low_52w) / low_52w * 100, 0.0)

        return res

    def detect_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects actionable technical patterns and events from the latest row of calculated indicators.
        """
        if df is None or df.empty or len(df) < 5:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        signals = []
        events = []

        # Golden Cross & Death Cross
        if "SMA_50" in df.columns and "SMA_200" in df.columns:
            if prev["SMA_50"] <= prev["SMA_200"] and latest["SMA_50"] > latest["SMA_200"]:
                events.append("Golden Cross (50 DMA crossed above 200 DMA)")
                signals.append("GOLDEN_CROSS")
            elif prev["SMA_50"] >= prev["SMA_200"] and latest["SMA_50"] < latest["SMA_200"]:
                events.append("Death Cross (50 DMA crossed below 200 DMA)")
                signals.append("DEATH_CROSS")

        # Breakouts / Breakdowns
        if "BB_Upper" in df.columns and latest["Close"] > latest["BB_Upper"]:
            events.append("Bollinger Upper Band Breakout")
            signals.append("BOLLINGER_BREAKOUT")
        elif "BB_Lower" in df.columns and latest["Close"] < latest["BB_Lower"]:
            events.append("Bollinger Lower Band Breakdown")
            signals.append("BOLLINGER_BREAKDOWN")

        # Unusual Volume
        if "Relative_Volume" in df.columns and latest["Relative_Volume"] >= 2.5:
            events.append(f"Unusual Volume ({latest['Relative_Volume']:.1f}x 20-day SMA)")
            signals.append("UNUSUAL_VOLUME")

        # Support & Resistance levels (20-day high/low)
        high_20d = df["High"].tail(20).max()
        low_20d = df["Low"].tail(20).min()

        # Trend change detection
        trend_status = "Neutral"
        if latest["Close"] > latest.get("SMA_20", latest["Close"]) > latest.get("SMA_50", latest["Close"]):
            trend_status = "Bullish Alignment"
        elif latest["Close"] < latest.get("SMA_20", latest["Close"]) < latest.get("SMA_50", latest["Close"]):
            trend_status = "Bearish Alignment"

        return {
            "signals": signals,
            "events": events,
            "support_level": float(low_20d),
            "resistance_level": float(high_20d),
            "trend_alignment": trend_status,
            "rsi_14": float(latest.get("RSI_14", 50.0)),
            "macd_hist": float(latest.get("MACD_Hist", 0.0)),
            "relative_volume": float(latest.get("Relative_Volume", 1.0)),
            "dist_52w_high": float(latest.get("Dist_From_52W_High", 0.0)),
            "dist_52w_low": float(latest.get("Dist_From_52W_Low", 0.0)),
        }
