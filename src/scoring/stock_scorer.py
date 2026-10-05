"""
Stock Scoring Engine providing transparent composite scoring.
"""

from typing import Dict, Any, Tuple
import pandas as pd


class StockScorer:
    """Calculates composite stock score (0 to 100) from components with clear label mappings."""

    @staticmethod
    def score_stock(
        df: pd.DataFrame,
        market_regime_score: float = 0.0,
        fundamental_score: float = 50.0
    ) -> Dict[str, Any]:
        """
        Computes component scores and overall composite score.
        Score categories:
        80 - 100: Very Strong
        65 - 79:  Strong
        50 - 64:  Neutral
        35 - 49:  Weak
        0  - 34:  Very Weak
        """
        if df.empty or len(df) < 5:
            return {
                "composite_score": 50,
                "label": "Neutral",
                "components": {}
            }

        latest = df.iloc[-1]

        # 1. Technical Trend Score (SMA / EMA alignment)
        trend_score = 50.0
        close = latest["close"]
        sma20 = latest.get("sma_20", close)
        sma50 = latest.get("sma_50", close)
        sma200 = latest.get("sma_200", close)

        if close > sma20: trend_score += 15
        if close > sma50: trend_score += 15
        if close > sma200: trend_score += 20
        if sma20 > sma50: trend_score += 10
        trend_score = min(100.0, trend_score)

        # 2. Momentum Score (RSI + MACD + ROC)
        mom_score = 50.0
        rsi = latest.get("rsi_14", 50)
        macd_hist = latest.get("macd_hist", 0)
        roc = latest.get("roc_12", 0)

        if 50 <= rsi <= 70: mom_score += 20
        elif rsi > 70: mom_score += 10
        elif rsi < 30: mom_score -= 20

        if macd_hist > 0: mom_score += 15
        else: mom_score -= 15

        if roc > 0: mom_score += 15
        else: mom_score -= 15
        mom_score = max(0.0, min(100.0, mom_score))

        # 3. Volume Score
        vol_score = 50.0
        rel_vol = latest.get("relative_volume", 1.0)
        vol_chg = latest.get("volume_change", 0)

        if rel_vol >= 1.5: vol_score += 25
        elif rel_vol >= 1.0: vol_score += 10
        elif rel_vol < 0.7: vol_score -= 15
        vol_score = max(0.0, min(100.0, vol_score))

        # 4. Relative Strength Score (20-day return vs benchmark)
        ret_20 = latest.get("return_20d", 0)
        if pd.isna(ret_20): ret_20 = 0
        rs_score = max(0.0, min(100.0, 50.0 + (ret_20 * 200.0)))

        # 5. Volatility Score
        volat = latest.get("volatility_20d", 0.2)
        if pd.isna(volat): volat = 0.2
        # Moderate volatility preferred over extreme volatility
        volat_score = 70.0 if 0.12 <= volat <= 0.30 else (40.0 if volat > 0.40 else 55.0)

        # Market Regime Score normalized (score range -100 to +100 -> 0 to 100)
        reg_score_norm = max(0.0, min(100.0, (market_regime_score + 100) / 2.0))

        # Weighted Composite Score
        composite = (
            trend_score * 0.25 +
            mom_score * 0.25 +
            vol_score * 0.15 +
            rs_score * 0.15 +
            volat_score * 0.10 +
            reg_score_norm * 0.10
        )
        composite = round(max(0.0, min(100.0, composite)), 1)

        # Categorize label
        if composite >= 80: label = "Very Strong"
        elif composite >= 65: label = "Strong"
        elif composite >= 50: label = "Neutral"
        elif composite >= 35: label = "Weak"
        else: label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "components": {
                "technical_trend": round(trend_score, 1),
                "momentum": round(mom_score, 1),
                "volume": round(vol_score, 1),
                "relative_strength": round(rs_score, 1),
                "volatility": round(volat_score, 1),
                "market_regime": round(reg_score_norm, 1),
                "fundamental": round(fundamental_score, 1)
            }
        }
