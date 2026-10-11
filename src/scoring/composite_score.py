import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CompositeScorer:
    """Calculates a transparent composite stock score (0-100) and individual sub-scores."""

    LABEL_RANGES = [
        (80, 100, "Very Strong"),
        (65, 79, "Strong"),
        (50, 64, "Neutral"),
        (35, 49, "Weak"),
        (0, 34, "Very Weak")
    ]

    @staticmethod
    def compute_stock_score(
        technical_signals: Dict[str, Any],
        market_regime: Dict[str, Any],
        sector_info: Optional[Dict[str, Any]],
        fundamental_info: Optional[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates normalized sub-scores (0-100) and weighted composite score.
        """
        if weights is None:
            weights = {
                "technical_trend": 0.25,
                "momentum": 0.20,
                "volume": 0.15,
                "relative_strength": 0.15,
                "volatility": 0.10,
                "market_regime": 0.10,
                "fundamental": 0.05
            }

        # 1. Technical Trend Score
        dist_sma20 = technical_signals.get("dist_sma_20") or 0.0
        dist_sma50 = technical_signals.get("dist_sma_50") or 0.0
        dist_sma200 = technical_signals.get("dist_sma_200") or 0.0

        trend_pts = 50.0
        if dist_sma20 > 0: trend_pts += 15.0
        if dist_sma50 > 0: trend_pts += 15.0
        if dist_sma200 > 0: trend_pts += 20.0
        if dist_sma20 < 0: trend_pts -= 15.0
        if dist_sma50 < 0: trend_pts -= 15.0
        if dist_sma200 < 0: trend_pts -= 20.0
        trend_score = max(0.0, min(100.0, trend_pts))

        # 2. Momentum Score
        rsi = technical_signals.get("rsi_14") or 50.0
        macd_hist = technical_signals.get("macd_hist") or 0.0
        mom_pts = 50.0
        if 40 <= rsi <= 70:
            mom_pts += (rsi - 50) * 1.5
        elif rsi > 70:
            mom_pts += 25.0
        else:
            mom_pts -= (50 - rsi) * 1.5

        if macd_hist > 0: mom_pts += 15.0
        else: mom_pts -= 15.0
        momentum_score = max(0.0, min(100.0, mom_pts))

        # 3. Volume Score
        rel_vol = technical_signals.get("relative_volume") or 1.0
        ret_1d = technical_signals.get("return_1d") or 0.0
        vol_pts = 50.0
        if rel_vol > 1.2:
            if ret_1d > 0: vol_pts += 30.0
            else: vol_pts -= 30.0
        elif rel_vol < 0.8:
            vol_pts -= 10.0
        volume_score = max(0.0, min(100.0, vol_pts))

        # 4. Relative Strength Score
        nifty_ret = market_regime.get("nifty_return_1d") or 0.0
        rel_perf = ret_1d - nifty_ret
        rs_pts = 50.0 + (rel_perf * 1000.0) # 1% outperform = +10 pts
        rs_score = max(0.0, min(100.0, rs_pts))

        # 5. Volatility Score
        vol_regime = technical_signals.get("volatility_regime") or "Normal"
        if vol_regime == "Low": vol_score = 70.0
        elif vol_regime == "Normal": vol_score = 50.0
        else: vol_score = 30.0

        # 6. Market Regime Score
        regime_str = market_regime.get("regime") or "Neutral"
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 75.0,
            "Neutral": 50.0,
            "Bearish": 30.0,
            "Strong Bearish": 10.0
        }
        regime_score = regime_map.get(regime_str, 50.0)

        # 7. Sector Score
        sector_score = 50.0
        if sector_info:
            sec_rs = sector_info.get("relative_strength_1d", 0.0)
            sector_score = max(0.0, min(100.0, 50.0 + (sec_rs * 5.0)))

        # 8. Fundamental Score
        fund_score = 50.0
        if fundamental_info and fundamental_info.get("available"):
            fund_score = fundamental_info.get("fundamental_score", 50.0)

        # Calculate Total Composite Score
        composite = (
            trend_score * weights["technical_trend"] +
            momentum_score * weights["momentum"] +
            volume_score * weights["volume"] +
            rs_score * weights["relative_strength"] +
            vol_score * weights["volatility"] +
            regime_score * weights["market_regime"] +
            fund_score * weights["fundamental"]
        )
        composite = round(max(0.0, min(100.0, composite)), 2)

        # Label Assignment
        label = "Neutral"
        for low, high, lbl in CompositeScorer.LABEL_RANGES:
            if low <= composite <= high:
                label = lbl
                break

        return {
            "composite_score": composite,
            "label": label,
            "component_scores": {
                "technical_trend_score": round(trend_score, 2),
                "momentum_score": round(momentum_score, 2),
                "volume_score": round(volume_score, 2),
                "relative_strength_score": round(rs_score, 2),
                "volatility_score": round(vol_score, 2),
                "market_regime_score": round(regime_score, 2),
                "sector_score": round(sector_score, 2),
                "fundamental_score": round(fund_score, 2)
            },
            "weights_used": weights
        }
