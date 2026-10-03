import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

class StockScorer:
    """Calculates a composite transparent 0-100 score for a stock."""

    @staticmethod
    def calculate_score(stock_df: pd.DataFrame, market_regime_score: float = 50, fundamental_score: float = 50) -> Dict[str, Any]:
        if stock_df.empty or len(stock_df) < 5:
            return {
                "composite_score": 50,
                "label": "Neutral",
                "components": {}
            }

        latest = stock_df.iloc[-1]

        # 1. Technical Trend Score (0-100)
        c = latest["close"]
        sma20 = latest.get("sma_20", c)
        sma50 = latest.get("sma_50", c)
        sma200 = latest.get("sma_200", c)

        tech_trend = 50
        if c > sma20: tech_trend += 15
        if c > sma50: tech_trend += 15
        if c > sma200: tech_trend += 20
        tech_trend = max(0, min(100, tech_trend))

        # 2. Momentum Score (0-100)
        rsi = latest.get("rsi_14", 50)
        macd_hist = latest.get("macd_histogram", 0)

        momentum = 50
        if 50 <= rsi <= 70: momentum += 20
        elif rsi > 70: momentum += 10
        elif rsi < 30: momentum -= 20

        if macd_hist > 0: momentum += 20
        elif macd_hist < 0: momentum -= 20
        momentum = max(0, min(100, momentum))

        # 3. Volume Score (0-100)
        rel_vol = latest.get("relative_volume", 1.0)
        vol = 50
        if rel_vol >= 1.5: vol = 80
        elif rel_vol >= 1.0: vol = 60
        else: vol = 40

        # 4. Relative Strength Score (0-100)
        ret_1d = latest.get("return_1d", 0)
        rs_score = 50
        if ret_1d > 0.01: rs_score = 75
        elif ret_1d < -0.01: rs_score = 25

        # Weighted Composite Score
        weights = {
            "technical_trend": 0.25,
            "momentum": 0.25,
            "volume": 0.15,
            "relative_strength": 0.15,
            "market_regime": 0.10,
            "fundamental": 0.10
        }

        composite = (
            tech_trend * weights["technical_trend"] +
            momentum * weights["momentum"] +
            vol * weights["volume"] +
            rs_score * weights["relative_strength"] +
            market_regime_score * weights["market_regime"] +
            fundamental_score * weights["fundamental"]
        )

        composite = round(composite, 1)

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
            "components": {
                "technical_trend": tech_trend,
                "momentum": momentum,
                "volume": vol,
                "relative_strength": rs_score,
                "market_regime": market_regime_score,
                "fundamental": fundamental_score
            }
        }
