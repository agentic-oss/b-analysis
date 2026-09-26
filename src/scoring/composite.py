"""
Composite Stock Scoring Engine calculating transparent 0-100 stock ratings
from individual component scores (Trend, Momentum, Volume, RS, Volatility, Regime, Sector, Fundamentals).
"""

import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_composite_score(
    stock_df: pd.DataFrame,
    market_regime: Dict[str, Any],
    sector_info: Optional[Dict[str, Any]] = None,
    fundamental_info: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculates transparent 0-100 composite stock score with individual component scores.
    """
    if weights is None:
        weights = {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.10,
            "sector": 0.05
        }

    if stock_df.empty or len(stock_df) < 5:
        return {
            "composite_score": 50.0,
            "label": "Neutral",
            "components": {},
            "weights": weights
        }

    latest = stock_df.iloc[-1]
    close = latest["Close"]

    # 1. Technical Trend Score (0-100)
    sma20 = latest.get("sma_20", close)
    sma50 = latest.get("sma_50", close)
    sma200 = latest.get("sma_200", close)
    ema20 = latest.get("ema_20", close)

    trend_pts = 50.0
    if close > sma20:
        trend_pts += 15.0
    else:
        trend_pts -= 15.0

    if close > sma50:
        trend_pts += 15.0
    else:
        trend_pts -= 15.0

    if close > sma200:
        trend_pts += 10.0
    else:
        trend_pts -= 10.0

    if ema20 > sma50:
        trend_pts += 10.0
    else:
        trend_pts -= 10.0

    trend_score = max(0.0, min(100.0, trend_pts))

    # 2. Momentum Score (0-100)
    rsi = latest.get("rsi_14", 50.0)
    macd_hist = latest.get("macd_hist", 0.0)
    roc = latest.get("roc_12", 0.0)

    mom_pts = 50.0
    if 50.0 <= rsi <= 70.0:
        mom_pts += 20.0
    elif rsi > 70.0:
        mom_pts += 10.0  # Overbought warning
    elif rsi < 30.0:
        mom_pts -= 20.0  # Oversold

    if macd_hist > 0:
        mom_pts += 15.0
    else:
        mom_pts -= 15.0

    if roc > 0:
        mom_pts += 15.0
    else:
        mom_pts -= 15.0

    momentum_score = max(0.0, min(100.0, mom_pts))

    # 3. Volume Score (0-100)
    rel_vol = latest.get("relative_volume", 1.0)
    vol_chg = latest.get("volume_change_pct", 0.0)

    vol_pts = 50.0
    if rel_vol >= 1.5:
        vol_pts += 25.0
    elif rel_vol >= 1.0:
        vol_pts += 10.0
    else:
        vol_pts -= 15.0

    if vol_chg > 0 and latest.get("daily_return", 0.0) > 0:
        vol_pts += 15.0

    volume_score = max(0.0, min(100.0, vol_pts))

    # 4. Relative Strength Score (0-100)
    ret_5d = (close - stock_df["Close"].iloc[-6]) / stock_df["Close"].iloc[-6] * 100.0 if len(stock_df) >= 6 else 0.0
    nifty_1d = market_regime.get("nifty_1d_return") or 0.0
    rs_pts = 50.0 + (ret_5d * 2.0) - (nifty_1d * 1.5)
    rs_score = max(0.0, min(100.0, rs_pts))

    # 5. Volatility Score (0-100)
    vol_regime = latest.get("volatility_regime", "Normal")
    vol_pts = 70.0
    if vol_regime == "Low":
        vol_pts = 85.0
    elif vol_regime == "Normal":
        vol_pts = 70.0
    elif vol_regime == "High":
        vol_pts = 45.0
    elif vol_regime == "Extreme":
        vol_pts = 20.0

    volatility_score = max(0.0, min(100.0, vol_pts))

    # 6. Market Regime Score (0-100)
    regime_score = float(market_regime.get("composite_score", 50.0))

    # 7. Sector Score (0-100)
    sector_score = float(sector_info.get("momentum_score", 50.0)) if sector_info else 50.0

    # 8. Fundamental Score (0-100)
    fund_score = None
    if fundamental_info and fundamental_info.get("available") and fundamental_info.get("fundamental_score") is not None:
        fund_score = float(fundamental_info["fundamental_score"])

    # Aggregate weighted composite score
    comp_map = {
        "technical_trend": trend_score,
        "momentum": momentum_score,
        "volume": volume_score,
        "relative_strength": rs_score,
        "volatility": volatility_score,
        "market_regime": regime_score,
        "sector": sector_score
    }

    if fund_score is not None:
        comp_map["fundamental"] = fund_score
        # Adjust weights if fundamental present
        norm_weights = {
            "technical_trend": 0.20,
            "momentum": 0.15,
            "volume": 0.10,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.10,
            "sector": 0.05,
            "fundamental": 0.15
        }
    else:
        norm_weights = weights

    composite_score = sum(comp_map[k] * norm_weights[k] for k in comp_map if k in norm_weights)
    composite_score = round(max(0.0, min(100.0, composite_score)), 1)

    # Label classification
    if composite_score >= 80.0:
        label = "Very Strong"
    elif composite_score >= 65.0:
        label = "Strong"
    elif composite_score >= 50.0:
        label = "Neutral"
    elif composite_score >= 35.0:
        label = "Weak"
    else:
        label = "Very Weak"

    components = {k: round(v, 1) for k, v in comp_map.items()}

    return {
        "composite_score": composite_score,
        "label": label,
        "components": components,
        "weights": norm_weights
    }
