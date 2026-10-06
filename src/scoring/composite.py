import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


class StockScorer:
    """Calculates a transparent, weighted 0-100 composite stock score."""

    DEFAULT_WEIGHTS = {
        "technical_trend": 0.25,
        "momentum": 0.20,
        "volume": 0.15,
        "relative_strength": 0.15,
        "volatility": 0.10,
        "market_regime": 0.10,
        "fundamental": 0.05
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = custom_weights if custom_weights else self.DEFAULT_WEIGHTS

    def calculate_stock_score(
        self,
        stock_df: pd.DataFrame,
        nifty_df: pd.DataFrame,
        regime_info: Dict[str, Any],
        fundamental_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates sub-scores (0-100) and composite score (0-100) for a stock.
        """
        if stock_df.empty or len(stock_df) < 5:
            return {
                "composite_score": 50,
                "label": "Neutral",
                "components": {k: 50 for k in self.weights.keys()}
            }

        latest = stock_df.iloc[-1]
        c_close = latest['close']

        # 1. Technical Trend Sub-score (0-100)
        trend_pts = 0
        sma_20 = latest.get('sma_20', c_close)
        sma_50 = latest.get('sma_50', c_close)
        sma_200 = latest.get('sma_200', c_close)

        if c_close > sma_20: trend_pts += 30
        if c_close > sma_50: trend_pts += 35
        if c_close > sma_200: trend_pts += 35
        trend_score = min(100, max(0, trend_pts))

        # 2. Momentum Sub-score (0-100)
        rsi = latest.get('rsi_14', 50)
        macd_hist = latest.get('macd_hist', 0)
        # Optimal RSI between 50 and 70
        if 50 <= rsi <= 70:
            rsi_pts = 85
        elif 40 <= rsi < 50 or 70 < rsi <= 80:
            rsi_pts = 65
        elif rsi > 80: # Overbought
            rsi_pts = 45
        else: # Oversold / weak
            rsi_pts = 30

        macd_pts = 75 if macd_hist > 0 else 35
        momentum_score = int(rsi_pts * 0.6 + macd_pts * 0.4)

        # 3. Volume Sub-score (0-100)
        rvol = latest.get('relative_volume', 1.0)
        if rvol >= 2.0:
            vol_score = 90
        elif rvol >= 1.2:
            vol_score = 75
        elif rvol >= 0.8:
            vol_score = 50
        else:
            vol_score = 30

        # 4. Relative Strength vs NIFTY Sub-score (0-100)
        if len(stock_df) >= 20 and len(nifty_df) >= 20:
            s_ret_20 = (c_close - stock_df['close'].iloc[-20]) / stock_df['close'].iloc[-20]
            n_ret_20 = (nifty_df['close'].iloc[-1] - nifty_df['close'].iloc[-20]) / nifty_df['close'].iloc[-20]
            excess_ret = s_ret_20 - n_ret_20
            if excess_ret >= 0.10:
                rs_score = 95
            elif excess_ret >= 0.03:
                rs_score = 80
            elif excess_ret >= -0.03:
                rs_score = 50
            else:
                rs_score = 25
        else:
            rs_score = 50

        # 5. Volatility Sub-score (0-100) - lower volatility in bull, or healthy ATR
        vol_regime = latest.get('volatility_regime', 'Normal')
        if vol_regime == 'Normal':
            vol_score = 70
        elif vol_regime == 'Low':
            vol_score = 85
        else: # High
            vol_score = 40

        # 6. Market Regime Sub-score (0-100)
        regime_str = regime_info.get('regime', 'Neutral')
        regime_map = {
            'Strong Bullish': 90,
            'Bullish': 75,
            'Neutral': 50,
            'Bearish': 30,
            'Strong Bearish': 10
        }
        regime_score = regime_map.get(regime_str, 50)

        # 7. Fundamental Sub-score (0-100)
        fund_score = fundamental_info.get('score', 50)

        components = {
            "technical_trend": trend_score,
            "momentum": momentum_score,
            "volume": vol_score,
            "relative_strength": rs_score,
            "volatility": vol_score,
            "market_regime": regime_score,
            "fundamental": fund_score
        }

        composite = sum(components[k] * self.weights.get(k, 0.0) for k in components.keys())
        composite_score = int(round(composite))

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
            "composite_score": max(0, min(100, composite_score)),
            "label": label,
            "components": components
        }
