import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DailyReportGenerator:
    """Generates human-readable Markdown reports for daily stock market analysis."""

    @staticmethod
    def generate_markdown_report(date_str: str, analysis_data: Dict[str, Any]) -> str:
        market = analysis_data.get("market", {})
        breadth = market.get("breadth", {})
        sectors = analysis_data.get("sectors", [])
        stocks = analysis_data.get("stocks", [])
        data_quality = analysis_data.get("data_quality", {})

        md = []
        md.append(f"# Daily Indian Stock Market Deep Analysis - {date_str}\n")

        # 1. Market Summary
        md.append("## Market Summary\n")
        md.append(f"- **Market Regime**: {market.get('regime', 'N/A')} (Score: {market.get('score', 'N/A')}/100)")
        md.append(f"- **NIFTY Trend**: {market.get('nifty_trend', 'N/A')}")
        md.append(f"- **BANK NIFTY Trend**: {market.get('bank_nifty_trend', 'N/A')}")
        md.append(f"- **Advance / Decline Ratio**: {breadth.get('ad_ratio', 'N/A')} ({breadth.get('advances', 0)} Advances / {breadth.get('declines', 0)} Declines)")
        md.append(f"- **Stocks > 20 DMA**: {breadth.get('pct_above_20dma', 'N/A')}%")
        md.append(f"- **Stocks > 50 DMA**: {breadth.get('pct_above_50dma', 'N/A')}%")
        md.append(f"- **Stocks > 200 DMA**: {breadth.get('pct_above_200dma', 'N/A')}%\n")

        # 2. Sector Performance
        md.append("## Sector Leaders & Laggards\n")
        if sectors:
            md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | Relative Strength | Momentum Score |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for sec in sectors:
                md.append(f"| {sec.get('rank')} | {sec.get('sector')} | {sec.get('daily_return')}% | {sec.get('weekly_return')}% | {sec.get('relative_strength')} | {sec.get('momentum_score')} |")
            md.append("\n")

        # 3. Top Strong & Weak Stocks
        sorted_stocks = sorted(stocks, key=lambda x: x.get("composite_score", 50), reverse=True)
        strong_stocks = sorted_stocks[:5]
        weak_stocks = sorted_stocks[-5:][::-1]

        md.append("## Strong Stocks (Highest Composite Score)\n")
        if strong_stocks:
            md.append("| Symbol | Composite Score | Category | Tech Trend | Momentum | Volume |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for s in strong_stocks:
                comp = s.get("score_components", {})
                md.append(f"| {s.get('symbol')} | {s.get('composite_score')} | {s.get('score_label')} | {comp.get('technical_trend')} | {comp.get('momentum')} | {comp.get('volume')} |")
            md.append("\n")

        md.append("## Weak Stocks (Lowest Composite Score)\n")
        if weak_stocks:
            md.append("| Symbol | Composite Score | Category | Tech Trend | Momentum | Volume |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for s in weak_stocks:
                comp = s.get("score_components", {})
                md.append(f"| {s.get('symbol')} | {s.get('composite_score')} | {s.get('score_label')} | {comp.get('technical_trend')} | {comp.get('momentum')} | {comp.get('volume')} |")
            md.append("\n")

        # 4. Technical Breakouts / Breakdowns & Unusual Volume
        md.append("## Breakouts, Breakdowns & Unusual Volume\n")
        breakouts = [s.get('symbol') for s in stocks if s.get('signals', {}).get('breakout')]
        breakdowns = [s.get('symbol') for s in stocks if s.get('signals', {}).get('breakdown')]
        unusual_vol = [s.get('symbol') for s in stocks if s.get('signals', {}).get('unusual_volume')]

        md.append(f"- **20-Day Breakouts**: {', '.join(breakouts) if breakouts else 'None'}")
        md.append(f"- **20-Day Breakdowns**: {', '.join(breakdowns) if breakdowns else 'None'}")
        md.append(f"- **Unusual Volume Surge (>2x SMA20)**: {', '.join(unusual_vol) if unusual_vol else 'None'}\n")

        # 5. Probabilistic Forward Signals & Research Notes
        md.append("## Historical Analogues & Research Notes\n")
        md.append("Forward-looking signals are derived empirically from historical RSI, volatility, and trend setups. They represent probabilistic research estimates and not guaranteed forecasts.\n")

        # 6. Data Quality Report Summary
        md.append("## Data Quality Audit\n")
        md.append(f"- **Processed Records**: {data_quality.get('records_processed', 0)}")
        md.append(f"- **Valid Records**: {data_quality.get('records_valid', 0)}")
        md.append(f"- **Warnings**: {len(data_quality.get('warnings', []))}")
        md.append(f"- **Errors**: {len(data_quality.get('errors', []))}\n")

        return "\n".join(md)
