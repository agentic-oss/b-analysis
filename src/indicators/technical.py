"""
Technical Indicators computation engine.
Computes Trend, Momentum, Volatility, Volume, Price Structure, and Key Technical Events.
"""
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Deterministic technical analysis calculator.
    """

    @staticmethod
    def compute_all(df: pd.DataFrame, config: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Computes all technical indicators on a DataFrame containing OHLCV data.
        Returns DataFrame enriched with indicator columns.
        """
        if df.empty or len(df) < 5:
            return df

        res = df.copy()
        if "Date" in res.columns:
            res["Date"] = pd.to_datetime(res["Date"])
            res = res.sort_values("Date").reset_index(drop=True)

        close = res["close"]
        high = res["high"]
        low = res["low"]
        open_p = res["open"]
        volume = res["volume"]

        # --- 1. Trend Indicators ---
        for sma in [5, 10, 20, 50, 100, 200]:
            res[f"sma_{sma}"] = close.rolling(window=sma, min_periods=1).mean()

        for ema in [9, 20, 50, 200]:
            res[f"ema_{ema}"] = close.ewm(span=ema, adjust=False).mean()

        # --- 2. Momentum Indicators ---
        # RSI 14
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        res["rsi_14"] = 100 - (100 / (1 + rs))

        # Stochastic RSI
        rsi = res["rsi_14"]
        rsi_min = rsi.rolling(14, min_periods=1).min()
        rsi_max = rsi.rolling(14, min_periods=1).max()
        rsi_range = (rsi_max - rsi_min).replace(0, 1e-9)
        stoch_rsi = (rsi - rsi_min) / rsi_range
        res["stoch_rsi_k"] = stoch_rsi.rolling(3, min_periods=1).mean() * 100
        res["stoch_rsi_d"] = res["stoch_rsi_k"].rolling(3, min_periods=1).mean()

        # MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        res["macd"] = ema_12 - ema_26
        res["macd_signal"] = res["macd"].ewm(span=9, adjust=False).mean()
        res["macd_hist"] = res["macd"] - res["macd_signal"]

        # ROC & Momentum
        res["roc_12"] = close.pct_change(periods=12) * 100
        res["momentum_10"] = close - close.shift(10)

        # --- 3. Volatility Indicators ---
        # ATR 14
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["atr_14"] = tr.ewm(alpha=1/14, adjust=False).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(close / close.shift(1))
        res["volatility_20d"] = log_ret.rolling(window=20, min_periods=5).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        bb_sma = res["sma_20"]
        bb_std = close.rolling(window=20, min_periods=1).std()
        res["bollinger_upper"] = bb_sma + (2 * bb_std)
        res["bollinger_lower"] = bb_sma - (2 * bb_std)
        bb_width_denom = bb_sma.replace(0, 1e-9)
        res["bollinger_bandwidth"] = (res["bollinger_upper"] - res["bollinger_lower"]) / bb_width_denom

        # Volatility Regime
        vol = res["volatility_20d"].fillna(0)
        res["volatility_regime"] = np.where(
            vol > 0.35, "High Volatility",
            np.where(vol < 0.15, "Low Volatility", "Normal Volatility")
        )

        # --- 4. Volume Indicators ---
        res["volume_sma_20"] = volume.rolling(window=20, min_periods=1).mean()
        vol_sma_denom = res["volume_sma_20"].replace(0, 1)
        res["relative_volume"] = volume / vol_sma_denom
        res["volume_change_pct"] = volume.pct_change() * 100

        # On Balance Volume (OBV)
        obv_direction = np.where(close > close.shift(1), 1, np.where(close < close.shift(1), -1, 0))
        res["obv"] = (obv_direction * volume).fillna(0).cumsum()

        # Accumulation / Distribution (A/D)
        hl_denom = (high - low).replace(0, 1e-9)
        mfm = ((close - low) - (high - close)) / hl_denom
        mfv = mfm * volume
        res["ad_line"] = mfv.fillna(0).cumsum()

        # --- 5. Price Structure & Distances ---
        res["daily_return"] = close.pct_change()
        res["gap_pct"] = ((open_p - prev_close) / prev_close.replace(0, 1e-9)) * 100
        res["intraday_range_pct"] = ((high - low) / low.replace(0, 1e-9)) * 100

        # Moving average distances
        res["dist_sma_20_pct"] = ((close - res["sma_20"]) / res["sma_20"].replace(0, 1e-9)) * 100
        res["dist_sma_50_pct"] = ((close - res["sma_50"]) / res["sma_50"].replace(0, 1e-9)) * 100
        res["dist_sma_200_pct"] = ((close - res["sma_200"]) / res["sma_200"].replace(0, 1e-9)) * 100

        # 52-week High / Low distances
        rolling_52w_high = high.rolling(window=252, min_periods=20).max()
        rolling_52w_low = low.rolling(window=252, min_periods=20).min()
        res["dist_52w_high_pct"] = ((close - rolling_52w_high) / rolling_52w_high.replace(0, 1e-9)) * 100
        res["dist_52w_low_pct"] = ((close - rolling_52w_low) / rolling_52w_low.replace(0, 1e-9)) * 100

        # --- 6. Technical Events Identification ---
        # Golden Cross (50 DMA crosses above 200 DMA)
        sma50 = res["sma_50"]
        sma200 = res["sma_200"]
        res["golden_cross"] = (sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1))

        # Death Cross (50 DMA crosses below 200 DMA)
        res["death_cross"] = (sma50 < sma200) & (sma50.shift(1) >= sma200.shift(1))

        # Breakouts & Breakdowns (20-day high/low breakout)
        rolling_20_high = high.shift(1).rolling(window=20, min_periods=10).max()
        rolling_20_low = low.shift(1).rolling(window=20, min_periods=10).min()
        res["breakout_20d"] = close > rolling_20_high
        res["breakdown_20d"] = close < rolling_20_low

        # Support & Resistance levels (20-day min/max)
        res["support_level_20d"] = low.rolling(window=20, min_periods=5).min()
        res["resistance_level_20d"] = high.rolling(window=20, min_periods=5).max()

        # Unusual Volume (> 2.5x 20-day volume SMA)
        res["unusual_volume"] = res["relative_volume"] > 2.5

        if "Date" in res.columns:
            res["Date"] = res["Date"].dt.strftime("%Y-%m-%d")

        return res
