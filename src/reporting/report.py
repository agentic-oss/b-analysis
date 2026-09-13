import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DailyReportGenerator:
    """
    Generates human-readable daily Markdown report (reports/daily/YYYY-MM-DD.md).
    """

    @staticmethod
    def generate_markdown(analysis_data: Dict[str, Any], output_path: str) -> str:
        date_str = analysis_data.get("date", "N/A")
        market = analysis_data.get("market", {})
        sectors = analysis_data.get("sectors", [])
        stocks = analysis_data.get("stocks", [])
        quality = analysis_data.get("quality", {})

        md = []
        md.append(f"# Daily Indian Stock Market Research & Analysis Report - {date_str}\n")

        # 1. Market Summary
        md.append("## Market Summary\n")
        md.append(f"- **Market Regime:** `{market.get('regime', 'N/A')}`")
        md.append(f"- **NIFTY 50 Close:** `{market.get('nifty_close', 'N/A')}` ({market.get('nifty_return_1d', 0)*100:+.2f}%)")
        md.append(f"- **NIFTY Trend:** {market.get('nifty_trend', 'N/A')}")
        md.append(f"- **BANK NIFTY Trend:** {market.get('banknifty_trend', 'N/A')}")
        md.append(f"- **Advance / Decline Ratio:** `{market.get('advance_decline_ratio', 1.0)}` ({market.get('advances', 0)} Advances / {market.get('declines', 0)} Declines)")
        md.append(f"- **Market Breadth (% > 50 DMA):** `{market.get('breadth_pct_above_50dma', 0)}%`\n")
        md.append(f"> **Regime Note:** {market.get('explanation', '')}\n")

        # 2. Sector Leaders & Laggards
        md.append("## Sector Analysis\n")
        if sectors:
            md.append("| Rank | Sector | Daily Return | Weekly Return | Rel. Strength vs NIFTY | Momentum Score |")
            md.append("|:---:|:---|:---:|:---:|:---:|:---:|")
            for s in sectors:
                md.append(f"| {s.get('rank')} | {s.get('sector')} | {s.get('daily_return'):+.2f}% | {s.get('weekly_return'):+.2f}% | {s.get('relative_strength'):+.2f}% | {s.get('momentum_score')} |")
            md.append("\n")

        # 3. Top Strong & Weak Stocks
        sorted_stocks = sorted(stocks, key=lambda x: x.get('composite_score', 0), reverse=True)
        strong_stocks = sorted_stocks[:5]
        weak_stocks = sorted_stocks[-5:][::-1]

        md.append("## Strong Stocks (Top Composite Scores)\n")
        if strong_stocks:
            md.append("| Symbol | Composite Score | Label | Trend | Momentum | Vol. RVOL |")
            md.append("|:---|:---:|:---:|:---:|:---:|:---:|")
            for st in strong_stocks:
                comps = st.get('score_components', {})
                md.append(f"| {st.get('symbol')} | **{st.get('composite_score')}** | {st.get('label')} | {comps.get('technical_trend')} | {comps.get('momentum')} | {st.get('relative_volume', 1.0):.2f}x |")
            md.append("\n")

        md.append("## Weak Stocks (Lowest Composite Scores)\n")
        if weak_stocks:
            md.append("| Symbol | Composite Score | Label | Trend | Momentum | Vol. RVOL |")
            md.append("|:---|:---:|:---:|:---:|:---:|:---:|")
            for st in weak_stocks:
                comps = st.get('score_components', {})
                md.append(f"| {st.get('symbol')} | **{st.get('composite_score')}** | {st.get('label')} | {comps.get('technical_trend')} | {comps.get('momentum')} | {st.get('relative_volume', 1.0):.2f}x |")
            md.append("\n")

        # 4. Technical Events (Breakouts / Breakdowns / Unusual Volume)
        md.append("## Technical Events & Unusual Volume\n")
        breakouts = [s['symbol'] for s in stocks if s.get('breakout_20d')]
        breakdowns = [s['symbol'] for s in stocks if s.get('breakdown_20d')]
        unusual_vol = [s['symbol'] for s in stocks if s.get('relative_volume', 0) > 2.0]

        md.append(f"- **20-Day Breakouts:** {', '.join(breakouts) if breakouts else 'None detected'}")
        md.append(f"- **20-Day Breakdowns:** {', '.join(breakdowns) if breakdowns else 'None detected'}")
        md.append(f"- **Unusual Volume (>2x 20DMA):** {', '.join(unusual_vol) if unusual_vol else 'None detected'}\n")

        # 5. Sample Historical Analogues & Forward Probabilities
        md.append("## Historical Analogues & Directional Signals (Sample)\n")
        sample = sorted_stocks[0] if sorted_stocks else None
        if sample:
            md.append(f"### Symbol Focus: {sample.get('symbol')}")
            md.append(f"- **Analogues Found:** {sample.get('historical_analogues', {}).get('observations_count', 0)} historical instances")
            fwd = sample.get('signals', {})
            if fwd:
                md.append("| Horizon | Directional Bias | Confidence | Historical Win Rate |")
                md.append("|:---:|:---:|:---:|:---:|")
                for h, sig in fwd.items():
                    md.append(f"| {h.upper()} | **{sig.get('directional_bias')}** | {sig.get('confidence_score')}% | {sig.get('historical_win_rate_pct')}% |")
            md.append("\n")

        # 6. Data Quality & Safeguards
        md.append("## Data Quality & Research Safeguards\n")
        md.append(f"- **Processed Records:** `{quality.get('records_processed', 0)}`")
        md.append(f"- **Valid Records:** `{quality.get('records_valid', 0)}`")
        md.append(f"- **Warnings:** `{len(quality.get('warnings', []))}`")
        md.append(f"- **Errors:** `{len(quality.get('errors', []))}`\n")
        md.append("> **Disclaimer:** All model outputs and signals are statistical estimates derived from historical data. They do not constitute financial advice or guaranteed market predictions.")

        report_content = "\n".join(md)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report_content)

        return report_content
