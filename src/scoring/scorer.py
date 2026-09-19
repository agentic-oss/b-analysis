"""
Stock Scoring System Engine.
Creates transparent composite scores (0-100) with separate component breakdown.
"""

from typing import Dict, Any, Optional


class StockScorer:
    """Computes composite stock score (0-100) and sub-scores."""

    def compute_score(
        self,
        stock_indicators: Dict[str, Any],
        market_regime_info: Dict[str, Any],
        sector_info: Optional[Dict[str, Any]] = None,
        fundamental_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculates normalized sub-scores and weighted total score."""

        # 1. Technical Trend Score
        trend_score = 50.0
        close = stock_indicators.get("close", 0)
        sma_20 = stock_indicators.get("sma_20", close)
        sma_50 = stock_indicators.get("sma_50", close)
        sma_200 = stock_indicators.get("sma_200", close)

        if close > sma_20: trend_score += 15.0
        if close > sma_50: trend_score += 15.0
        if close > sma_200: trend_score += 20.0
        trend_score = min(max(trend_score, 0.0), 100.0)

        # 2. Momentum Score
        rsi = stock_indicators.get("rsi_14", 50.0)
        macd_hist = stock_indicators.get("macd_hist", 0.0)
        roc_10 = stock_indicators.get("roc_10", 0.0)

        mom_score = 50.0
        if 50.0 <= rsi <= 70.0: mom_score += 20.0
        elif rsi > 70.0: mom_score += 10.0
        elif rsi < 30.0: mom_score -= 20.0

        if macd_hist > 0: mom_score += 15.0
        if roc_10 > 0: mom_score += 15.0
        mom_score = min(max(mom_score, 0.0), 100.0)

        # 3. Volume Score
        rel_vol = stock_indicators.get("relative_volume", 1.0)
        daily_ret = stock_indicators.get("daily_return", 0.0)

        vol_score = 50.0
        if rel_vol > 1.5 and daily_ret > 0: vol_score += 30.0
        elif rel_vol > 1.2 and daily_ret > 0: vol_score += 15.0
        elif rel_vol > 1.5 and daily_ret < 0: vol_score -= 20.0
        vol_score = min(max(vol_score, 0.0), 100.0)

        # 4. Relative Strength Score (dist from 52w high / low)
        dist_52w_high = stock_indicators.get("dist_52w_high", -10.0)
        rs_score = 50.0
        if dist_52w_high > -5.0: rs_score += 35.0
        elif dist_52w_high > -15.0: rs_score += 20.0
        elif dist_52w_high < -30.0: rs_score -= 20.0
        rs_score = min(max(rs_score, 0.0), 100.0)

        # 5. Volatility Score
        vol_regime = stock_indicators.get("volatility_regime", "Normal")
        vol_score = 70.0 if vol_regime == "Normal" else (50.0 if vol_regime == "Low" else 30.0)

        # 6. Market Regime Score
        mkt_score = market_regime_info.get("regime_score", 50.0)

        # 7. Sector Score
        sec_score = 50.0
        if sector_info:
            sec_momentum = sector_info.get("momentum_score", 0.0)
            sec_score = min(max(50.0 + sec_momentum, 0.0), 100.0)

        # 8. Fundamental Score
        fund_score = 50.0
        if fundamental_info and fundamental_info.get("available", False):
            fund_score = fundamental_info.get("fundamental_score", 50.0)

        # Composite Score Calculation with standard weights
        weights = {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.05,
            "sector": 0.05,
            "fundamental": 0.05
        }

        total_score = (
            (trend_score * weights["technical_trend"]) +
            (mom_score * weights["momentum"]) +
            (vol_score * weights["volume"]) +
            (rs_score * weights["relative_strength"]) +
            (vol_score * weights["volatility"]) +
            (mkt_score * weights["market_regime"]) +
            (sec_score * weights["sector"]) +
            (fund_score * weights["fundamental"])
        )
        total_score = round(min(max(total_score, 0.0), 100.0), 2)

        label = "Very Strong" if total_score >= 80 else \
                "Strong" if total_score >= 65 else \
                "Neutral" if total_score >= 50 else \
                "Weak" if total_score >= 35 else "Very Weak"

        return {
            "composite_score": total_score,
            "label": label,
            "components": {
                "technical_trend_score": round(trend_score, 2),
                "momentum_score": round(mom_score, 2),
                "volume_score": round(vol_score, 2),
                "relative_strength_score": round(rs_score, 2),
                "volatility_score": round(vol_score, 2),
                "market_regime_score": round(mkt_score, 2),
                "sector_score": round(sec_score, 2),
                "fundamental_score": round(fund_score, 2)
            }
        }
