"""
Daily Markdown & Machine-Readable JSON Report Generator.
Formats pipeline analysis results into factual daily markdown reports and stable JSON schemas.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates daily markdown and JSON outputs for the pipeline."""

    @staticmethod
    def generate_json_output(
        date_str: str,
        market_info: Dict[str, Any],
        sectors_info: List[Dict[str, Any]],
        stocks_info: List[Dict[str, Any]],
        quality_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generates stable machine-readable daily analysis JSON data.
        Schema: data/analysis/daily/YYYY-MM-DD.json
        """
        output = {
            "date": date_str,
            "market": market_info,
            "sectors": sectors_info,
            "stocks": stocks_info,
            "data_quality": quality_info,
        }
        return output

    @staticmethod
    def generate_markdown_report(
        date_str: str,
        market_info: Dict[str, Any],
        sectors_info: List[Dict[str, Any]],
        stocks_info: List[Dict[str, Any]],
        quality_info: Dict[str, Any],
        research_notes: Optional[List[str]] = None,
    ) -> str:
        """
        Generates human-readable Markdown report saved to reports/daily/YYYY-MM-DD.md.
        """
        breadth = market_info.get("breadth", {})
        regime = market_info.get("regime", "Neutral")

        # Top/Bottom Stocks
        sorted_stocks = sorted(stocks_info, key=lambda x: x.get("technical_score", 50.0), reverse=True)
        top_stocks = sorted_stocks[:5]
        bottom_stocks = sorted_stocks[-5:][::-1] if len(sorted_stocks) >= 5 else []

        # Technical events
        breakouts = [s["symbol"] for s in stocks_info if s.get("signals", {}).get("breakout")]
        breakdowns = [s["symbol"] for s in stocks_info if s.get("signals", {}).get("breakdown")]
        unusual_vol = [s["symbol"] for s in stocks_info if s.get("signals", {}).get("unusual_volume")]

        lines = [
            f"# Daily Indian Stock Market Analysis - {date_str}",
            "",
            "## Market Summary",
            f"- **Market Regime**: {regime} (Score: {market_info.get('regime_score', 0)})",
            f"- **NIFTY 50 Close**: {market_info.get('nifty_close', 'N/A')} ({market_info.get('nifty_return_1d', 0)*100:+.2f}%)",
            f"- **NIFTY Trend**: {market_info.get('nifty_trend', 'N/A')}",
            f"- **BANK NIFTY Trend**: {market_info.get('banknifty_trend', 'N/A')}",
            f"- **Market Volatility (20D Annualized)**: {market_info.get('nifty_volatility', 0)*100:.2f}%",
            f"- **Advance / Decline Ratio**: {breadth.get('advance_decline_ratio', 'N/A')} ({breadth.get('advances', 0)} Advances / {breadth.get('declines', 0)} Declines)",
            f"- **Stocks > 50 DMA**: {breadth.get('above_50_dma_pct', 'N/A')}%",
            "",
            "## Sector Performance & Rankings",
            "| Rank | Sector | Daily Return | Weekly Return | Relative Strength vs NIFTY | Momentum Score |",
            "| --- | --- | --- | --- | --- | --- |",
        ]

        for s in sectors_info:
            lines.append(
                f"| {s.get('rank', '-')} | {s.get('name', s.get('symbol'))} | {s.get('daily_return', 0):+.2f}% | "
                f"{s.get('weekly_return', 0):+.2f}% | {s.get('relative_strength_1d', 0):+.2f}% | {s.get('momentum_score', 50)} |"
            )

        lines.extend([
            "",
            "## Strongest Stocks (Highest Scores)",
            "| Symbol | Technical Score | Label | Trend State | 1D Return | 5D Directional Bias |",
            "| --- | --- | --- | --- | --- | --- |",
        ])

        for s in top_stocks:
            sig = s.get("signals", {})
            fwd = s.get("forward_probabilities", {}).get("5d", {})
            lines.append(
                f"| {s.get('symbol')} | {s.get('technical_score')} | {s.get('label')} | "
                f"{sig.get('trend_state', 'N/A')} | {s.get('daily_return', 0):+.2f}% | {fwd.get('directional_bias', 'Neutral')} ({fwd.get('confidence_score', 50)}%) |"
            )

        lines.extend([
            "",
            "## Weakest Stocks (Lowest Scores)",
            "| Symbol | Technical Score | Label | Trend State | 1D Return | 5D Directional Bias |",
            "| --- | --- | --- | --- | --- | --- |",
        ])

        for s in bottom_stocks:
            sig = s.get("signals", {})
            fwd = s.get("forward_probabilities", {}).get("5d", {})
            lines.append(
                f"| {s.get('symbol')} | {s.get('technical_score')} | {s.get('label')} | "
                f"{sig.get('trend_state', 'N/A')} | {s.get('daily_return', 0):+.2f}% | {fwd.get('directional_bias', 'Neutral')} ({fwd.get('confidence_score', 50)}%) |"
            )

        lines.extend([
            "",
            "## Key Technical Events",
            f"- **Breakouts (20-Day High)**: {', '.join(breakouts) if breakouts else 'None'}",
            f"- **Breakdowns (20-Day Low)**: {', '.join(breakdowns) if breakdowns else 'None'}",
            f"- **Unusual Volume Activity**: {', '.join(unusual_vol) if unusual_vol else 'None'}",
            "",
            "## Data Quality & Diagnostics",
            f"- **Processed Records**: {quality_info.get('records_processed', 0)}",
            f"- **Valid Records**: {quality_info.get('records_valid', 0)}",
            f"- **Warnings Count**: {quality_info.get('total_warnings', 0)}",
            f"- **Errors Count**: {quality_info.get('total_errors', 0)}",
            "",
            "## Research & Probabilistic Signals Note",
            "This report is produced by an automated empirical research engine. "
            "Forward directional biases and probabilities are statistical historical estimates, not guaranteed forecasts.",
        ])

        if research_notes:
            lines.extend(["", "### Additional Observations"] + [f"- {note}" for note in research_notes])

        return "\n".join(lines)
