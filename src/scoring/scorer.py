"""Composite Stock Scoring Engine."""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class StockScorer:
    """Calculates transparent, componentized 0-100 stock composite scores and labels."""

    DEFAULT_WEIGHTS = {
        "technical_trend": 0.25,
        "momentum": 0.20,
        "volume": 0.15,
        "relative_strength": 0.15,
        "volatility": 0.10,
        "market_regime": 0.10,
        "fundamentals": 0.05
    }

    @staticmethod
    def calculate_stock_score(
        stock_df: pd.DataFrame,
        nifty_df: Optional[pd.DataFrame] = None,
        market_regime_data: Optional[Dict[str, Any]] = None,
        sector_data: Optional[Dict[str, Any]] = None,
        fundamental_data: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Compute transparent 0-100 composite score and component scores.

        Returns score breakdown and overall qualitative label.
        """
        if stock_df.empty or len(stock_df) < 5:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "components": {}
            }

        w = weights or StockScorer.DEFAULT_WEIGHTS
        latest = stock_df.iloc[-1]
        close = float(latest["Close"])

        # 1. Technical Trend Score (0-100)
        trend_score = 50.0
        sma20 = float(latest.get("sma_20", close))
        sma50 = float(latest.get("sma_50", close))
        sma200 = float(latest.get("sma_200", close))

        if close > sma20:
            trend_score += 15.0
        else:
            trend_score -= 15.0

        if close > sma50:
            trend_score += 15.0
        else:
            trend_score -= 15.0

        if close > sma200:
            trend_score += 20.0
        else:
            trend_score -= 20.0

        if bool(latest.get("golden_cross", False)):
            trend_score += 10.0
        if bool(latest.get("breakout", False)):
            trend_score += 10.0

        trend_score = max(0.0, min(100.0, trend_score))

        # 2. Momentum Score (0-100)
        momentum_score = 50.0
        rsi = float(latest.get("rsi_14", 50.0))
        stoch_rsi = float(latest.get("stoch_rsi", 50.0))
        macd_hist = float(latest.get("macd_hist", 0.0))

        # RSI contribution
        if 50.0 <= rsi <= 70.0:
            momentum_score += 20.0
        elif rsi > 70.0:
            momentum_score += 10.0  # Overbought caution
        elif rsi < 30.0:
            momentum_score -= 20.0
        else:
            momentum_score -= 10.0

        # MACD histogram
        if macd_hist > 0:
            momentum_score += 15.0
        else:
            momentum_score -= 15.0

        # Stoch RSI
        if stoch_rsi > 50.0:
            momentum_score += 15.0
        else:
            momentum_score -= 15.0

        momentum_score = max(0.0, min(100.0, momentum_score))

        # 3. Volume Score (0-100)
        volume_score = 50.0
        rel_vol = float(latest.get("relative_volume", 1.0))
        if rel_vol > 2.0:
            volume_score += 30.0
        elif rel_vol > 1.2:
            volume_score += 15.0
        elif rel_vol < 0.7:
            volume_score -= 15.0

        if bool(latest.get("unusual_volume", False)):
            volume_score += 20.0

        volume_score = max(0.0, min(100.0, volume_score))

        # 4. Relative Strength Score vs NIFTY (0-100)
        rs_score = 50.0
        if nifty_df is not None and not nifty_df.empty and len(nifty_df) >= 20:
            nifty_latest = nifty_df.iloc[-1]
            nifty_ret20 = float(nifty_latest.get("return_1d", 0.0)) # Fallback
            if len(nifty_df) >= 20 and len(stock_df) >= 20:
                s_ret20 = ((close - float(stock_df.iloc[-20]["Close"])) / float(stock_df.iloc[-20]["Close"])) * 100.0
                n_ret20 = ((float(nifty_latest["Close"]) - float(nifty_df.iloc[-20]["Close"])) / float(nifty_df.iloc[-20]["Close"])) * 100.0
                excess_ret = s_ret20 - n_ret20
                rs_score = max(0.0, min(100.0, 50.0 + (excess_ret * 2.0)))

        # 5. Volatility Score (0-100)
        volatility_score = 50.0
        vol_regime = str(latest.get("volatility_regime", "Normal"))
        if vol_regime == "Low":
            volatility_score = 70.0
        elif vol_regime == "High":
            volatility_score = 30.0

        # 6. Market Regime Score (0-100)
        regime_score = float(market_regime_data.get("regime_score", 50.0)) if market_regime_data else 50.0

        # 7. Sector Score (0-100)
        sector_score = 50.0
        if sector_data:
            rank = sector_data.get("rank", 5)
            # Map top sectors higher
            sector_score = max(10.0, min(100.0, 100.0 - (rank - 1) * 10.0))

        # 8. Fundamental Score (0-100)
        fundamental_score = 50.0
        if fundamental_data:
            from src.fundamentals.fundamentals import FundamentalAnalyzer
            fundamental_score = FundamentalAnalyzer.calculate_fundamental_score(fundamental_data)

        # Calculate weighted composite score
        component_scores = {
            "technical_trend": round(trend_score, 1),
            "momentum": round(momentum_score, 1),
            "volume": round(volume_score, 1),
            "relative_strength": round(rs_score, 1),
            "volatility": round(volatility_score, 1),
            "market_regime": round(regime_score, 1),
            "sector": round(sector_score, 1),
            "fundamentals": round(fundamental_score, 1)
        }

        total_weight = sum(w.values())
        weighted_sum = (
            component_scores["technical_trend"] * w.get("technical_trend", 0.25) +
            component_scores["momentum"] * w.get("momentum", 0.20) +
            component_scores["volume"] * w.get("volume", 0.15) +
            component_scores["relative_strength"] * w.get("relative_strength", 0.15) +
            component_scores["volatility"] * w.get("volatility", 0.10) +
            component_scores["market_regime"] * w.get("market_regime", 0.10) +
            component_scores["fundamentals"] * w.get("fundamentals", 0.05)
        )

        composite_score = round(weighted_sum / total_weight, 1)

        # Map to label
        if composite_score >= 80.0:
            label = "Very Strong"
        elif composite_score >= 65.0:
            label = "Strong"
        elif composite_score >= 50.0:
            label = "Neutral"
        elif composite_score >= 35.0:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "composite_score": composite_score,
            "label": label,
            "components": component_scores
        }
