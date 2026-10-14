import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class CompositeScorer:
    """
    Computes transparent composite stock scores (0-100) and assigns labels:
    80–100: Very Strong
    65–79: Strong
    50–64: Neutral
    35–49: Weak
    0–34: Very Weak
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.05,
            "sector": 0.05,
            "fundamental": 0.05
        }

    def compute_stock_score(
        self,
        stock_df: pd.DataFrame,
        market_regime_score: float,
        sector_rank_info: Optional[Dict[str, Any]] = None,
        fundamental_score: float = 50.0
    ) -> Dict[str, Any]:
        """Calculates component scores and weighted composite score for a single stock."""
        if stock_df.empty:
            return {"composite_score": 50, "label": "Neutral", "components": {}}

        latest = stock_df.iloc[-1]
        close = latest.get("close", 0)
        sma20 = latest.get("sma_20", close)
        sma50 = latest.get("sma_50", close)
        sma200 = latest.get("sma_200", close)

        # 1. Technical Trend Score (0-100)
        trend_score = 50.0
        if close > sma20: trend_score += 15
        if close > sma50: trend_score += 15
        if close > sma200: trend_score += 10
        if sma20 > sma50 > sma200: trend_score += 10
        trend_score = min(100.0, max(0.0, trend_score))

        # 2. Momentum Score (0-100)
        rsi = latest.get("rsi_14", 50) or 50
        stoch_rsi = latest.get("stoch_rsi", 0.5) or 0.5
        macd_hist = latest.get("macd_hist", 0) or 0

        mom_score = 50.0
        if 50 <= rsi <= 70: mom_score += 20
        elif rsi > 70: mom_score += 10
        elif rsi < 30: mom_score -= 20

        if macd_hist > 0: mom_score += 15
        else: mom_score -= 15
        mom_score = min(100.0, max(0.0, mom_score))

        # 3. Volume Score (0-100)
        rel_vol = latest.get("relative_volume", 1.0) or 1.0
        vol_score = 50.0
        if rel_vol >= 1.5: vol_score += 30
        elif rel_vol >= 1.1: vol_score += 15
        elif rel_vol < 0.7: vol_score -= 20
        vol_score = min(100.0, max(0.0, vol_score))

        # 4. Relative Strength Score (0-100)
        ret_20d = latest.get("return_20d", 0.0) or 0.0
        rs_score = 50.0 + (ret_20d * 100)
        rs_score = min(100.0, max(0.0, float(rs_score)))

        # 5. Volatility Score (0-100)
        vol_20d = latest.get("volatility_20d", 0.2) or 0.2
        volat_score = 50.0
        if 0.10 <= vol_20d <= 0.30: volat_score += 25
        elif vol_20d > 0.50: volat_score -= 25
        volat_score = min(100.0, max(0.0, volat_score))

        # 6. Sector Score
        sector_score = 50.0
        if sector_rank_info:
            sector_score = sector_rank_info.get("momentum_score", 50.0)

        components = {
            "technical_trend": round(trend_score, 2),
            "momentum": round(mom_score, 2),
            "volume": round(vol_score, 2),
            "relative_strength": round(rs_score, 2),
            "volatility": round(volat_score, 2),
            "market_regime": round(float(market_regime_score), 2),
            "sector": round(float(sector_score), 2),
            "fundamental": round(float(fundamental_score), 2)
        }

        composite = sum(components[k] * self.weights.get(k, 0.0) for k in components)
        composite = round(max(0.0, min(100.0, composite)), 2)

        if composite >= 80:
            label = "Very Strong"
        elif composite >= 65:
            label = "Strong"
        elif composite >= 50:
            label = "Neutral"
        elif composite >= 35:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "components": components
        }
