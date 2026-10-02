"""
Transparent Stock Scoring System.
Calculates transparent 0-100 composite scores from component scores (trend, momentum, volume,
relative strength, volatility, market regime, sector, fundamentals) and provides human-readable labels.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class StockScorer:
    """Transparent composite stock scoring engine."""

    DEFAULT_WEIGHTS = {
        "technical_trend": 0.25,
        "momentum": 0.20,
        "volume": 0.15,
        "relative_strength": 0.15,
        "market_regime": 0.10,
        "sector": 0.10,
        "fundamental": 0.05,
    }

    LABELS = [
        (80.0, 100.0, "Very Strong"),
        (65.0, 79.99, "Strong"),
        (50.0, 64.99, "Neutral"),
        (35.0, 49.99, "Weak"),
        (0.0, 34.99, "Very Weak"),
    ]

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate_score(
        self,
        stock_row: pd.Series,
        market_regime_info: Dict[str, Any],
        sector_info: Optional[Dict[str, Any]] = None,
        fundamental_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates composite 0-100 score and sub-component scores for a single stock observation.
        """
        c_price = float(stock_row.get("close", 0.0))
        sma_20 = float(stock_row.get("sma_20", c_price))
        sma_50 = float(stock_row.get("sma_50", c_price))
        sma_200 = float(stock_row.get("sma_200", c_price))

        # 1. Technical Trend Score (0 - 100)
        trend_score = 50.0
        if c_price > sma_20:
            trend_score += 15
        if c_price > sma_50:
            trend_score += 15
        if c_price > sma_200:
            trend_score += 10
        if sma_20 > sma_50 > sma_200:
            trend_score += 10
        elif c_price < sma_20 and c_price < sma_50 and c_price < sma_200:
            trend_score = 15.0
        trend_score = min(max(trend_score, 0.0), 100.0)

        # 2. Momentum Score (0 - 100)
        rsi = float(stock_row.get("rsi_14", 50.0))
        macd_hist = float(stock_row.get("macd_hist", 0.0))
        roc_12 = float(stock_row.get("roc_12", 0.0))

        mom_score = 50.0
        if 50.0 <= rsi <= 70.0:
            mom_score += 20
        elif rsi > 70.0:
            mom_score += 10  # Bullish momentum but near overbought
        elif rsi < 30.0:
            mom_score -= 20

        if macd_hist > 0:
            mom_score += 15
        else:
            mom_score -= 15

        if roc_12 > 0:
            mom_score += 15
        else:
            mom_score -= 15
        mom_score = min(max(mom_score, 0.0), 100.0)

        # 3. Volume Score (0 - 100)
        rel_vol = float(stock_row.get("relative_volume", 1.0))
        ret_1d = float(stock_row.get("daily_return", 0.0))
        vol_score = 50.0
        if rel_vol > 1.5 and ret_1d > 0:
            vol_score = 85.0
        elif rel_vol > 1.2 and ret_1d > 0:
            vol_score = 70.0
        elif rel_vol > 1.5 and ret_1d < 0:
            vol_score = 25.0
        elif rel_vol < 0.7:
            vol_score = 40.0

        # 4. Relative Strength Score (0 - 100)
        nifty_ret = float(market_regime_info.get("nifty_return_1d", 0.0))
        rs_diff = (ret_1d - nifty_ret) * 100
        rs_score = min(max(50.0 + (rs_diff * 10.0), 0.0), 100.0)

        # 5. Market Regime Score (0 - 100)
        regime_label = market_regime_info.get("regime", "Neutral")
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 75.0,
            "Neutral": 50.0,
            "Bearish": 30.0,
            "Strong Bearish": 10.0,
        }
        market_score = regime_map.get(regime_label, 50.0)

        # 6. Sector Score (0 - 100)
        sector_score = 50.0
        if sector_info:
            sector_score = float(sector_info.get("momentum_score", 50.0))

        # 7. Fundamental Score (0 - 100)
        fund_score = 50.0
        if fundamental_info:
            fund_score = float(fundamental_info.get("fundamental_score", 50.0))

        # Composite Calculation
        weighted_score = (
            trend_score * self.weights["technical_trend"]
            + mom_score * self.weights["momentum"]
            + vol_score * self.weights["volume"]
            + rs_score * self.weights["relative_strength"]
            + market_score * self.weights["market_regime"]
            + sector_score * self.weights["sector"]
            + fund_score * self.weights["fundamental"]
        )

        composite_score = round(min(max(weighted_score, 0.0), 100.0), 1)

        # Labeling
        label = "Neutral"
        for min_val, max_val, l in self.LABELS:
            if min_val <= composite_score <= max_val:
                label = l
                break

        return {
            "symbol": stock_row.get("ticker", "UNKNOWN"),
            "composite_score": composite_score,
            "label": label,
            "components": {
                "technical_trend_score": round(trend_score, 1),
                "momentum_score": round(mom_score, 1),
                "volume_score": round(vol_score, 1),
                "relative_strength_score": round(rs_score, 1),
                "market_regime_score": round(market_score, 1),
                "sector_score": round(sector_score, 1),
                "fundamental_score": round(fund_score, 1),
            },
        }
