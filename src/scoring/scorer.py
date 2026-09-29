"""
Stock Scoring module.
Provides transparent, component-wise stock scoring normalized from 0 to 100 with clear categorical labels.
"""
import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class StockScorer:
    """
    Computes component scores and composite score (0-100) for a stock.
    """

    @staticmethod
    def calculate_scores(
        stock_df: pd.DataFrame,
        market_regime_info: Dict[str, Any],
        sector_info: Dict[str, Any],
        fundamental_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates individual component scores and final weighted composite score.
        """
        if stock_df.empty:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "components": {}
            }

        latest = stock_df.iloc[-1]
        close = latest.get("close", 1.0)

        # 1. Technical Trend Score (0-100)
        sma20 = latest.get("sma_20", close)
        sma50 = latest.get("sma_50", close)
        sma200 = latest.get("sma_200", close)
        ema20 = latest.get("ema_20", close)

        trend_points = 0
        if close > sma20: trend_points += 25
        if close > sma50: trend_points += 25
        if close > sma200: trend_points += 25
        if sma20 > sma50: trend_points += 15
        if sma50 > sma200: trend_points += 10
        technical_trend_score = float(trend_points)

        # 2. Momentum Score (0-100)
        rsi = latest.get("rsi_14", 50.0)
        macd_hist = latest.get("macd_hist", 0.0)
        roc = latest.get("roc_12", 0.0)

        mom_points = 50.0
        # RSI component
        if 50 <= rsi <= 70:
            mom_points += 25
        elif rsi > 70:
            mom_points += 15  # slightly overbought
        elif 30 <= rsi < 50:
            mom_points -= 15
        else:
            mom_points -= 25

        if macd_hist > 0:
            mom_points += 15
        else:
            mom_points -= 15

        if roc > 0:
            mom_points += 10
        else:
            mom_points -= 10

        momentum_score = float(np.clip(mom_points, 0, 100))

        # 3. Volume Score (0-100)
        rel_vol = latest.get("relative_volume", 1.0)
        vol_change = latest.get("volume_change_pct", 0.0)

        vol_points = 50.0
        if rel_vol > 1.5:
            vol_points += 30
        elif rel_vol > 1.0:
            vol_points += 15
        elif rel_vol < 0.5:
            vol_points -= 20

        if vol_change > 0:
            vol_points += 10
        else:
            vol_points -= 10

        volume_score = float(np.clip(vol_points, 0, 100))

        # 4. Relative Strength Score (0-100)
        ret_20d = (close - stock_df.iloc[-21].get("close", close)) / stock_df.iloc[-21].get("close", close) * 100 if len(stock_df) > 20 else 0.0
        nifty_ret_20d = market_regime_info.get("details", {}).get("nifty_return_20d", 0.0)
        rel_perf = ret_20d - nifty_ret_20d

        rs_points = 50.0 + (rel_perf * 3.0)
        relative_strength_score = float(np.clip(rs_points, 0, 100))

        # 5. Volatility Score (0-100)
        vol_20d = latest.get("volatility_20d", 0.20)
        if vol_20d < 0.15:
            volatility_score = 80.0
        elif vol_20d < 0.30:
            volatility_score = 60.0
        elif vol_20d < 0.45:
            volatility_score = 40.0
        else:
            volatility_score = 20.0

        # 6. Market Regime Score (0-100)
        regime_str = market_regime_info.get("market_regime", "Neutral")
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 70.0,
            "Neutral": 50.0,
            "Bearish": 30.0,
            "Strong Bearish": 10.0
        }
        market_regime_score = regime_map.get(regime_str, 50.0)

        # 7. Sector Score (0-100)
        sector_score = sector_info.get("momentum_score", 50.0)

        # 8. Fundamental Score (0-100)
        fundamental_score = fundamental_info.get("fundamental_score", 50.0)

        # Composite Score calculation
        weights = {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.05,
            "sector": 0.05,
            "fundamentals": 0.05
        }

        composite_score = (
            (technical_trend_score * weights["technical_trend"]) +
            (momentum_score * weights["momentum"]) +
            (volume_score * weights["volume"]) +
            (relative_strength_score * weights["relative_strength"]) +
            (volatility_score * weights["volatility"]) +
            (market_regime_score * weights["market_regime"]) +
            (sector_score * weights["sector"]) +
            (fundamental_score * weights["fundamentals"])
        )

        composite_score = round(float(np.clip(composite_score, 0, 100)), 2)

        # Score Labeling
        if composite_score >= 80:
            label = "Very Strong"
        elif composite_score >= 65:
            label = "Strong"
        elif composite_score >= 50:
            label = "Neutral"
        elif composite_score >= 35:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "composite_score": composite_score,
            "label": label,
            "components": {
                "technical_trend_score": round(technical_trend_score, 2),
                "momentum_score": round(momentum_score, 2),
                "volume_score": round(volume_score, 2),
                "relative_strength_score": round(relative_strength_score, 2),
                "volatility_score": round(volatility_score, 2),
                "market_regime_score": round(market_regime_score, 2),
                "sector_score": round(sector_score, 2),
                "fundamental_score": round(fundamental_score, 2)
            }
        }
