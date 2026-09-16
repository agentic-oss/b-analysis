import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates human-readable Markdown reports and machine-readable JSON outputs.
    Follows required stable schema and includes all analytical sections.
    """

    def generate_markdown_report(
        self,
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_analysis: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]],
        quality_report: Dict[str, Any],
        model_metrics: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> str:
        md = []
        md.append(f"# Daily Indian Stock Market Research & Analysis Report - {date_str}\n")
        md.append(f"*Generated on:* {date_str} | *Market:* NSE & BSE Equities\n")

        # 1. Market Summary
        md.append("## Market Summary\n")
        m = market_analysis
        mb = m.get("market_breadth", {})
        md.append(f"- **NIFTY 50 Close:** {m.get('nifty_close', 'N/A')} (20 DMA: {m.get('nifty_sma_20', 'N/A')}, 50 DMA: {m.get('nifty_sma_50', 'N/A')}, 200 DMA: {m.get('nifty_sma_200', 'N/A')})")
        md.append(f"- **NIFTY Trend:** {m.get('nifty_trend', 'N/A')}")
        md.append(f"- **BANK NIFTY Trend:** {m.get('bank_nifty_trend', 'N/A')}")
        md.append(f"- **Market Regime:** **{m.get('regime', 'N/A')}** (Score: {m.get('regime_score', 50)}/100)")
        md.append(f"- **Market Breadth:** AD Ratio: {mb.get('advance_decline_ratio', 1.0)} | % > 20 DMA: {mb.get('pct_above_20dma', 0)}% | % > 50 DMA: {mb.get('pct_above_50dma', 0)}% | % > 200 DMA: {mb.get('pct_above_200dma', 0)}%")
        md.append(f"- **New Highs / Lows (20D):** Highs: {mb.get('new_20d_highs', 0)} | Lows: {mb.get('new_20d_lows', 0)}\n")

        # 2. Sector Leaders & Laggards
        md.append("## Sector Analysis & Rankings\n")
        md.append("| Rank | Sector | Daily Return (%) | Weekly Return (%) | Monthly Return (%) | Relative Strength vs NIFTY (1D) | Momentum Score |")
        md.append("|------|--------|------------------|-------------------|--------------------|----------------------------------|----------------|")
        for s in sector_analysis:
            md.append(f"| {s.get('rank')} | {s.get('sector')} | {s.get('daily_return')}% | {s.get('weekly_return')}% | {s.get('monthly_return')}% | {s.get('rs_vs_nifty_1d')}% | {s.get('momentum_score')} |")
        md.append("\n")

        # 3. Strong & Weak Stocks
        sorted_stocks = sorted(stock_analyses, key=lambda x: x.get("composite_score", 0), reverse=True)
        top_strong = sorted_stocks[:5]
        top_weak = sorted_stocks[-5:][::-1]

        md.append("## Strong Stocks (Top Composite Scores)\n")
        md.append("| Symbol | Score | Rating | Tech Score | Momentum Score | Relative Vol | 1D Return | Bias (5D) |")
        md.append("|--------|-------|--------|------------|----------------|--------------|-----------|-----------|")
        for st in top_strong:
            c = st.get("score_components", {})
            b = st.get("directional_bias", {}).get("5d", "Neutral")
            md.append(f"| {st.get('symbol')} | {st.get('composite_score')} | {st.get('score_label')} | {c.get('technical_trend')} | {c.get('momentum')} | {st.get('relative_volume')} | {st.get('return_1d_pct')}% | {b} |")
        md.append("\n")

        md.append("## Weak Stocks (Lowest Composite Scores)\n")
        md.append("| Symbol | Score | Rating | Tech Score | Momentum Score | Relative Vol | 1D Return | Bias (5D) |")
        md.append("|--------|-------|--------|------------|----------------|--------------|-----------|-----------|")
        for st in top_weak:
            c = st.get("score_components", {})
            b = st.get("directional_bias", {}).get("5d", "Neutral")
            md.append(f"| {st.get('symbol')} | {st.get('composite_score')} | {st.get('score_label')} | {c.get('technical_trend')} | {c.get('momentum')} | {st.get('relative_volume')} | {st.get('return_1d_pct')}% | {b} |")
        md.append("\n")

        # 4. Technical Events: Breakouts, Breakdowns & Unusual Volume
        breakouts = [st['symbol'] for st in stock_analyses if st.get("breakout_20d")]
        breakdowns = [st['symbol'] for st in stock_analyses if st.get("breakdown_20d")]
        unusual_vol = [st['symbol'] for st in stock_analyses if st.get("relative_volume", 0) > 2.0]

        md.append("## Technical Events & Signals\n")
        md.append(f"- **20-Day Breakouts:** {', '.join(breakouts) if breakouts else 'None detected'}")
        md.append(f"- **20-Day Breakdowns:** {', '.join(breakdowns) if breakdowns else 'None detected'}")
        md.append(f"- **Unusual Volume Spikes (>2x 20DMA Volume):** {', '.join(unusual_vol) if unusual_vol else 'None detected'}\n")

        # 5. Historical Analogues & Forward Probabilities Summary
        md.append("## Historical Analogue & Empirical Forward Probabilities\n")
        md.append("Historical setups matching current RSI/volatility profiles and empirical forward returns:\n")
        md.append("| Symbol | Matches Found | 1D Win Prob (%) | 5D Win Prob (%) | 20D Win Prob (%) | 5D Expected Return (%) |")
        md.append("|--------|---------------|-----------------|-----------------|------------------|------------------------|")
        for st in sorted_stocks[:8]:
            an = st.get("historical_analogues", {})
            fp = an.get("forward_probabilities", {})
            f1 = fp.get("1d", {})
            f5 = fp.get("5d", {})
            f20 = fp.get("20d", {})
            md.append(f"| {st.get('symbol')} | {an.get('matches_found', 0)} | {f1.get('win_probability', 'N/A')}% | {f5.get('win_probability', 'N/A')}% | {f20.get('win_probability', 'N/A')}% | {f5.get('mean_return', 'N/A')}% |")
        md.append("\n")

        # 6. ML Model & Backtest Performance Baseline
        md.append("## ML Research & Backtest Baselines\n")
        md.append(f"- **ML Model Accuracy (5D Direction):** {model_metrics.get('accuracy', 0.0) * 100:.2f}% | **F1 Score:** {model_metrics.get('f1_score', 0.0):.4f}")
        md.append(f"- **Backtest Strategy Cumulative Return:** {backtest_results.get('cumulative_return_pct', 0.0)}% | **Max Drawdown:** {backtest_results.get('max_drawdown_pct', 0.0)}% | **Sharpe Ratio:** {backtest_results.get('sharpe_ratio', 0.0)}")
        md.append(f"- **Strategy Win Rate:** {backtest_results.get('win_rate_pct', 0.0)}% across {backtest_results.get('total_trades', 0)} trades\n")

        # 7. Data Quality & Research Safeguards
        md.append("## Data Quality & Research Safeguards\n")
        md.append(f"- **Symbols Processed:** {quality_report.get('symbols_processed', 0)}")
        md.append(f"- **Records Processed:** {quality_report.get('records_processed', 0)} (Valid: {quality_report.get('records_valid', 0)})")
        md.append(f"- **Warnings Flagged:** {quality_report.get('warnings_count', 0)} | **Errors Flagged:** {quality_report.get('errors_count', 0)}")
        md.append("\n*Research Safeguard Disclaimer:* All directional signals and forward return statistics are empirical probabilistic outputs derived from historical analogues. They are strictly research outputs and do not constitute guaranteed financial forecasts or trade recommendations.\n")

        return "\n".join(md)

    def generate_json_output(
        self,
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_analysis: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]],
        quality_report: Dict[str, Any],
        model_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "date": date_str,
            "market": market_analysis,
            "sectors": sector_analysis,
            "stocks": stock_analyses,
            "data_quality": quality_report,
            "ml_research_baseline": model_metrics,
        }
