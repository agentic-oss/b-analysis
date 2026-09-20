"""Report Generator for daily Markdown and JSON analysis outputs."""

import json
from typing import Dict, Any, List

class ReportGenerator:
    """Generates structured human-readable Markdown reports and machine-readable JSON files."""

    @staticmethod
    def generate_json_output(date_str: str, market_data: Dict[str, Any], sectors_data: List[Dict[str, Any]], stocks_data: List[Dict[str, Any]], quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """Builds machine-readable JSON payload following stable schema."""
        return {
            "date": date_str,
            "market": market_data,
            "sectors": sectors_data,
            "stocks": stocks_data,
            "data_quality": quality_data
        }

    @staticmethod
    def generate_markdown_report(date_str: str, market_data: Dict[str, Any], sectors_data: List[Dict[str, Any]], stocks_data: List[Dict[str, Any]], quality_data: Dict[str, Any]) -> str:
        """Builds comprehensive human-readable Markdown daily market report."""
        breadth = market_data.get('breadth', {})
        nifty = market_data.get('nifty_summary', {})

        md = []
        md.append(f"# Daily Indian Stock Market Analysis & Research Report ({date_str})\n")

        # 1. Market Summary
        md.append("## Market Summary")
        md.append(f"- **Market Regime**: `{market_data.get('regime', 'Neutral')}`")
        md.append(f"- **Assessment**: {market_data.get('explanation', 'N/A')}")
        md.append(f"- **NIFTY Trend**: {nifty.get('trend', 'N/A')} (20D Volatility: {nifty.get('volatility_20d', 0)*100:.1f}%)")
        md.append(f"- **Market Breadth**: Advances: {breadth.get('advances', 0)} | Declines: {breadth.get('declines', 0)} | A/D Ratio: {breadth.get('ad_ratio', 0)}")
        md.append(f"- **Moving Average Coverage**: {breadth.get('pct_above_20dma', 0)}% above 20 DMA | {breadth.get('pct_above_50dma', 0)}% above 50 DMA | {breadth.get('pct_above_200dma', 0)}% above 200 DMA\n")

        # 2. Sector Leaders & Laggards
        md.append("## Sector Analysis")
        if sectors_data:
            md.append("| Rank | Sector | Daily Return | Weekly Return | Relative Strength vs NIFTY | Momentum Score |")
            md.append("|---|---|---|---|---|---|")
            for sec in sectors_data:
                md.append(f"| {sec.get('rank')} | {sec.get('sector')} | {sec.get('daily_return_pct')}% | {sec.get('weekly_return_pct')}% | {sec.get('relative_strength_1d')}% | {sec.get('momentum_score')} |")
        else:
            md.append("No sector data available.")
        md.append("\n")

        # Sort stocks by score for Top / Bottom lists
        sorted_stocks = sorted(stocks_data, key=lambda x: x.get('composite_score', 0), reverse=True)

        # 3. Top Strong Stocks
        md.append("## Strong Stocks (Top Composite Scores)")
        md.append("| Symbol | Score | Rating | Technical Score | Momentum | 1D Return | 5D Bias |")
        md.append("|---|---|---|---|---|---|---|")
        for s in sorted_stocks[:5]:
            fwd_5d = s.get('forward_probabilities', {}).get('signals', {}).get('5d', {})
            md.append(f"| **{s.get('symbol')}** | {s.get('composite_score')} | {s.get('score_label')} | {s.get('components', {}).get('technical_trend_score')} | {s.get('components', {}).get('momentum_score')} | {s.get('daily_return_pct')}% | {fwd_5d.get('bias', 'N/A')} ({fwd_5d.get('confidence', 0)}%) |")
        md.append("\n")

        # 4. Weak Stocks
        md.append("## Weak Stocks (Lowest Composite Scores)")
        md.append("| Symbol | Score | Rating | Technical Score | Momentum | 1D Return | 5D Bias |")
        md.append("|---|---|---|---|---|---|---|")
        for s in sorted_stocks[-5:]:
            fwd_5d = s.get('forward_probabilities', {}).get('signals', {}).get('5d', {})
            md.append(f"| **{s.get('symbol')}** | {s.get('composite_score')} | {s.get('score_label')} | {s.get('components', {}).get('technical_trend_score')} | {s.get('components', {}).get('momentum_score')} | {s.get('daily_return_pct')}% | {fwd_5d.get('bias', 'N/A')} ({fwd_5d.get('confidence', 0)}%) |")
        md.append("\n")

        # 5. Technical Events (Breakouts & Unusual Volume)
        breakouts = [s['symbol'] for s in stocks_data if s.get('breakout_20d')]
        breakdowns = [s['symbol'] for s in stocks_data if s.get('breakdown_20d')]
        high_vol = [s['symbol'] for s in stocks_data if s.get('relative_volume', 1.0) >= 1.8]

        md.append("## Key Technical Events & Unusual Volume")
        md.append(f"- **20-Day Breakouts**: {', '.join(breakouts) if breakouts else 'None'}")
        md.append(f"- **20-Day Breakdowns**: {', '.join(breakdowns) if breakdowns else 'None'}")
        md.append(f"- **Unusual Volume (Rel Vol >= 1.8x)**: {', '.join(high_vol) if high_vol else 'None'}\n")

        # 6. Historical Analogues & Forward Probabilities Summary
        md.append("## Empirical Historical Analogues & Forward Probabilities")
        md.append("Sample statistical analogue forward returns based on past Euclidean similarity in RSI, volatility, and moving average structure:")
        if stocks_data:
            sample_stock = sorted_stocks[0]
            analogues = sample_stock.get('historical_analogues', {}).get('horizons', {})
            md.append(f"\n### Sample Analogue Breakdown: **{sample_stock.get('symbol')}**")
            md.append("| Horizon | Avg Forward Return | Median Return | Win Rate | Max Gain | Max Loss |")
            md.append("|---|---|---|---|---|---|")
            for h, h_data in analogues.items():
                md.append(f"| {h} | {h_data.get('avg_forward_return_pct')}% | {h_data.get('median_forward_return_pct')}% | {h_data.get('win_rate_pct')}% | {h_data.get('max_gain_pct')}% | {h_data.get('max_loss_pct')}% |")
        md.append("\n")

        # 7. Data Quality
        md.append("## Data Quality Summary")
        md.append(f"- **Processed Records**: {quality_data.get('records_processed', 0)}")
        md.append(f"- **Valid Records**: {quality_data.get('records_valid', 0)}")
        md.append(f"- **Warnings**: {', '.join(quality_data.get('warnings', [])) if quality_data.get('warnings') else 'None'}")
        md.append(f"- **Errors**: {', '.join(quality_data.get('errors', [])) if quality_data.get('errors') else 'None'}\n")

        # 8. Research Notes Safeguards
        md.append("## Research Notes & Disclaimer")
        md.append("> **Safeguard Notice**: Forward-looking movement signals, analogue probabilities, and confidence scores are empirical research statistics generated from historical price distribution patterns. They do not constitute financial advice or guaranteed market outcomes.")

        return "\n".join(md)
