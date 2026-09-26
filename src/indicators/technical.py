"""
Technical Analysis module calculating deterministic technical indicators
and detecting actionable technical chart patterns and signals.
"""

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_technical_indicators(
    df: pd.DataFrame,
    sma_periods: List[int] = [5, 10, 20, 50, 100, 200],
    ema_periods: List[int] = [9, 20, 50, 200],
    rsi_period: int = 14,
    stoch_rsi_period: int = 14,
    stoch_k_period: int = 3,
    stoch_d_period: int = 3,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    roc_period: int = 12,
    atr_period: int = 14,
    bollinger_period: int = 20,
    bollinger_std: float = 2.0,
    volatility_period: int = 20,
    volume_sma_period: int = 20
) -> pd.DataFrame:
    """Calculates comprehensive technical indicators on OHLCV DataFrame."""
    if df.empty or len(df) < 2:
        return df

    out = df.copy()

    # 1. Price Returns & Structure
    out["daily_return"] = out["Close"].pct_change()
    out["gap_pct"] = (out["Open"] - out["Close"].shift(1)) / out["Close"].shift(1) * 100.0
    out["intraday_range_pct"] = (out["High"] - out["Low"]) / out["Low"] * 100.0

    # 2. Trend Moving Averages (SMA & EMA)
    for p in sma_periods:
        out[f"sma_{p}"] = out["Close"].rolling(window=p, min_periods=1).mean()
        out[f"dist_sma_{p}_pct"] = (out["Close"] - out[f"sma_{p}"]) / out[f"sma_{p}"] * 100.0

    for p in ema_periods:
        out[f"ema_{p}"] = out["Close"].ewm(span=p, adjust=False, min_periods=1).mean()
        out[f"dist_ema_{p}_pct"] = (out["Close"] - out[f"ema_{p}"]) / out[f"ema_{p}"] * 100.0

    # 3. 52-Week High & Low Distances (252 trading sessions)
    rolling_52w_high = out["High"].rolling(window=252, min_periods=1).max()
    rolling_52w_low = out["Low"].rolling(window=252, min_periods=1).min()
    out["dist_52w_high_pct"] = (out["Close"] - rolling_52w_high) / rolling_52w_high * 100.0
    out["dist_52w_low_pct"] = (out["Close"] - rolling_52w_low) / rolling_52w_low * 100.0

    # 4. Momentum Indicators
    # RSI
    delta = out["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1.0 / rsi_period, adjust=False, min_periods=rsi_period).mean()
    avg_loss = loss.ewm(alpha=1.0 / rsi_period, adjust=False, min_periods=rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
    out["rsi_14"] = out["rsi_14"].fillna(50.0)

    # Stochastic RSI
    rsi_min = out["rsi_14"].rolling(window=stoch_rsi_period, min_periods=1).min()
    rsi_max = out["rsi_14"].rolling(window=stoch_rsi_period, min_periods=1).max()
    stoch_rsi = (out["rsi_14"] - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
    out["stoch_rsi"] = stoch_rsi.fillna(0.5)
    out["stoch_rsi_k"] = out["stoch_rsi"].rolling(window=stoch_k_period, min_periods=1).mean() * 100.0
    out["stoch_rsi_d"] = out["stoch_rsi_k"].rolling(window=stoch_d_period, min_periods=1).mean()

    # MACD
    ema_fast = out["Close"].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = out["Close"].ewm(span=macd_slow, adjust=False).mean()
    out["macd"] = ema_fast - ema_slow
    out["macd_signal"] = out["macd"].ewm(span=macd_signal, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    # ROC & Momentum
    out["roc_12"] = out["Close"].pct_change(periods=roc_period) * 100.0
    out["momentum_10"] = out["Close"].diff(periods=10)

    # 5. Volatility Indicators
    # ATR
    prev_close = out["Close"].shift(1)
    tr1 = out["High"] - out["Low"]
    tr2 = (out["High"] - prev_close).abs()
    tr3 = (out["Low"] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    out["atr_14"] = tr.ewm(alpha=1.0 / atr_period, adjust=False, min_periods=1).mean()

    # Historical Volatility (Annualized std dev of log returns)
    log_returns = np.log(out["Close"] / prev_close)
    out["volatility_20d"] = log_returns.rolling(window=volatility_period, min_periods=1).std() * np.sqrt(252) * 100.0

    # Bollinger Bands
    bb_mid = out["Close"].rolling(window=bollinger_period, min_periods=1).mean()
    bb_std = out["Close"].rolling(window=bollinger_period, min_periods=1).std()
    out["bollinger_mid"] = bb_mid
    out["bollinger_upper"] = bb_mid + (bollinger_std * bb_std)
    out["bollinger_lower"] = bb_mid - (bollinger_std * bb_std)
    out["bollinger_width"] = (out["bollinger_upper"] - out["bollinger_lower"]) / bb_mid * 100.0

    # Volatility Regime
    vol_mean = out["volatility_20d"].rolling(window=252, min_periods=1).mean()
    vol_std = out["volatility_20d"].rolling(window=252, min_periods=1).std().replace(0, 1.0)
    vol_z = (out["volatility_20d"] - vol_mean) / vol_std
    regime_conds = [
        vol_z < -0.5,
        (vol_z >= -0.5) & (vol_z <= 0.5),
        (vol_z > 0.5) & (vol_z <= 1.5),
        vol_z > 1.5
    ]
    regime_labels = ["Low", "Normal", "High", "Extreme"]
    out["volatility_regime"] = np.select(regime_conds, regime_labels, default="Normal")

    # 6. Volume Indicators
    out["volume_sma_20"] = out["Volume"].rolling(window=volume_sma_period, min_periods=1).mean()
    out["relative_volume"] = out["Volume"] / out["volume_sma_20"].replace(0, np.nan)
    out["volume_change_pct"] = out["Volume"].pct_change() * 100.0

    # OBV
    price_diff = out["Close"].diff()
    direction = np.where(price_diff > 0, 1, np.where(price_diff < 0, -1, 0))
    out["obv"] = (direction * out["Volume"]).cumsum()

    # Accumulation / Distribution (A/D)
    clv = ((out["Close"] - out["Low"]) - (out["High"] - out["Close"])) / (out["High"] - out["Low"]).replace(0, np.nan)
    clv = clv.fillna(0.0)
    out["acc_dist"] = (clv * out["Volume"]).cumsum()

    return out


def detect_technical_signals(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects technical events on the latest row of processed DataFrame."""
    if df.empty or len(df) < 5:
        return {
            "golden_cross": False,
            "death_cross": False,
            "breakout": False,
            "breakdown": False,
            "unusual_volume": False,
            "support_level": None,
            "resistance_level": None,
            "trend": "Neutral",
            "momentum_divergence": False,
            "signals_list": []
        }

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    signals_list = []

    # Golden Cross / Death Cross
    golden_cross = False
    death_cross = False
    if "sma_50" in df.columns and "sma_200" in df.columns:
        curr_sma50 = latest["sma_50"]
        curr_sma200 = latest["sma_200"]
        prev_sma50 = prev["sma_50"]
        prev_sma200 = prev["sma_200"]

        if prev_sma50 <= prev_sma200 and curr_sma50 > curr_sma200:
            golden_cross = True
            signals_list.append("Golden Cross (50 DMA crossed above 200 DMA)")

        if prev_sma50 >= prev_sma200 and curr_sma50 < curr_sma200:
            death_cross = True
            signals_list.append("Death Cross (50 DMA crossed below 200 DMA)")

    # Breakouts / Breakdowns
    high_20 = df["High"].iloc[-21:-1].max() if len(df) >= 21 else df["High"].iloc[:-1].max()
    low_20 = df["Low"].iloc[-21:-1].min() if len(df) >= 21 else df["Low"].iloc[:-1].min()

    breakout = False
    breakdown = False
    if latest["Close"] > high_20 or ("bollinger_upper" in latest and latest["Close"] > latest["bollinger_upper"]):
        breakout = True
        signals_list.append("20-Day Price/Band Breakout")

    if latest["Close"] < low_20 or ("bollinger_lower" in latest and latest["Close"] < latest["bollinger_lower"]):
        breakdown = True
        signals_list.append("20-Day Price/Band Breakdown")

    # Unusual Volume
    unusual_vol = False
    rel_vol = latest.get("relative_volume", 1.0)
    if rel_vol >= 2.0:
        unusual_vol = True
        signals_list.append(f"Unusual Volume ({rel_vol:.2f}x 20DMA)")

    # Support / Resistance
    support_level = round(float(low_20), 2)
    resistance_level = round(float(high_20), 2)

    # Trend
    close_price = latest["Close"]
    sma20 = latest.get("sma_20", close_price)
    sma50 = latest.get("sma_50", close_price)
    sma200 = latest.get("sma_200", close_price)

    if close_price > sma20 > sma50 > sma200:
        trend = "Strong Uptrend"
    elif close_price > sma50:
        trend = "Uptrend"
    elif close_price < sma20 < sma50 < sma200:
        trend = "Strong Downtrend"
    elif close_price < sma50:
        trend = "Downtrend"
    else:
        trend = "Sideways/Neutral"

    # Momentum Divergence check (20-day high comparison with RSI)
    momentum_divergence = False
    if len(df) >= 30 and "rsi_14" in df.columns:
        recent_window = df.iloc[-20:]
        max_price_idx = recent_window["Close"].idxmax()
        max_rsi_idx = recent_window["rsi_14"].idxmax()
        if max_price_idx == df.index[-1] and max_rsi_idx != df.index[-1]:
            momentum_divergence = True
            signals_list.append("Bearish Momentum Divergence (Price New High without RSI New High)")

    return {
        "golden_cross": golden_cross,
        "death_cross": death_cross,
        "breakout": breakout,
        "breakdown": breakdown,
        "unusual_volume": unusual_vol,
        "support_level": support_level,
        "resistance_level": resistance_level,
        "trend": trend,
        "momentum_divergence": momentum_divergence,
        "signals_list": signals_list
    }
