import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class StockScorer:
    """
    Transparent composite scoring system (0-100):
    Components: Technical Trend, Momentum, Volume, Relative Strength, Market Regime, Sector.
    Labels: 80-100 (Very Strong), 65-79 (Strong), 50-64 (Neutral), 35-49 (Weak), 0-34 (Very Weak).
    """

    @staticmethod
    def calculate_score(
        stock_latest: Dict[str, Any],
        market_regime: Dict[str, Any],
        sector_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        close = stock_latest.get("close", 0)
        sma20 = stock_latest.get("sma_20", close)
        sma50 = stock_latest.get("sma_50", close)
        sma200 = stock_latest.get("sma_200", close)

        # 1. Technical Trend Score (0 - 100)
        trend_pts = 0
        if close > sma20:
            trend_pts += 30
        if close > sma50:
            trend_pts += 35
        if close > sma200:
            trend_pts += 35
        tech_score = trend_pts

        # 2. Momentum Score (0 - 100)
        rsi = stock_latest.get("rsi_14", 50)
        macd = stock_latest.get("macd", 0)
        macd_sig = stock_latest.get("macd_signal", 0)

        mom_pts = 0
        if 40 <= rsi <= 70:
            mom_pts += 50
        elif rsi > 70:
            mom_pts += 30
        else:
            mom_pts += 10

        if macd > macd_sig:
            mom_pts += 50
        momentum_score = mom_pts

        # 3. Volume Score (0 - 100)
        rvol = stock_latest.get("relative_volume", 1.0)
        vol_score = min(100, int(rvol * 50))

        # 4. Relative Strength Score (0 - 100)
        ret_20d = stock_latest.get("return_1d", 0.0) * 20  # proxy 20d estimate if not explicit
        if "dist_52w_high" in stock_latest:
            dist_high = stock_latest.get("dist_52w_high", -20)
            rs_score = max(0, min(100, int(100 + dist_high * 2)))
        else:
            rs_score = 50

        # 5. Market / Sector Score (0 - 100)
        m_cls = market_regime.get("classification", "Neutral")
        m_map = {"Strong Bullish": 100, "Bullish": 80, "Neutral": 50, "Bearish": 30, "Strong Bearish": 0}
        m_score = m_map.get(m_cls, 50)

        s_rank = sector_info.get("rank", 5)
        s_score = max(0, 100 - (s_rank - 1) * 10)

        mkt_sec_score = int(m_score * 0.5 + s_score * 0.5)

        # Weighted Total Score
        total_score = round(
            tech_score * 0.35 +
            momentum_score * 0.25 +
            vol_score * 0.15 +
            rs_score * 0.15 +
            mkt_sec_score * 0.10,
            2
        )

        if total_score >= 80:
            label = "Very Strong"
        elif total_score >= 65:
            label = "Strong"
        elif total_score >= 50:
            label = "Neutral"
        elif total_score >= 35:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "symbol": stock_latest.get("ticker", "UNKNOWN"),
            "total_score": total_score,
            "label": label,
            "components": {
                "technical_trend_score": tech_score,
                "momentum_score": momentum_score,
                "volume_score": vol_score,
                "relative_strength_score": rs_score,
                "market_sector_score": mkt_sec_score,
            }
        }
