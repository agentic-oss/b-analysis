import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates human-readable Markdown reports and machine-readable JSON outputs."""

    def __init__(self, reports_dir: str = "reports/daily", data_analysis_dir: str = "data/analysis/daily"):
        self.reports_dir = reports_dir
        self.data_analysis_dir = data_analysis_dir
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.data_analysis_dir, exist_ok=True)

    def generate_json_output(self, date_str: str, pipeline_output: Dict[str, Any]) -> str:
        """
        Generates structured JSON data export: data/analysis/daily/YYYY-MM-DD.json
        """
        json_path = os.path.join(self.data_analysis_dir, f"{date_str}.json")
        with open(json_path, "w") as f:
            json.dump(pipeline_output, f, indent=2)
        logger.info(f"Saved machine-readable JSON analysis to {json_path}")
        return json_path

    def generate_markdown_report(self, date_str: str, pipeline_output: Dict[str, Any]) -> str:
        """
        Generates human-readable Markdown report: reports/daily/YYYY-MM-DD.md
        """
        market = pipeline_output.get("market", {})
        sectors = pipeline_output.get("sectors", [])
        stocks = pipeline_output.get("stocks", [])
        quality = pipeline_output.get("data_quality", {})

        # Rank stocks by composite score
        sorted_stocks = sorted(stocks, key=lambda s: s.get("score", {}).get("composite_score", 0.0), reverse=True)
        strong_stocks = sorted_stocks[:5]
        weak_stocks = sorted_stocks[-5:] if len(sorted_stocks) >= 5 else []

        md = []
        md.append(f"# Daily Indian Stock Market Deep Analysis - {date_str}\n")
        md.append("## Market Summary")
        md.append(f"- **Market Regime**: `{market.get('regime', 'N/A')}`")
        md.append(f"- **NIFTY Close**: {market.get('nifty_close', 'N/A')}")
        md.append(f"- **NIFTY Trend**: {market.get('nifty_trend', 'N/A')}")
        md.append(f"- **Annualized Volatility**: {market.get('nifty_volatility_annualized', 'N/A')}%")
        md.append(f"- **Advance / Decline Ratio**: {market.get('advance_decline_ratio', 'N/A')} ({market.get('advances', 0)} Advances / {market.get('declines', 0)} Declines)")
        md.append(f"- **Stocks Above 50 DMA**: {market.get('breadth_pct_above_50dma', 'N/A')}%\n")

        md.append("## Sector Leaders & Laggards")
        md.append("| Rank | Sector | Daily Return | Weekly Return | Relative Strength vs NIFTY | Momentum Score |")
        md.append("|------|--------|--------------|---------------|-----------------------------|----------------|")
        for sec in sectors:
            md.append(f"| {sec.get('rank', '-')} | {sec.get('sector', 'N/A')} | {sec.get('daily_return', 0.0)}% | {sec.get('weekly_return', 0.0)}% | {sec.get('relative_strength_vs_nifty', 0.0)}% | {sec.get('momentum_score', 0.0)} |")
        md.append("")

        md.append("## Top Scoring Stocks (Strong)")
        md.append("| Symbol | Composite Score | Label | Trend Score | Momentum Score | Volume Score | Sector |")
        md.append("|--------|-----------------|-------|-------------|----------------|--------------|--------|")
        for stk in strong_stocks:
            sc = stk.get("score", {})
            comp = sc.get("components", {})
            md.append(f"| {stk.get('symbol')} | {sc.get('composite_score')} | {sc.get('label')} | {comp.get('technical_trend_score')} | {comp.get('momentum_score')} | {comp.get('volume_score')} | {stk.get('sector', 'N/A')} |")
        md.append("")

        if weak_stocks:
            md.append("## Lowest Scoring Stocks (Weak)")
            md.append("| Symbol | Composite Score | Label | Trend Score | Momentum Score | Volume Score | Sector |")
            md.append("|--------|-----------------|-------|-------------|----------------|--------------|--------|")
            for stk in weak_stocks:
                sc = stk.get("score", {})
                comp = sc.get("components", {})
                md.append(f"| {stk.get('symbol')} | {sc.get('composite_score')} | {sc.get('label')} | {comp.get('technical_trend_score')} | {comp.get('momentum_score')} | {comp.get('volume_score')} | {stk.get('sector', 'N/A')} |")
            md.append("")

        md.append("## Technical Breakouts & Events")
        events_found = 0
        for stk in stocks:
            ev = stk.get("technical_events", {})
            if ev.get("breakout_20d") or ev.get("golden_cross") or ev.get("unusual_volume"):
                events_found += 1
                ev_list = []
                if ev.get("breakout_20d"): ev_list.append("20-Day Breakout")
                if ev.get("golden_cross"): ev_list.append("Golden Cross")
                if ev.get("unusual_volume"): ev_list.append("Unusual Volume")
                md.append(f"- **{stk.get('symbol')}**: {', '.join(ev_list)} (Support: {ev.get('support_level')}, Resistance: {ev.get('resistance_level')})")
        if events_found == 0:
            md.append("- No major breakout or cross events detected in today's session.\n")
        else:
            md.append("")

        md.append("## Forward Probability Signals (5-Day Horizon)")
        md.append("| Symbol | Directional Bias | Confidence | Historical Positive Return % | Expected Avg Return % |")
        md.append("|--------|------------------|------------|-------------------------------|-----------------------|")
        for stk in stocks[:10]:
            sig_5d = stk.get("signals", {}).get("5d", {})
            md.append(f"| {stk.get('symbol')} | {sig_5d.get('directional_bias', 'N/A')} | {sig_5d.get('confidence', 0)}% | {sig_5d.get('empirical_positive_probability', 0)}% | {sig_5d.get('expected_average_return_pct', 0)}% |")
        md.append("")

        md.append("## Data Quality & System Status")
        md.append(f"- **Records Processed**: {quality.get('records_processed', 0)}")
        md.append(f"- **Records Valid**: {quality.get('records_valid', 0)}")
        md.append(f"- **Quality Warnings**: {len(quality.get('warnings', []))}")
        md.append(f"- **Quality Errors**: {len(quality.get('errors', []))}\n")

        md.append("## Research Disclaimer")
        md.append("This report is produced by an automated market data analysis system. Outputs represent historical statistical probabilities and research metrics, not guaranteed predictions or financial advice.\n")

        report_content = "\n".join(md)
        md_path = os.path.join(self.reports_dir, f"{date_str}.md")
        with open(md_path, "w") as f:
            f.write(report_content)

        logger.info(f"Saved human-readable Markdown report to {md_path}")
        return md_path
