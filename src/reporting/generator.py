"""
Daily Report Generator module.
Produces human-readable Markdown reports (reports/daily/YYYY-MM-DD.md)
and validates machine-readable JSON outputs (data/analysis/daily/YYYY-MM-DD.json).
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates research-oriented daily market reports.
    """

    @staticmethod
    def generate_markdown_report(
        run_date: str,
        market_regime: Dict[str, Any],
        sector_ranks: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]],
        quality_summary: Dict[str, Any]
    ) -> str:
        """
        Creates structured Markdown daily report.
        """
        lines = []
        lines.append(f"# Daily Indian Stock Market Research Report — {run_date}")
        lines.append("")
        lines.append("*Automated Analytics & Quantitative Research Engine*")
        lines.append("")

        # 1. Market Summary
        lines.append("## 1. Market Summary & Regime")
        regime = market_regime.get("market_regime", "Neutral")
        conf = market_regime.get("confidence", 50)
        details = market_regime.get("details", {})

        lines.append(f"- **Market Regime Classification:** **{regime}** (Confidence: {conf}%)")
        lines.append(f"- **NIFTY 50 Close:** `{details.get('nifty_close', 'N/A')}` | **RSI (14):** `{details.get('nifty_rsi_14', 'N/A')}`")
        lines.append(f"- **Market Breadth:** Advance/Decline Ratio `{details.get('advance_decline_ratio', 'N/A')}` ({details.get('advances', 0)} Advances / {details.get('declines', 0)} Declines)")
        lines.append(f"- **DMA Position:** `{details.get('pct_above_50dma', 'N/A')}%` stocks above 50 DMA, `{details.get('pct_above_200dma', 'N/A')}%` above 200 DMA.")
        lines.append("")

        # 2. Sector Performance
        lines.append("## 2. Sector Performance & Rotation")
        lines.append("| Rank | Sector Index | Daily Return | Weekly Return | Relative Strength (vs NIFTY) | Momentum Score |")
        lines.append("|---|---|---|---|---|---|")
        for sec in sector_ranks:
            lines.append(f"| {sec.get('rank', '-')} | {sec.get('name', sec.get('symbol'))} | {sec.get('daily_return', 0.0)}% | {sec.get('weekly_return', 0.0)}% | {sec.get('relative_strength_1d', 0.0)}% | {sec.get('momentum_score', 50.0)} |")
        lines.append("")

        # Sort stocks by composite score
        sorted_stocks = sorted(stock_analyses, key=lambda x: x.get("composite_score", 0), reverse=True)

        # 3. Strong & Weak Stocks
        lines.append("## 3. Stock Scoring Highlights")
        lines.append("### Top Strongest Stocks (Highest Scores)")
        lines.append("| Ticker | Score | Label | Technical Trend | Momentum | Volume | Sector Score |")
        lines.append("|---|---|---|---|---|---|---|")
        for s in sorted_stocks[:5]:
            c = s.get("score_components", {})
            lines.append(f"| **{s.get('symbol')}** | **{s.get('composite_score')}** | {s.get('score_label')} | {c.get('technical_trend_score')} | {c.get('momentum_score')} | {c.get('volume_score')} | {c.get('sector_score')} |")

        lines.append("")
        lines.append("### Top Weakest Stocks (Lowest Scores)")
        lines.append("| Ticker | Score | Label | Technical Trend | Momentum | Volume | Sector Score |")
        lines.append("|---|---|---|---|---|---|---|")
        for s in sorted_stocks[-5:]:
            c = s.get("score_components", {})
            lines.append(f"| **{s.get('symbol')}** | **{s.get('composite_score')}** | {s.get('score_label')} | {c.get('technical_trend_score')} | {c.get('momentum_score')} | {c.get('volume_score')} | {c.get('sector_score')} |")
        lines.append("")

        # 4. Technical Events & Unusual Volume
        breakouts = [s["symbol"] for s in sorted_stocks if s.get("technical_events", {}).get("breakout_20d")]
        breakdowns = [s["symbol"] for s in sorted_stocks if s.get("technical_events", {}).get("breakdown_20d")]
        unusual_vol = [s["symbol"] for s in sorted_stocks if s.get("technical_events", {}).get("unusual_volume")]

        lines.append("## 4. Technical Events & Volume Alerts")
        lines.append(f"- **20-Day Breakouts:** {', '.join(breakouts) if breakouts else 'None detected'}")
        lines.append(f"- **20-Day Breakdowns:** {', '.join(breakdowns) if breakdowns else 'None detected'}")
        lines.append(f"- **Unusual Volume Surge (>2.5x 20DMA):** {', '.join(unusual_vol) if unusual_vol else 'None detected'}")
        lines.append("")

        # 5. Probabilistic Forward Movement Signals
        lines.append("## 5. Sample Probabilistic Forward Movements (5-Day Horizon)")
        lines.append("| Ticker | Directional Bias | Confidence Score | Implied Bullish Prob | Historical Match Win Rate |")
        lines.append("|---|---|---|---|---|")
        for s in sorted_stocks[:5]:
            fwd_5d = s.get("forward_signals", {}).get("5d", {})
            lines.append(f"| {s.get('symbol')} | {fwd_5d.get('directional_bias', 'Neutral')} | {fwd_5d.get('confidence_score', 50)} | {fwd_5d.get('implied_bullish_probability_pct', 50.0)}% | {fwd_5d.get('historical_win_rate_pct', 50.0)}% |")
        lines.append("")

        # 6. Data Quality & Diagnostics
        lines.append("## 6. Data Quality Diagnostics")
        lines.append(f"- **Total Stocks Processed:** {quality_summary.get('records_processed', 0)}")
        lines.append(f"- **Valid Observations:** {quality_summary.get('records_valid', 0)}")
        lines.append(f"- **Data Warnings:** {quality_summary.get('warnings_count', 0)}")
        lines.append(f"- **Data Errors:** {quality_summary.get('errors_count', 0)}")
        lines.append("")

        # 7. Research Notes & Disclaimer
        lines.append("## 7. Research Notes & Safeguards")
        lines.append("- All forward-looking directional bias metrics are probabilistic empirical signals derived from historical analogues and component scores.")
        lines.append("- No outputs constitute guaranteed forecasts or financial trading advice.")
        lines.append("- Historical backtests account for transaction slippage and execution costs.")

        return "\n".join(lines)
