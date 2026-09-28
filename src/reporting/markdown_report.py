import os
from typing import Dict, Any, List

class MarkdownReportGenerator:
    """Generates a comprehensive human-readable Markdown report for daily market analysis."""

    @staticmethod
    def generate_report(data: Dict[str, Any], output_path: str):
        """Builds and writes reports/daily/YYYY-MM-DD.md."""
        date_str = data.get("date", "N/A")
        market = data.get("market", {})
        sectors = data.get("sectors", [])
        stocks = data.get("stocks", [])
        quality = data.get("quality", {})

        md = []
        md.append(f"# Daily Indian Stock Market Research Report - {date_str}\n")

        # 1. Market Summary
        md.append("## Market Summary\n")
        md.append(f"- **Market Regime:** {market.get('market_regime', 'N/A')}")
        md.append(f"- **NIFTY Benchmark Close:** {market.get('nifty_close', 'N/A')} ({market.get('nifty_trend', 'N/A')})")
        md.append(f"- **BANK NIFTY Trend:** {market.get('banknifty_trend', 'N/A')}")
        md.append(f"- **NIFTY 20D Annualized Volatility:** {market.get('nifty_volatility_20d', 0.0)*100:.1f}%\n")

        breadth = market.get('breadth', {})
        if breadth:
            md.append("### Market Breadth")
            md.append(f"- **Tracked Equities:** {breadth.get('total_tracked', 0)}")
            md.append(f"- **% Stocks Above 20 DMA:** {breadth.get('pct_above_20dma', 0)}%")
            md.append(f"- **% Stocks Above 50 DMA:** {breadth.get('pct_above_50dma', 0)}%")
            md.append(f"- **% Stocks Above 200 DMA:** {breadth.get('pct_above_200dma', 0)}%")
            md.append(f"- **Advance / Decline Ratio:** {breadth.get('advance_decline_ratio', 0)} ({breadth.get('advances', 0)} Advances / {breadth.get('declines', 0)} Declines)")
            md.append(f"- **20-Day New Highs / Lows:** {breadth.get('new_highs_20d', 0)} / {breadth.get('new_lows_20d', 0)}\n")

        # 2. Sector Performance
        md.append("## Sector Performance\n")
        if sectors:
            md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | RS vs NIFTY (%) | Momentum Score |")
            md.append("|------|--------|------------------|-------------------|-----------------|----------------|")
            for sec in sectors:
                md.append(f"| {sec.get('rank', '-')} | {sec.get('sector', '-')} | {sec.get('daily_return', 0.0)}% | {sec.get('weekly_return', 0.0)}% | {sec.get('relative_strength_vs_nifty', 0.0)}% | {sec.get('momentum_score', 0.0)} |")
            md.append("")

        # Top/Bottom Stocks
        sorted_stocks = sorted(stocks, key=lambda x: x.get('technical_score', 0), reverse=True)
        top_stocks = sorted_stocks[:5] if len(sorted_stocks) >= 5 else sorted_stocks
        bottom_stocks = sorted_stocks[-5:] if len(sorted_stocks) >= 5 else []

        md.append("## Stock Universe Focus\n")
        md.append("### Strongest Stocks (Top Composite Scores)")
        if top_stocks:
            md.append("| Symbol | Composite Score | Label | Fundamental Score | 1D Bias | 5D Bias |")
            md.append("|--------|-----------------|-------|-------------------|---------|---------|")
            for stk in top_stocks:
                fwd_1d = stk.get('forward_signals', {}).get('1d', {}).get('directional_bias', 'Neutral')
                fwd_5d = stk.get('forward_signals', {}).get('5d', {}).get('directional_bias', 'Neutral')
                md.append(f"| {stk.get('symbol')} | {stk.get('technical_score')} | {stk.get('label')} | {stk.get('fundamental_score')} | {fwd_1d} | {fwd_5d} |")
            md.append("")

        if bottom_stocks:
            md.append("### Weakest Stocks (Lowest Composite Scores)")
            md.append("| Symbol | Composite Score | Label | Fundamental Score | 1D Bias | 5D Bias |")
            md.append("|--------|-----------------|-------|-------------------|---------|---------|")
            for stk in bottom_stocks:
                fwd_1d = stk.get('forward_signals', {}).get('1d', {}).get('directional_bias', 'Neutral')
                fwd_5d = stk.get('forward_signals', {}).get('5d', {}).get('directional_bias', 'Neutral')
                md.append(f"| {stk.get('symbol')} | {stk.get('technical_score')} | {stk.get('label')} | {stk.get('fundamental_score')} | {fwd_1d} | {fwd_5d} |")
            md.append("")

        # Breakouts & Technical Events
        md.append("## Technical Events & Breakouts\n")
        events_found = False
        for stk in stocks:
            signals = stk.get('signals', [])
            if signals:
                events_found = True
                md.append(f"- **{stk.get('symbol')}:** {', '.join(signals)}")
        if not events_found:
            md.append("No major breakout or technical crossover events detected today.")
        md.append("")

        # Data Quality Section
        md.append("## Data Quality Audit\n")
        md.append(f"- **Records Processed:** {quality.get('records_processed', 0)}")
        md.append(f"- **Valid Records:** {quality.get('records_valid', 0)}")
        if quality.get('warnings'):
            md.append(f"- **Warnings ({len(quality['warnings'])}):** {quality['warnings'][:3]}")
        else:
            md.append("- **Warnings:** None")
        if quality.get('errors'):
            md.append(f"- **Errors ({len(quality['errors'])}):** {quality['errors']}")
        else:
            md.append("- **Errors:** None")
        md.append("")

        # Disclaimers & Methodology Note
        md.append("## Research Disclaimers\n")
        md.append("> *Notice: This analysis report is generated automatically for statistical research and quantitative modeling purposes only. Directional inferences and analogue probabilities represent statistical empirical signals, NOT guaranteed market outcomes or financial advice.*")

        content = "\n".join(md)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
