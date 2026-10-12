"""
Report generator for creating human-readable Markdown reports and machine-readable JSON files.
"""

from typing import Dict, Any, List
import json


class ReportGenerator:
    """
    Generates Markdown daily market analysis report and structured JSON output.
    """

    def generate_markdown_report(self, date_str: str, analysis_data: Dict[str, Any]) -> str:
        """
        Generates comprehensive Markdown report adhering to required daily schema.
        """
        market = analysis_data.get("market", {})
        sectors = analysis_data.get("sectors", [])
        stocks = analysis_data.get("stocks", [])
        quality = analysis_data.get("quality", {})

        top_sectors = sorted(sectors, key=lambda x: x.get("momentum_score", 0), reverse=True)[:3]
        bottom_sectors = sorted(sectors, key=lambda x: x.get("momentum_score", 0))[:3]

        top_stocks = sorted(stocks, key=lambda x: x.get("composite_score", 0), reverse=True)[:5]
        bottom_stocks = sorted(stocks, key=lambda x: x.get("composite_score", 0))[:5]

        unusual_volume_stocks = [s for s in stocks if "UNUSUAL_VOLUME" in s.get("signals", [])]
        breakout_stocks = [s for s in stocks if "BOLLINGER_BREAKOUT" in s.get("signals", []) or "GOLDEN_CROSS" in s.get("signals", [])]

        md = []
        md.append(f"# Daily Indian Stock Market Analysis - {date_str}")
        md.append("")
        md.append("## Market Summary")
        md.append(f"- **Market Regime**: {market.get('regime', 'Neutral')}")
        md.append(f"- **NIFTY Trend**: {market.get('nifty_trend', 'Neutral')}")
        md.append(f"- **NIFTY Daily Return**: {market.get('nifty_return_1d', 0.0) * 100:.2f}%")
        md.append(f"- **NIFTY 20D Annualized Volatility**: {market.get('nifty_volatility_20d', 0.0) * 100:.2f}%")
        md.append(f"- **Advance/Decline Ratio**: {market.get('advance_decline_ratio', 1.0)}")
        md.append(f"- **Market Breadth (% > 50 DMA)**: {market.get('pct_above_50dma', 50.0)}%")
        md.append("")

        md.append("## Sector Leaders")
        if top_sectors:
            md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | Momentum Score |")
            md.append("|---|---|---|---|---|")
            for s in top_sectors:
                md.append(f"| {s.get('rank')} | {s.get('sector')} | {s.get('daily_return')}% | {s.get('weekly_return')}% | {s.get('momentum_score')} |")
        else:
            md.append("No sector data available.")
        md.append("")

        md.append("## Sector Laggards")
        if bottom_sectors:
            md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | Momentum Score |")
            md.append("|---|---|---|---|---|")
            for s in bottom_sectors:
                md.append(f"| {s.get('rank')} | {s.get('sector')} | {s.get('daily_return')}% | {s.get('weekly_return')}% | {s.get('momentum_score')} |")
        else:
            md.append("No sector data available.")
        md.append("")

        md.append("## Strong Stocks")
        if top_stocks:
            md.append("| Symbol | Composite Score | Label | Daily Return (%) | Trend Alignment |")
            md.append("|---|---|---|---|---|")
            for st in top_stocks:
                md.append(f"| {st.get('symbol')} | {st.get('composite_score')} | {st.get('label')} | {st.get('daily_return_pct', 0.0):.2f}% | {st.get('trend_alignment', 'Neutral')} |")
        else:
            md.append("No stock data available.")
        md.append("")

        md.append("## Weak Stocks")
        if bottom_stocks:
            md.append("| Symbol | Composite Score | Label | Daily Return (%) | Trend Alignment |")
            md.append("|---|---|---|---|---|")
            for st in bottom_stocks:
                md.append(f"| {st.get('symbol')} | {st.get('composite_score')} | {st.get('label')} | {st.get('daily_return_pct', 0.0):.2f}% | {st.get('trend_alignment', 'Neutral')} |")
        else:
            md.append("No stock data available.")
        md.append("")

        md.append("## Breakouts / Breakdowns")
        if breakout_stocks:
            for s in breakout_stocks:
                md.append(f"- **{s.get('symbol')}**: {', '.join(s.get('events', []))}")
        else:
            md.append("No breakout or golden cross events detected today.")
        md.append("")

        md.append("## Unusual Volume")
        if unusual_volume_stocks:
            for s in unusual_volume_stocks:
                md.append(f"- **{s.get('symbol')}**: Relative Volume {s.get('relative_volume', 1.0):.2f}x 20-day SMA")
        else:
            md.append("No unusual volume spikes detected today.")
        md.append("")

        md.append("## Historical Analogues & Forward Probabilities")
        sample_stock = top_stocks[0] if top_stocks else (stocks[0] if stocks else None)
        if sample_stock and "forward_probabilities" in sample_stock:
            fwd = sample_stock.get("forward_probabilities", {})
            bias = sample_stock.get("directional_bias", {})
            md.append(f"Sample Stock Analysis for **{sample_stock.get('symbol')}** (Based on {sample_stock.get('num_analogues', 0)} historical analogues):")
            md.append("| Horizon | Positive Prob (%) | Avg Forward Return (%) | Directional Bias |")
            md.append("|---|---|---|---|")
            for h in ["1d", "3d", "5d", "10d", "20d"]:
                if h in fwd:
                    stat = fwd[h]
                    md.append(f"| {h} | {stat.get('positive_return_prob')}% | {stat.get('avg_forward_return_pct')}% | {bias.get(h, 'Neutral')} |")
        else:
            md.append("Historical analogue probability data not available.")
        md.append("")

        md.append("## Data Quality")
        md.append(f"- **Total Records Processed**: {quality.get('records_processed', 0)}")
        md.append(f"- **Valid Records**: {quality.get('records_valid', 0)}")
        md.append(f"- **Warnings**: {len(quality.get('warnings', []))}")
        md.append(f"- **Errors**: {len(quality.get('errors', []))}")
        md.append("")

        md.append("## Research Notes")
        md.append("- All forward-looking directional bias estimates represent empirical statistical probabilities derived from historical setup analogues and should not be treated as guaranteed forecasts.")
        md.append("- Market regime classification is calculated deterministically based on market breadth (% stocks above 50 DMA) and NIFTY moving average alignment.")
        md.append("")

        return "\n".join(md)

    def generate_json_schema_data(self, date_str: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats machine-readable JSON structure adhering to stable schema requirements.
        """
        return {
            "date": date_str,
            "market": analysis_data.get("market", {}),
            "sectors": analysis_data.get("sectors", []),
            "stocks": analysis_data.get("stocks", []),
            "quality": analysis_data.get("quality", {}),
        }
