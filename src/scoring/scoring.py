import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class StockScorer:
    """
    Computes transparent, composite 0-100 stock score based on weighted sub-scores:
    - Technical Trend Score (25%)
    - Momentum Score (20%)
    - Volume Score (15%)
    - Relative Strength Score (15%)
    - Market Regime Score (10%)
    - Sector Score (10%)
    - Fundamental Score (5%)

    Score Labels:
    - 80-100: Very Strong
    - 65-79: Strong
    - 50-64: Neutral
    - 35-49: Weak
    - 0-34: Very Weak
    """

    @staticmethod
    def calculate_score(
        stock_df: pd.DataFrame,
        nifty_df: pd.DataFrame,
        regime_info: Dict[str, Any],
        sector_info: Optional[Dict[str, Any]] = None,
        fundamental_info: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:

        default_weights = {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "market_regime": 0.10,
            "sector": 0.10,
            "fundamental": 0.05
        }
        if weights:
            default_weights.update(weights)

        if stock_df.empty or len(stock_df) == 0:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "components": {}
            }

        last = stock_df.iloc[-1]
        close = last['close']

        # 1. Technical Trend Score (0-100)
        # Based on position relative to SMAs and EMAs
        trend_pts = 0
        max_trend_pts = 5
        if close > last.get('sma_20', close): trend_pts += 1
        if close > last.get('sma_50', close): trend_pts += 1
        if close > last.get('sma_200', close): trend_pts += 1
        if close > last.get('ema_20', close): trend_pts += 1
        if close > last.get('ema_50', close): trend_pts += 1
        tech_score = (trend_pts / max_trend_pts) * 100.0

        # 2. Momentum Score (0-100)
        rsi = float(last.get('rsi_14', 50.0))
        macd_hist = float(last.get('macd_hist', 0.0))
        roc = float(last.get('roc_10', 0.0))
        # Optimal RSI between 50 and 70
        rsi_pts = max(0.0, 100.0 - abs(rsi - 60) * 2)
        macd_pts = 75.0 if macd_hist > 0 else 25.0
        roc_pts = min(100.0, max(0.0, (roc + 10) * 5))
        mom_score = rsi_pts * 0.4 + macd_pts * 0.3 + roc_pts * 0.3

        # 3. Volume Score (0-100)
        rvol = float(last.get('relative_volume', 1.0))
        vol_score = min(100.0, max(0.0, rvol * 50.0))

        # 4. Relative Strength Score (0-100) vs NIFTY
        nifty_ret = nifty_df.iloc[-1].get('return_1d', 0.0) if not nifty_df.empty else 0.0
        stock_ret = float(last.get('return_1d', 0.0))
        diff_pct = (stock_ret - nifty_ret) * 100
        rs_score = min(100.0, max(0.0, 50.0 + diff_pct * 10))

        # 5. Market Regime Score (0-100)
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 75.0,
            "Neutral": 50.0,
            "Bearish": 30.0,
            "Strong Bearish": 10.0
        }
        regime_score = regime_map.get(regime_info.get("regime", "Neutral"), 50.0)

        # 6. Sector Score (0-100)
        sec_score = 50.0
        if sector_info:
            sec_score = float(sector_info.get("momentum_score", 50.0))

        # 7. Fundamental Score (0-100)
        fund_score = 50.0
        if fundamental_info and fundamental_info.get("market_cap"):
            pts = 50.0
            roe = fundamental_info.get("roe")
            pe = fundamental_info.get("pe_ratio")
            if roe and roe > 0.15: pts += 20.0
            if pe and 0 < pe < 30: pts += 20.0
            if fundamental_info.get("debt_to_equity") and fundamental_info.get("debt_to_equity") < 1.0: pts += 10.0
            fund_score = min(100.0, pts)

        components = {
            "technical_trend": round(tech_score, 2),
            "momentum": round(mom_score, 2),
            "volume": round(vol_score, 2),
            "relative_strength": round(rs_score, 2),
            "market_regime": round(regime_score, 2),
            "sector": round(sec_score, 2),
            "fundamental": round(fund_score, 2)
        }

        composite = (
            components["technical_trend"] * default_weights["technical_trend"] +
            components["momentum"] * default_weights["momentum"] +
            components["volume"] * default_weights["volume"] +
            components["relative_strength"] * default_weights["relative_strength"] +
            components["market_regime"] * default_weights["market_regime"] +
            components["sector"] * default_weights["sector"] +
            components["fundamental"] * default_weights["fundamental"]
        )
        composite = round(composite, 2)

        if composite >= 80: label = "Very Strong"
        elif composite >= 65: label = "Strong"
        elif composite >= 50: label = "Neutral"
        elif composite >= 35: label = "Weak"
        else: label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "components": components
        }
