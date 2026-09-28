import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class CompositeScorer:
    """Calculates transparent multi-component composite stock scores normalized to 0-100."""

    @staticmethod
    def calculate_stock_score(
        df_stock: pd.DataFrame,
        market_regime_info: Dict[str, Any],
        sector_info: Optional[Dict[str, Any]],
        fundamental_info: Optional[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates individual component scores (0-100) and weighted total score.
        Labels:
            80-100: Very Strong
            65-79: Strong
            50-64: Neutral
            35-49: Weak
            0-34: Very Weak
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

        if df_stock.empty or len(df_stock) < 5:
            return {
                "total_score": 50.0,
                "label": "Neutral",
                "components": {}
            }

        latest = df_stock.iloc[-1]
        close = float(latest['close'])

        # 1. Technical Trend Score
        sma20 = float(latest.get('sma_20', close))
        sma50 = float(latest.get('sma_50', close))
        sma200 = float(latest.get('sma_200', close))
        ema20 = float(latest.get('ema_20', close))

        tech_points = 0
        if close > sma20: tech_points += 25
        if close > sma50: tech_points += 25
        if close > sma200: tech_points += 25
        if ema20 > sma50: tech_points += 25
        tech_score = float(tech_points)

        # 2. Momentum Score
        rsi = float(latest.get('rsi_14', 50.0))
        macd = float(latest.get('macd', 0.0))
        macd_sig = float(latest.get('macd_signal', 0.0))
        roc = float(latest.get('roc_10', 0.0))

        mom_score = 50.0
        if 50 <= rsi <= 70: mom_score += 20
        elif rsi > 70: mom_score += 10
        elif rsi < 30: mom_score -= 20
        else: mom_score -= 10

        if macd > macd_sig: mom_score += 15
        else: mom_score -= 15

        if roc > 0: mom_score += 15
        else: mom_score -= 15
        mom_score = max(0.0, min(100.0, mom_score))

        # 3. Volume Score
        rel_vol = float(latest.get('relative_volume', 1.0))
        vol_score = 50.0
        if rel_vol >= 2.0: vol_score = 90.0
        elif rel_vol >= 1.2: vol_score = 75.0
        elif rel_vol >= 0.8: vol_score = 50.0
        else: vol_score = 30.0

        # 4. Relative Strength Score
        ret_1d = float(latest.get('return_1d', 0.0))
        nifty_vol = float(market_regime_info.get('nifty_volatility_20d', 0.15))
        # Estimate stock RS vs market
        dist_52w = float(latest.get('dist_52w_high', -0.10))
        rs_score = max(0.0, min(100.0, 50.0 + (dist_52w * 100.0) + (ret_1d * 200.0)))

        # 5. Volatility Score
        vol_20d = float(latest.get('volatility_20d', 0.20))
        if vol_20d < 0.20: vol_score_val = 80.0
        elif vol_20d < 0.35: vol_score_val = 60.0
        elif vol_20d < 0.50: vol_score_val = 40.0
        else: vol_score_val = 20.0

        # 6. Market Regime Score
        regime = market_regime_info.get("market_regime", "Neutral")
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 75.0,
            "Neutral": 50.0,
            "Bearish": 30.0,
            "Strong Bearish": 10.0
        }
        regime_score = regime_map.get(regime, 50.0)

        # 7. Fundamental Score
        fund_score = float(fundamental_info.get("fundamental_score", 50.0)) if fundamental_info else 50.0

        components = {
            "technical_trend": round(tech_score, 2),
            "momentum": round(mom_score, 2),
            "volume": round(vol_score, 2),
            "relative_strength": round(rs_score, 2),
            "volatility": round(vol_score_val, 2),
            "market_regime": round(regime_score, 2),
            "fundamental": round(fund_score, 2)
        }

        total_score = sum(components[k] * weights.get(k, 0.0) for k in components)
        total_score = round(max(0.0, min(100.0, total_score)), 2)

        label = "Very Strong" if total_score >= 80 else ("Strong" if total_score >= 65 else ("Neutral" if total_score >= 50 else ("Weak" if total_score >= 35 else "Very Weak")))

        return {
            "symbol": latest.get('symbol', 'UNKNOWN'),
            "total_score": total_score,
            "label": label,
            "components": components,
            "weights": weights
        }
