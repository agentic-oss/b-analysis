"""
Market Regime Analysis module calculating market breadth, benchmark trends,
volatility regimes, and rule-based market classification.
"""

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def analyze_market_regime(
    nifty_df: pd.DataFrame,
    banknifty_df: pd.DataFrame,
    stock_dfs: Dict[str, pd.DataFrame]
) -> Dict[str, Any]:
    """
    Analyzes market regime based on benchmark trends, volatility, and market breadth.

    Classification Rules (Composite Score 0 to 100):
    - Benchmark Trend: NIFTY vs 20, 50, 200 DMA (Up to 30 pts)
    - BANK NIFTY Trend: Bank NIFTY vs 20, 50 DMA (Up to 15 pts)
    - Breadth (% Above 50 DMA): High breadth > 70% (Up to 25 pts)
    - Advance / Decline Ratio: A/D > 1.5 (Up to 15 pts)
    - Volatility Regime: Low/Normal volatility adds up to 15 pts, Extreme subtracts.

    Regime Map:
    - >= 80: Strong Bullish
    - >= 60: Bullish
    - >= 40: Neutral
    - >= 20: Bearish
    - < 20: Strong Bearish
    """
    result = {
        "regime": "Neutral",
        "composite_score": 50.0,
        "nifty_close": None,
        "nifty_1d_return": None,
        "nifty_trend": "Unknown",
        "nifty_volatility_20d": None,
        "banknifty_close": None,
        "banknifty_1d_return": None,
        "banknifty_trend": "Unknown",
        "breadth": {
            "advance_decline_ratio": 1.0,
            "advances": 0,
            "declines": 0,
            "unchanged": 0,
            "pct_above_20dma": 0.0,
            "pct_above_50dma": 0.0,
            "pct_above_200dma": 0.0,
            "new_20d_highs": 0,
            "new_20d_lows": 0
        },
        "description": "Market environment analysis based on rule-based framework."
    }

    # 1. NIFTY Analysis
    if not nifty_df.empty and len(nifty_df) >= 5:
        latest_nifty = nifty_df.iloc[-1]
        close = latest_nifty["Close"]
        result["nifty_close"] = float(round(close, 2))
        result["nifty_1d_return"] = float(round(latest_nifty.get("daily_return", 0.0) * 100.0, 2))
        result["nifty_volatility_20d"] = float(round(latest_nifty.get("volatility_20d", 15.0), 2))

        sma20 = latest_nifty.get("sma_20", close)
        sma50 = latest_nifty.get("sma_50", close)
        sma200 = latest_nifty.get("sma_200", close)

        if close > sma20 > sma50 > sma200:
            result["nifty_trend"] = "Strong Uptrend"
        elif close > sma50:
            result["nifty_trend"] = "Uptrend"
        elif close < sma20 < sma50 < sma200:
            result["nifty_trend"] = "Strong Downtrend"
        elif close < sma50:
            result["nifty_trend"] = "Downtrend"
        else:
            result["nifty_trend"] = "Sideways"

    # 2. BANK NIFTY Analysis
    if not banknifty_df.empty and len(banknifty_df) >= 5:
        latest_bn = banknifty_df.iloc[-1]
        close = latest_bn["Close"]
        result["banknifty_close"] = float(round(close, 2))
        result["banknifty_1d_return"] = float(round(latest_bn.get("daily_return", 0.0) * 100.0, 2))

        sma50 = latest_bn.get("sma_50", close)
        result["banknifty_trend"] = "Uptrend" if close >= sma50 else "Downtrend"

    # 3. Market Breadth across tracked stocks
    total_stocks = len(stock_dfs)
    if total_stocks > 0:
        advances = 0
        declines = 0
        unchanged = 0
        above_20dma = 0
        above_50dma = 0
        above_200dma = 0
        new_highs = 0
        new_lows = 0

        for sym, df in stock_dfs.items():
            if df.empty or len(df) < 2:
                continue

            last = df.iloc[-1]
            ret = last.get("daily_return", 0.0)
            if ret > 0.0001:
                advances += 1
            elif ret < -0.0001:
                declines += 1
            else:
                unchanged += 1

            c = last["Close"]
            if c > last.get("sma_20", c):
                above_20dma += 1
            if c > last.get("sma_50", c):
                above_50dma += 1
            if c > last.get("sma_200", c):
                above_200dma += 1

            if len(df) >= 20:
                high_20 = df["High"].iloc[-21:-1].max()
                low_20 = df["Low"].iloc[-21:-1].min()
                if c >= high_20:
                    new_highs += 1
                if c <= low_20:
                    new_lows += 1

        ad_ratio = float(advances / max(1, declines))
        result["breadth"] = {
            "advance_decline_ratio": round(ad_ratio, 2),
            "advances": advances,
            "declines": declines,
            "unchanged": unchanged,
            "pct_above_20dma": round(above_20dma / total_stocks * 100.0, 1),
            "pct_above_50dma": round(above_50dma / total_stocks * 100.0, 1),
            "pct_above_200dma": round(above_200dma / total_stocks * 100.0, 1),
            "new_20d_highs": new_highs,
            "new_20d_lows": new_lows
        }

    # 4. Rule-based composite score logic
    score = 50.0

    # NIFTY trend score
    if result["nifty_trend"] == "Strong Uptrend":
        score += 20.0
    elif result["nifty_trend"] == "Uptrend":
        score += 10.0
    elif result["nifty_trend"] == "Downtrend":
        score -= 10.0
    elif result["nifty_trend"] == "Strong Downtrend":
        score -= 20.0

    # Bank Nifty
    if result["banknifty_trend"] == "Uptrend":
        score += 5.0
    else:
        score -= 5.0

    # Breadth score
    pct_50 = result["breadth"]["pct_above_50dma"]
    if pct_50 >= 70.0:
        score += 15.0
    elif pct_50 >= 50.0:
        score += 5.0
    elif pct_50 <= 30.0:
        score -= 15.0

    ad_r = result["breadth"]["advance_decline_ratio"]
    if ad_r >= 1.5:
        score += 10.0
    elif ad_r <= 0.67:
        score -= 10.0

    score = max(0.0, min(100.0, score))
    result["composite_score"] = round(score, 1)

    if score >= 80.0:
        result["regime"] = "Strong Bullish"
    elif score >= 60.0:
        result["regime"] = "Bullish"
    elif score >= 40.0:
        result["regime"] = "Neutral"
    elif score >= 20.0:
        result["regime"] = "Bearish"
    else:
        result["regime"] = "Strong Bearish"

    return result
