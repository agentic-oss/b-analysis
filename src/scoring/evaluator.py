"""
Transparent composite scoring system (0-100) for stock evaluation.
Breakdowns: Trend, Momentum, Volume, Relative Strength, Volatility, Market Regime, Sector.
"""
from typing import Dict, Any, Optional
import pandas as pd


class StockScorer:
    """Calculates transparent composite score and labels for individual stocks."""

    @staticmethod
    def score_stock(
        stock_df: pd.DataFrame,
        market_regime_data: Dict[str, Any],
        sector_data: Optional[Dict[str, Any]] = None,
        fundamental_data: Optional[Dict[str, Any]] = None,
        config_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        if stock_df.empty or len(stock_df) < 5:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "components": {},
            }

        latest = stock_df.iloc[-1]
        c = latest["Close"]

        # Default weights
        weights = {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.10,
            "sector": 0.05,
        }
        if config_weights:
            weights.update(config_weights)

        # 1. Technical Trend Score (0-100)
        trend_pts = 0
        if c > latest.get("sma_20", c):
            trend_pts += 25
        if c > latest.get("sma_50", c):
            trend_pts += 25
        if c > latest.get("sma_200", c):
            trend_pts += 25
        if latest.get("sma_50", 0) > latest.get("sma_200", 0):
            trend_pts += 25
        trend_score = trend_pts

        # 2. Momentum Score (0-100)
        rsi = latest.get("rsi_14", 50)
        if 45 <= rsi <= 65:
            rsi_score = 80
        elif 65 < rsi <= 75:
            rsi_score = 90
        elif 35 <= rsi < 45:
            rsi_score = 50
        elif rsi > 75:
            rsi_score = 40  # Overbought
        else:
            rsi_score = 20  # Oversold / Downtrend

        macd_hist = latest.get("macd_histogram", 0)
        macd_score = 80 if macd_hist > 0 else 30
        momentum_score = (rsi_score * 0.6) + (macd_score * 0.4)

        # 3. Volume Score (0-100)
        rel_vol = latest.get("relative_volume", 1.0)
        if rel_vol >= 2.0:
            vol_score = 90
        elif rel_vol >= 1.2:
            vol_score = 75
        elif rel_vol >= 0.8:
            vol_score = 50
        else:
            vol_score = 30

        # 4. Relative Strength Score (0-100)
        ret_20d = latest.get("return_20d", 0.0) or 0.0
        if ret_20d >= 0.10:
            rs_score = 90
        elif ret_20d >= 0.03:
            rs_score = 70
        elif ret_20d >= -0.03:
            rs_score = 50
        elif ret_20d >= -0.10:
            rs_score = 35
        else:
            rs_score = 15

        # 5. Volatility Score (0-100)
        ann_vol = latest.get("volatility_20d", 0.20) or 0.20
        if ann_vol <= 0.25:
            volatility_score = 80
        elif ann_vol <= 0.40:
            volatility_score = 60
        else:
            volatility_score = 40

        # 6. Market Regime Score
        regime_score = market_regime_data.get("score", 50.0)

        # 7. Sector Score
        sector_score = sector_data.get("momentum_score", 50.0) if sector_data else 50.0
        sector_score = min(max(sector_score + 50.0, 0.0), 100.0)  # Normalize around 50

        # Fundamental Score (optional inclusion if requested)
        fund_score = fundamental_data.get("score", 50.0) if fundamental_data else None

        components = {
            "technical_trend": round(trend_score, 2),
            "momentum": round(momentum_score, 2),
            "volume": round(vol_score, 2),
            "relative_strength": round(rs_score, 2),
            "volatility": round(volatility_score, 2),
            "market_regime": round(regime_score, 2),
            "sector": round(sector_score, 2),
        }
        if fund_score is not None:
            components["fundamental"] = round(fund_score, 2)

        composite = (
            (trend_score * weights["technical_trend"])
            + (momentum_score * weights["momentum"])
            + (vol_score * weights["volume"])
            + (rs_score * weights["relative_strength"])
            + (volatility_score * weights["volatility"])
            + (regime_score * weights["market_regime"])
            + (sector_score * weights["sector"])
        )
        composite = round(composite, 2)

        # Assign score label
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
            "components": components,
            "weights": weights,
        }
