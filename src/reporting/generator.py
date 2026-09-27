"""
Generates daily Markdown reports from aggregated market analysis outputs.
"""
from typing import Dict, Any, List
import pandas as pd


class ReportGenerator:
    """Renders human-readable daily analysis Markdown report."""

    @staticmethod
    def generate_markdown(analysis_data: Dict[str, Any]) -> str:
        date_str = analysis_data.get("date", "YYYY-MM-DD")
        mkt = analysis_data.get("market", {})
        sectors = analysis_data.get("sectors", [])
        stocks = analysis_data.get("stocks", [])
        events = analysis_data.get("technical_events", [])
        quality = analysis_data.get("quality", {})

        md = []
        md.append(f"# Daily Indian Stock Market Analysis Report — {date_str}\n")

        # 1. Market Summary
        md.append("## Market Summary\n")
        md.append(f"- **Market Regime:** `{mkt.get('regime', 'Neutral')}` (Composite Score: {mkt.get('score', 50)}/100)")
        md.append(f"- **NIFTY Trend:** {mkt.get('nifty_trend', 'N/A')}")
        md.append(f"- **Market Breadth (>50 DMA):** {mkt.get('breadth_above_50dma_pct', 0.0)}%")
        md.append(f"- **Advance / Decline Ratio:** {mkt.get('advance_decline_ratio', 1.0)}\n")

        if mkt.get("rules_applied"):
            md.append("### Classification Rules Applied")
            for r in mkt["rules_applied"]:
                md.append(f"- {r}")
            md.append("")

        # 2. Sector Leaders & Laggards
        md.append("## Sector Performance Rankings\n")
        if sectors:
            md.append("| Rank | Sector | Daily Return | Weekly Return | Relative Strength vs NIFTY | Momentum Score |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for sec in sectors:
                md.append(
                    f"| {sec.get('rank')} | {sec.get('sector')} | {sec.get('daily_return_pct')}% | {sec.get('weekly_return_pct')}% | {sec.get('relative_strength_vs_nifty')}% | {sec.get('momentum_score')} |"
                )
            md.append("")
        else:
            md.append("Sector data unavailable.\n")

        # 3. Strongest & Weakest Stocks
        md.append("## Stock Universe Highlights\n")
        sorted_stocks = sorted(stocks, key=lambda x: x.get("technical_score", 50), reverse=True)

        md.append("### Highest Scoring Stocks")
        md.append("| Symbol | Sector | Composite Score | Rating | Technical Score | Fundamental Score |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in sorted_stocks[:5]:
            md.append(
                f"| **{st.get('symbol')}** | {st.get('sector')} | {st.get('technical_score')} | {st.get('score_label')} | {st.get('technical_score')} | {st.get('fundamental_score', 'N/A')} |"
            )
        md.append("")

        md.append("### Lowest Scoring Stocks")
        md.append("| Symbol | Sector | Composite Score | Rating | Technical Score | Fundamental Score |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in sorted_stocks[-5:]:
            md.append(
                f"| **{st.get('symbol')}** | {st.get('sector')} | {st.get('technical_score')} | {st.get('score_label')} | {st.get('technical_score')} | {st.get('fundamental_score', 'N/A')} |"
            )
        md.append("")

        # 4. Technical Events (Breakouts / Crosses / Volume Surges)
        md.append("## Technical Events & Anomalies\n")
        if events:
            for ev in events:
                md.append(
                    f"- **[{ev.get('severity')}] {ev.get('symbol')}**: {ev.get('type')} ({ev.get('bias')} bias)"
                )
            md.append("")
        else:
            md.append("No major breakout or technical cross events detected today.\n")

        # 5. Historical Analogues & Forward Probabilities Summary
        md.append("## Historical Analogue & Probabilistic Assessment\n")
        md.append("Below are empirical conditional forward probability statistics derived from historical pattern matches:\n")
        for st in sorted_stocks[:3]:
            analogues = st.get("historical_analogues", {})
            horizons = analogues.get("horizons", {})
            md.append(f"### {st.get('symbol')} (Match criteria: {analogues.get('match_conditions', 'N/A')})")
            if horizons:
                md.append("| Horizon | Matches | Mean Return | Win Rate % | Volatility |")
                md.append("| :--- | :--- | :--- | :--- | :--- |")
                for h_key, h_val in horizons.items():
                    md.append(
                        f"| {h_key} | {h_val.get('count')} | {h_val.get('mean_return_pct')}% | {h_val.get('win_rate_pct')}% | {h_val.get('volatility_pct')}% |"
                    )
            else:
                md.append("No clear historical analogue cluster found.")
            md.append("")

        # 6. Data Quality & Observability
        md.append("## Data Quality & System Status\n")
        md.append(f"- **Symbols Processed:** {quality.get('records_processed', 0)}")
        md.append(f"- **Valid Records:** {quality.get('records_valid', 0)}")
        md.append(f"- **Data Warnings:** {quality.get('warnings_count', 0)}")
        md.append(f"- **Data Errors:** {quality.get('errors_count', 0)}\n")

        # 7. Research Notes & Safeguards
        md.append("## Research & Methodological Notes\n")
        md.append(
            "- **Non-Deterministic Signals:** Forward directional signals are research-oriented empirical probability estimates and do not guarantee future stock movements."
        )
        md.append(
            "- **Zero Look-Ahead Bias:** All technical features and historical analogue matches strictly evaluate data available on or prior to the trading date."
        )

        return "\n".join(md)
