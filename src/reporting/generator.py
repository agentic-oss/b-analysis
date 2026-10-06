import json
from typing import Dict, Any, List


class ReportGenerator:
    """Generates machine-readable JSON and human-readable Markdown research reports."""

    @staticmethod
    def generate_daily_json(
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_rankings: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generates schema-compliant JSON analysis structure."""
        return {
            "date": date_str,
            "market": market_analysis,
            "sectors": sector_rankings,
            "stocks": stock_analyses
        }

    @staticmethod
    def generate_daily_markdown(
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_rankings: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> str:
        """Generates comprehensive daily market research markdown report."""
        breadth = market_analysis.get('breadth', {})
        regime = market_analysis.get('regime', 'Neutral')
        nifty_close = market_analysis.get('nifty_close', 'N/A')
        nifty_vol = market_analysis.get('nifty_volatility_20d', 0.0)

        # Sort stock summaries
        sorted_stocks = sorted(stock_analyses, key=lambda x: x.get('composite_score', 0), reverse=True)
        top_strong = sorted_stocks[:5]
        top_weak = sorted_stocks[-5:][::-1] if len(sorted_stocks) >= 5 else []

        # Find events
        breakouts = []
        unusual_volume = []
        for s in stock_analyses:
            events = s.get('signals', {}).get('events', [])
            sym = s.get('symbol')
            if any('Breakout' in e for e in events):
                breakouts.append(sym)
            if s.get('signals', {}).get('unusual_volume', False):
                unusual_volume.append(sym)

        # Top sector leaders & laggards
        sector_leaders = sector_rankings[:3] if sector_rankings else []
        sector_laggards = sector_rankings[-3:][::-1] if len(sector_rankings) >= 3 else []

        md = []
        md.append(f"# Daily Indian Stock Market Analysis - {date_str}\n")

        # 1. Market Summary
        md.append("## Market Summary")
        md.append(f"- **Market Regime**: `{regime}` (Score: {market_analysis.get('regime_score', 0)})")
        md.append(f"- **NIFTY 50 Close**: `{nifty_close}`")
        md.append(f"- **Annualized 20D Volatility**: `{round(nifty_vol * 100, 2)}%`")
        md.append(f"- **Market Breadth**: Advances: `{breadth.get('advances', 0)}` | Declines: `{breadth.get('declines', 0)}` (A/D Ratio: `{breadth.get('ad_ratio', 1.0)}`)")
        md.append(f"- **Stocks above 50 DMA**: `{breadth.get('pct_above_50dma', 0)}%` | Above 200 DMA: `{breadth.get('pct_above_200dma', 0)}%`")
        md.append(f"- **20-Day New Highs / Lows**: `{breadth.get('new_highs_20d', 0)}` Highs / `{breadth.get('new_lows_20d', 0)}` Lows\n")

        # 2. Sector Performance
        md.append("## Sector Leaders")
        if sector_leaders:
            md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | Momentum Score |")
            md.append("|---|---|---|---|---|")
            for sec in sector_leaders:
                md.append(f"| {sec.get('rank')} | {sec.get('sector')} | {sec.get('daily_return')}% | {sec.get('weekly_return')}% | {sec.get('momentum_score')} |")
        else:
            md.append("No sector data available.")
        md.append("")

        md.append("## Sector Laggards")
        if sector_laggards:
            md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | Momentum Score |")
            md.append("|---|---|---|---|---|")
            for sec in sector_laggards:
                md.append(f"| {sec.get('rank')} | {sec.get('sector')} | {sec.get('daily_return')}% | {sec.get('weekly_return')}% | {sec.get('momentum_score')} |")
        else:
            md.append("No sector data available.")
        md.append("")

        # 3. Stock Highlights
        md.append("## Strong Stocks (Highest Composite Score)")
        if top_strong:
            md.append("| Symbol | Composite Score | Label | Technical Score | Fundamental Score |")
            md.append("|---|---|---|---|---|")
            for s in top_strong:
                md.append(f"| `{s.get('symbol')}` | {s.get('composite_score')} | {s.get('score_label')} | {s.get('technical_score')} | {s.get('fundamental_score')} |")
        md.append("")

        md.append("## Weak Stocks (Lowest Composite Score)")
        if top_weak:
            md.append("| Symbol | Composite Score | Label | Technical Score | Fundamental Score |")
            md.append("|---|---|---|---|---|")
            for s in top_weak:
                md.append(f"| `{s.get('symbol')}` | {s.get('composite_score')} | {s.get('score_label')} | {s.get('technical_score')} | {s.get('fundamental_score')} |")
        md.append("")

        # 4. Technical Events
        md.append("## Technical Events")
        md.append(f"- **Breakouts / Technical Events**: {', '.join(breakouts) if breakouts else 'None identified today'}")
        md.append(f"- **Unusual Volume**: {', '.join(unusual_volume) if unusual_volume else 'None identified today'}\n")

        # 5. Sample Forward Probabilities
        md.append("## Probabilistic Forward Expectations (Sample Top Stock)")
        if top_strong:
            top_s = top_strong[0]
            fwd = top_s.get('forward_probabilities', {}).get('forward_horizons', {})
            md.append(f"**Symbol**: `{top_s.get('symbol')}`")
            md.append("| Horizon | Directional Bias | Confidence | Historical Win Rate | Expected Return |")
            md.append("|---|---|---|---|---|")
            for h in ['1d', '3d', '5d', '10d', '20d']:
                if h in fwd:
                    item = fwd[h]
                    md.append(f"| {h} | `{item.get('directional_bias')}` | {item.get('confidence')}% | {int(item.get('historical_win_rate', 0)*100)}% | {item.get('expected_return_pct')}% |")
        md.append("")

        # 6. Data Quality & Diagnostics
        md.append("## Data Quality Summary")
        md.append(f"- **Processed Records**: `{quality_report.get('records_processed', 0)}`")
        md.append(f"- **Valid Records**: `{quality_report.get('records_valid', 0)}`")
        md.append(f"- **Warnings**: `{len(quality_report.get('warnings', []))}`")
        md.append(f"- **Errors**: `{len(quality_report.get('errors', []))}`\n")

        # 7. Research Notes
        md.append("## Research Notes")
        md.append("- All predictions and biases represent empirical historical conditional probabilities rather than guaranteed price targets.")
        md.append("- Feature datasets are preserved in Parquet format without look-ahead bias for machine learning model training.")

        return "\n".join(md)
