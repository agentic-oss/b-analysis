import numpy as np
import pandas as pd
from typing import Dict, Any

class StockScorer:
    """
    Calculates a transparent composite score (0-100) combining component sub-scores:
    - Technical Trend Score (20%)
    - Momentum Score (20%)
    - Volume Score (15%)
    - Relative Strength Score (15%)
    - Volatility Score (10%)
    - Market Regime Score (10%)
    - Sector Score (10%)

    Labels:
    80-100: Very Strong
    65-79: Strong
    50-64: Neutral
    35-49: Weak
    0-34: Very Weak
    """

    @staticmethod
    def calculate_score(
        stock_df: pd.DataFrame,
        market_regime_info: Dict[str, Any],
        sector_info: Dict[str, Any],
        fundamental_score: float = 50.0
    ) -> Dict[str, Any]:

        if stock_df.empty or len(stock_df) == 0:
            return StockScorer._default_score()

        latest = stock_df.iloc[-1]
        close = latest["close"]

        # 1. Technical Trend Score
        sma_20 = latest.get("sma_20", close)
        sma_50 = latest.get("sma_50", close)
        sma_200 = latest.get("sma_200", close)

        t_score = 50.0
        if close > sma_20: t_score += 15
        if close > sma_50: t_score += 15
        if close > sma_200: t_score += 20
        trend_score = np.clip(t_score, 0.0, 100.0)

        # 2. Momentum Score
        rsi = latest.get("rsi_14", 50.0)
        macd_hist = latest.get("macd_hist", 0.0)
        m_score = 50.0
        if 40 <= rsi <= 70: m_score += 20
        elif rsi > 70: m_score += 10
        else: m_score -= 20
        if macd_hist > 0: m_score += 15
        else: m_score -= 15
        momentum_score = np.clip(m_score, 0.0, 100.0)

        # 3. Volume Score
        rel_vol = latest.get("relative_volume", 1.0)
        v_score = 50.0 + (rel_vol - 1.0) * 25.0
        volume_score = np.clip(v_score, 0.0, 100.0)

        # 4. Relative Strength Score
        ret_20d = latest.get("daily_return", 0.0) # Proxy or 20d ret
        if "return_20d" in latest:
            ret_20d = latest["return_20d"]
        rs_score = 50.0 + (ret_20d * 100 * 2.0)
        relative_strength_score = np.clip(rs_score, 0.0, 100.0)

        # 5. Volatility Score (Lower/stable vol is better for scoring stability)
        vol_reg = latest.get("volatility_regime", "Normal")
        if vol_reg == "Low": vol_score = 80.0
        elif vol_reg == "Normal": vol_score = 65.0
        else: vol_score = 35.0

        # 6. Market Regime Score
        regime = market_regime_info.get("regime", "Neutral")
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 75.0,
            "Neutral": 50.0,
            "Bearish": 35.0,
            "Strong Bearish": 15.0
        }
        regime_score = regime_map.get(regime, 50.0)

        # 7. Sector Score
        sec_mom = sector_info.get("momentum_score", 50.0)

        # Composite Score Calculation
        composite = (
            trend_score * 0.20 +
            momentum_score * 0.20 +
            volume_score * 0.15 +
            relative_strength_score * 0.15 +
            vol_score * 0.10 +
            regime_score * 0.10 +
            sec_mom * 0.10
        )
        composite = float(np.clip(composite, 0.0, 100.0))

        # Determine Label
        if composite >= 80: label = "Very Strong"
        elif composite >= 65: label = "Strong"
        elif composite >= 50: label = "Neutral"
        elif composite >= 35: label = "Weak"
        else: label = "Very Weak"

        return {
            "composite_score": round(composite, 2),
            "label": label,
            "components": {
                "technical_trend_score": round(float(trend_score), 2),
                "momentum_score": round(float(momentum_score), 2),
                "volume_score": round(float(volume_score), 2),
                "relative_strength_score": round(float(relative_strength_score), 2),
                "volatility_score": round(float(vol_score), 2),
                "market_regime_score": round(float(regime_score), 2),
                "sector_score": round(float(sec_mom), 2),
                "fundamental_score": round(float(fundamental_score), 2)
            }
        }

    @staticmethod
    def _default_score() -> Dict[str, Any]:
        return {
            "composite_score": 50.0,
            "label": "Neutral",
            "components": {
                "technical_trend_score": 50.0,
                "momentum_score": 50.0,
                "volume_score": 50.0,
                "relative_strength_score": 50.0,
                "volatility_score": 50.0,
                "market_regime_score": 50.0,
                "sector_score": 50.0,
                "fundamental_score": 50.0
            }
        }
