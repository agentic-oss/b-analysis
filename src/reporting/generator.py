import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates human-readable Markdown reports for daily Indian market analysis."""

    def generate_markdown_report(self, date_str: str, market_data: Dict[str, Any], sectors_data: List[Dict[str, Any]], stock_results: List[Dict[str, Any]], quality_data: Dict[str, Any], prediction_metrics: Dict[str, Any] = None) -> str:
        """Constructs structured, analytical Markdown report."""
        mb = market_data.get("market_breadth", {})

        md = []
        md.append(f"# Daily Indian Stock Market Deep Analysis Report - {date_str}\n")
        md.append("## Executive Summary\n")
        md.append(f"- **Market Regime:** {market_data.get('regime', 'Neutral')} (Composite Score: {market_data.get('score', 50)}/100)")
        md.append(f"- **NIFTY 50 Trend:** {market_data.get('nifty_trend', 'Neutral')} (1D Return: {market_data.get('nifty_return_1d', 0)*100:.2f}%, 20D Return: {market_data.get('nifty_return_20d', 0)*100:.2f}%)")
        md.append(f"- **BANK NIFTY Trend:** {market_data.get('bank_nifty_trend', 'Neutral')}")
        md.append(f"- **Market Breadth (A/D Ratio):** {mb.get('advance_decline_ratio', 1.0)} | % Above 50 DMA: {mb.get('pct_above_50dma', 50.0)}%\n")

        # Rules triggered
        rules = market_data.get("rules_triggered", [])
        if rules:
            md.append("**Market Drivers Identified:**")
            for r in rules:
                md.append(f"- {r}")
            md.append("")

        # Sector Rankings
        md.append("## Sector Performance & Rotation\n")
        md.append("| Rank | Sector | Daily Return | Weekly Return | Monthly Return | RS vs NIFTY (20D) | Momentum Score |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for s in sectors_data:
            md.append(f"| {s.get('rank', '-')} | {s.get('sector', '-')} | {s.get('daily_return', 0):+.2f}% | {s.get('weekly_return', 0):+.2f}% | {s.get('monthly_return', 0):+.2f}% | {s.get('rs_vs_nifty_20d', 0):+.2f}% | {s.get('momentum_score', 50):.1f} |")
        md.append("")

        # Stock Highlights
        sorted_stocks = sorted(stock_results, key=lambda x: x.get("composite_score", 0), reverse=True)
        top_stocks = sorted_stocks[:5]
        bottom_stocks = sorted_stocks[-5:]

        md.append("## Stock Highlights\n")
        md.append("### Top Performing / Highest Scored Stocks")
        md.append("| Symbol | Label | Score | Trend | Momentum | Volume | 1D Return | 20D Bias |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in top_stocks:
            comps = st.get("components", {})
            sig20 = st.get("future_signals", {}).get("20d", {}).get("directional_bias", "Neutral")
            md.append(f"| {st.get('symbol')} | {st.get('label')} | {st.get('composite_score')} | {comps.get('technical_trend')} | {comps.get('momentum')} | {comps.get('volume')} | {st.get('return_1d', 0)*100:+.2f}% | {sig20} |")
        md.append("")

        md.append("### Weakest / Lowest Scored Stocks")
        md.append("| Symbol | Label | Score | Trend | Momentum | Volume | 1D Return | 20D Bias |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in bottom_stocks:
            comps = st.get("components", {})
            sig20 = st.get("future_signals", {}).get("20d", {}).get("directional_bias", "Neutral")
            md.append(f"| {st.get('symbol')} | {st.get('label')} | {st.get('composite_score')} | {comps.get('technical_trend')} | {comps.get('momentum')} | {comps.get('volume')} | {st.get('return_1d', 0)*100:+.2f}% | {sig20} |")
        md.append("")

        # Technical Events
        breakouts = [st['symbol'] for st in stock_results if st.get('breakout_20d')]
        breakdowns = [st['symbol'] for st in stock_results if st.get('breakdown_20d')]
        unusual_vol = [st['symbol'] for st in stock_results if st.get('unusual_volume')]

        md.append("## Technical Events & Patterns\n")
        md.append(f"- **20-Day Breakouts:** {', '.join(breakouts) if breakouts else 'None'}")
        md.append(f"- **20-Day Breakdowns:** {', '.join(breakdowns) if breakdowns else 'None'}")
        md.append(f"- **Unusual Volume Surge (>= 2.0x 20DMA):** {', '.join(unusual_vol) if unusual_vol else 'None'}\n")

        # Predictive ML Research & Model Health
        if prediction_metrics:
            md.append("## Predictive Research & Baseline Models\n")
            md.append("Out-of-sample directional prediction metrics:")
            for model_name, m in prediction_metrics.get("metrics", {}).items():
                acc = m.get("accuracy", 0) * 100
                md.append(f"- **{model_name}:** Accuracy = {acc:.2f}% (Samples = {m.get('sample_size', m.get('train_samples', 'N/A'))})")
            md.append("")

        # Data Quality Section
        md.append("## Data Quality & Integrity\n")
        md.append(f"- **Total Records Processed:** {quality_data.get('records_processed', 0)}")
        md.append(f"- **Valid Records:** {quality_data.get('records_valid', 0)}")
        md.append(f"- **Warnings Count:** {quality_data.get('warnings_count', 0)}")
        md.append(f"- **Errors Count:** {quality_data.get('errors_count', 0)}\n")

        md.append("---")
        md.append("*Disclaimer: This document is generated for empirical research and analytical purposes. Probabilities and scores represent statistical observations rather than guaranteed market forecasts.*")

        return "\n".join(md)
