"""Daily Report Generation Engine."""

import json
import logging
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates human-readable Markdown research reports and machine-readable JSON exports."""

    @staticmethod
    def generate_markdown_report(
        date_str: str,
        market_regime: Dict[str, Any],
        sectors: List[Dict[str, Any]],
        stocks_analysis: List[Dict[str, Any]],
        quality_summary: Dict[str, Any]
    ) -> str:
        """Construct comprehensive Markdown research report for the trading day."""
        breadth = market_regime.get("breadth", {})
        regime_label = market_regime.get("regime", "Neutral")
        regime_score = market_regime.get("regime_score", 50.0)

        # Sort stocks by score
        sorted_stocks = sorted(stocks_analysis, key=lambda x: x.get("composite_score", 0), reverse=True)
        top_stocks = sorted_stocks[:5]
        bottom_stocks = sorted_stocks[-5:] if len(sorted_stocks) >= 5 else []

        # Technical events
        breakouts = [s["symbol"] for s in stocks_analysis if s.get("technical_summary", {}).get("breakout", False)]
        breakdowns = [s["symbol"] for s in stocks_analysis if s.get("technical_summary", {}).get("breakdown", False)]
        unusual_vol = [s["symbol"] for s in stocks_analysis if s.get("technical_summary", {}).get("unusual_volume", False)]

        # Top sector leaders & laggards
        top_sectors = sectors[:3]
        bottom_sectors = sectors[-3:] if len(sectors) >= 3 else []

        md = []
        md.append(f"# Daily Indian Stock Market Analysis & Research Report: {date_str}\n")
        md.append("## Executive Summary\n")
        md.append(f"- **Market Regime:** `{regime_label}` (Regime Score: {regime_score}/100)")
        md.append(f"- **NIFTY Close:** {market_regime.get('nifty_close', 'N/A')}")
        md.append(f"- **Advance/Decline Ratio:** {breadth.get('advance_decline_ratio', 'N/A')}")
        md.append(f"- **Market Breadth (% Stocks > 50DMA):** {breadth.get('pct_above_50dma', 'N/A')}%\n")

        # Market Regime
        md.append("## 1. Market Regime Analysis")
        md.append("| Metric | Value |")
        md.append("| --- | --- |")
        md.append(f"| Regime Classification | **{regime_label}** |")
        md.append(f"| Composite Regime Score | {regime_score} / 100 |")
        md.append(f"| % Above 20 DMA | {breadth.get('pct_above_20dma', 'N/A')}% |")
        md.append(f"| % Above 50 DMA | {breadth.get('pct_above_50dma', 'N/A')}% |")
        md.append(f"| % Above 200 DMA | {breadth.get('pct_above_200dma', 'N/A')}% |")
        md.append(f"| New Breakouts / Highs | {breadth.get('new_highs', 0)} |")
        md.append(f"| New Breakdowns / Lows | {breadth.get('new_lows', 0)} |\n")

        # Sector Performance
        md.append("## 2. Sector Performance & Rankings")
        md.append("| Rank | Sector | Daily Return | Weekly Return | Relative Strength vs NIFTY | Momentum Score |")
        md.append("| --- | --- | --- | --- | --- | --- |")
        for s in sectors:
            md.append(f"| {s.get('rank', '-')} | **{s.get('sector')}** | {s.get('daily_return')}% | {s.get('weekly_return')}% | {s.get('relative_strength')} | {s.get('momentum_score')} |")
        md.append("")

        # Strongest & Weakest Stocks
        md.append("## 3. Stock Scoring Rankings")
        md.append("### Highest Scoring Stocks (Leaders)")
        md.append("| Symbol | Composite Score | Label | Technical Trend | Momentum | Volatility | RS vs NIFTY |")
        md.append("| --- | --- | --- | --- | --- | --- | --- |")
        for s in top_stocks:
            comp = s.get("components", {})
            md.append(f"| **{s.get('symbol')}** | **{s.get('composite_score')}** | {s.get('label')} | {comp.get('technical_trend')} | {comp.get('momentum')} | {comp.get('volatility')} | {comp.get('relative_strength')} |")
        md.append("")

        md.append("### Lowest Scoring Stocks (Laggards)")
        md.append("| Symbol | Composite Score | Label | Technical Trend | Momentum | Volatility | RS vs NIFTY |")
        md.append("| --- | --- | --- | --- | --- | --- | --- |")
        for s in bottom_stocks:
            comp = s.get("components", {})
            md.append(f"| **{s.get('symbol')}** | **{s.get('composite_score')}** | {s.get('label')} | {comp.get('technical_trend')} | {comp.get('momentum')} | {comp.get('volatility')} | {comp.get('relative_strength')} |")
        md.append("")

        # Technical Signals
        md.append("## 4. Key Technical Signals & Screeners")
        md.append(f"- **Breakout Stocks:** {', '.join(breakouts) if breakouts else 'None detected'}")
        md.append(f"- **Breakdown Stocks:** {', '.join(breakdowns) if breakdowns else 'None detected'}")
        md.append(f"- **Unusual Volume Surge:** {', '.join(unusual_vol) if unusual_vol else 'None detected'}\n")

        # Forward Probabilities Sample
        md.append("## 5. Historical Analogue Forward Probabilities (Sample)")
        md.append("| Symbol | 1D Bias | 5D Bias | 20D Bias | Historical Matches | 5D Win Rate % | 5D Avg Return % |")
        md.append("| --- | --- | --- | --- | --- | --- | --- |")
        for s in top_stocks[:3]:
            fwds = s.get("forward_probabilities", {})
            analogues = s.get("historical_analogues", {})
            f1 = fwds.get("1d", {}).get("directional_bias", "Neutral")
            f5 = fwds.get("5d", {}).get("directional_bias", "Neutral")
            f20 = fwds.get("20d", {}).get("directional_bias", "Neutral")
            matches = analogues.get("num_matches", 0)
            a5 = analogues.get("horizons", {}).get("5d", {})
            md.append(f"| **{s.get('symbol')}** | {f1} | {f5} | {f20} | {matches} | {a5.get('win_rate_pct', 0)}% | {a5.get('avg_forward_return', 0)}% |")
        md.append("")

        # Data Quality Summary
        md.append("## 6. Data Quality & Pipeline Diagnostics")
        md.append(f"- **Records Processed:** {quality_summary.get('records_processed', 0)}")
        md.append(f"- **Valid Records:** {quality_summary.get('records_valid', 0)}")
        md.append(f"- **Data Quality Warnings:** {len(quality_summary.get('warnings', []))}")
        md.append(f"- **Data Quality Errors:** {len(quality_summary.get('errors', []))}\n")

        # Research Notes
        md.append("## 7. Disclaimers & Research Methodology")
        md.append("> **Disclaimer:** All generated signals, forward probabilities, and composite scores are empirical research outputs and probabilistic statistical estimations. They do NOT constitute guaranteed price predictions or financial investment advice.")

        return "\n".join(md)

    @staticmethod
    def generate_json_output(
        date_str: str,
        market_regime: Dict[str, Any],
        sectors: List[Dict[str, Any]],
        stocks_analysis: List[Dict[str, Any]],
        quality_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construct machine-readable JSON structure adhering to stable schema."""
        return {
            "date": date_str,
            "market": market_regime,
            "sectors": sectors,
            "stocks": stocks_analysis,
            "quality": {
                "records_processed": quality_summary.get("records_processed", 0),
                "records_valid": quality_summary.get("records_valid", 0),
                "warnings_count": len(quality_summary.get("warnings", [])),
                "errors_count": len(quality_summary.get("errors", []))
            }
        }
