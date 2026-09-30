import pandas as pd
import numpy as np
from typing import Dict, Any

class StockScorer:
    """
    Transparent composite scoring engine normalizing component scores (0-100) and overall stock score.
    Components:
    - Technical Trend Score
    - Momentum Score
    - Volume Score
    - Relative Strength Score
    - Volatility Score
    - Market Regime Score
    - Fundamental Score
    Labels:
    80-100: Very Strong
    65-79: Strong
    50-64: Neutral
    35-49: Weak
    0-34: Very Weak
    """

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.10,
            "fundamental": 0.05
        }

    def score_stock(
        self,
        df: pd.DataFrame,
        market_regime_score: float = 50.0,
        fundamental_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculates transparent composite stock score.
        """
        if df.empty or len(df) < 5:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "components": {}
            }

        latest = df.iloc[-1]
        c = latest.get('close', 0.0)

        # 1. Technical Trend Score (0-100)
        sma20 = latest.get('sma_20', c)
        sma50 = latest.get('sma_50', c)
        sma200 = latest.get('sma_200', c)

        trend_score = 50.0
        if c > sma20: trend_score += 15.0
        if c > sma50: trend_score += 15.0
        if c > sma200: trend_score += 20.0
        if sma20 > sma50 > sma200: trend_score += 10.0
        if c < sma20: trend_score -= 15.0
        if c < sma50: trend_score -= 15.0
        if c < sma200: trend_score -= 20.0
        trend_score = max(0.0, min(100.0, trend_score))

        # 2. Momentum Score (0-100)
        rsi = latest.get('rsi_14', 50.0)
        macd_hist = latest.get('macd_histogram', 0.0)
        ret_1d = latest.get('daily_return', 0.0)

        mom_score = 50.0
        # Optimal RSI window 50-65
        if 50 <= rsi <= 70:
            mom_score += 20.0
        elif rsi > 70:
            mom_score += 10.0 # slightly overbought risk
        elif rsi < 30:
            mom_score -= 20.0

        if macd_hist > 0:
            mom_score += 15.0
        else:
            mom_score -= 15.0

        if ret_1d > 0:
            mom_score += 15.0
        else:
            mom_score -= 15.0
        mom_score = max(0.0, min(100.0, mom_score))

        # 3. Volume Score (0-100)
        rel_vol = latest.get('relative_volume', 1.0)
        vol_score = 50.0
        if rel_vol > 2.0:
            vol_score += 30.0
        elif rel_vol > 1.2:
            vol_score += 15.0
        elif rel_vol < 0.7:
            vol_score -= 20.0
        vol_score = max(0.0, min(100.0, vol_score))

        # 4. Relative Strength Score (0-100)
        ret_1w = (c - df['close'].iloc[-5]) / df['close'].iloc[-5] if len(df) >= 5 else 0.0
        rs_score = 50.0 + (ret_1w * 300.0)
        rs_score = max(0.0, min(100.0, rs_score))

        # 5. Volatility Score (0-100)
        vol_20 = latest.get('volatility_20d', 0.20)
        volatility_score = 50.0
        if 0.10 <= vol_20 <= 0.30:
            volatility_score = 75.0
        elif vol_20 > 0.40:
            volatility_score = 30.0
        elif vol_20 < 0.10:
            volatility_score = 60.0

        # 6. Fundamental Score (0-100)
        fund_score = 50.0
        if fundamental_data and isinstance(fundamental_data, dict):
            pe = fundamental_data.get('pe_ratio')
            roe = fundamental_data.get('roe')
            profit_growth = fundamental_data.get('profit_growth')

            if pe and 0 < pe < 30: fund_score += 15.0
            if roe and roe > 0.15: fund_score += 20.0
            if profit_growth and profit_growth > 0.10: fund_score += 15.0
            fund_score = max(0.0, min(100.0, fund_score))

        # Composite score calculation
        components = {
            "technical_trend": round(trend_score, 2),
            "momentum": round(mom_score, 2),
            "volume": round(vol_score, 2),
            "relative_strength": round(rs_score, 2),
            "volatility": round(volatility_score, 2),
            "market_regime": round(market_regime_score, 2),
            "fundamental": round(fund_score, 2)
        }

        composite = sum(components[k] * self.weights.get(k, 0.0) for k in components)
        composite = round(max(0.0, min(100.0, composite)), 2)

        # Label assignment
        if composite >= 80.0:
            label = "Very Strong"
        elif composite >= 65.0:
            label = "Strong"
        elif composite >= 50.0:
            label = "Neutral"
        elif composite >= 35.0:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "components": components,
            "methodology": "Weighted linear combination of component scores (0-100)"
        }
