"""
Daily Report Generator module producing human-readable Markdown reports
and machine-readable JSON analysis files.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_json_analysis(
    run_date: str,
    market_regime: Dict[str, Any],
    sectors: List[Dict[str, Any]],
    stocks_summary: List[Dict[str, Any]],
    quality_report: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates structured machine-readable JSON output matching schema."""
    return {
        "date": run_date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": market_regime,
        "sectors": sectors,
        "stocks": stocks_summary,
        "data_quality": {
            "records_processed": quality_report.get("records_processed", 0),
            "records_valid": quality_report.get("records_valid", 0),
            "total_warnings": quality_report.get("total_warnings", 0),
            "total_errors": quality_report.get("total_errors", 0)
        }
    }


def generate_markdown_report(
    run_date: str,
    market_regime: Dict[str, Any],
    sectors: List[Dict[str, Any]],
    stocks_summary: List[Dict[str, Any]],
    quality_report: Dict[str, Any]
) -> str:
    """Generates daily research-oriented Markdown market report."""
    md = []
    md.append(f"# Daily Indian Stock Market Research Report - {run_date}\n")
    md.append(f"*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC*\n")

    # 1. Market Summary
    md.append("## 1. Market Summary")
    md.append(f"- **Market Regime:** `{market_regime.get('regime', 'Neutral')}` (Composite Score: {market_regime.get('composite_score', 50)}/100)")
    md.append(f"- **NIFTY 50:** {market_regime.get('nifty_close', 'N/A')} ({market_regime.get('nifty_1d_return', 0):+.2f}% 1D) | Trend: `{market_regime.get('nifty_trend', 'N/A')}`")
    md.append(f"- **BANK NIFTY:** {market_regime.get('banknifty_close', 'N/A')} ({market_regime.get('banknifty_1d_return', 0):+.2f}% 1D) | Trend: `{market_regime.get('banknifty_trend', 'N/A')}`")
    md.append(f"- **NIFTY Volatility (20D):** {market_regime.get('nifty_volatility_20d', 'N/A')}%")

    breadth = market_regime.get("breadth", {})
    md.append(f"- **Market Breadth:** Advance/Decline Ratio = {breadth.get('advance_decline_ratio', 1.0)} ({breadth.get('advances', 0)} Advances / {breadth.get('declines', 0)} Declines)")
    md.append(f"- **Stocks Above Moving Averages:** 20 DMA: {breadth.get('pct_above_20dma', 0)}% | 50 DMA: {breadth.get('pct_above_50dma', 0)}% | 200 DMA: {breadth.get('pct_above_200dma', 0)}%")
    md.append(f"- **20-Day Highs/Lows:** New Highs: {breadth.get('new_20d_highs', 0)} | New Lows: {breadth.get('new_20d_lows', 0)}\n")

    # 2. Sector Performance
    md.append("## 2. Sector Rankings & Performance")
    md.append("| Rank | Sector | Daily Return | Weekly Return | Monthly Return | Relative Strength vs NIFTY | Momentum Score |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for sec in sectors:
        md.append(f"| {sec.get('rank', '-')} | {sec.get('sector')} | {sec.get('daily_return', 0):+.2f}% | {sec.get('weekly_return', 0):+.2f}% | {sec.get('monthly_return', 0):+.2f}% | {sec.get('relative_strength_5d', 0):+.2f}% | {sec.get('momentum_score', 0)}/100 |")
    md.append("")

    # Sector Leaders & Laggards
    if sectors:
        md.append(f"- **Sector Leader:** {sectors[0].get('sector')} ({sectors[0].get('daily_return'):+.2f}%)")
        md.append(f"- **Sector Laggard:** {sectors[-1].get('sector')} ({sectors[-1].get('daily_return'):+.2f}%)\n")

    # 3. Strong & Weak Stocks
    sorted_stocks = sorted(stocks_summary, key=lambda x: x.get("composite_score", 0), reverse=True)
    strong_stocks = sorted_stocks[:5]
    weak_stocks = sorted_stocks[-5:] if len(sorted_stocks) >= 5 else []

    md.append("## 3. Top Scoring Stocks (Strongest Setups)")
    md.append("| Symbol | Composite Score | Label | 1D Return | Trend | RSI (14) | Volatility |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for st in strong_stocks:
        md.append(f"| `{st.get('symbol')}` | **{st.get('composite_score')}** | {st.get('label')} | {st.get('daily_return', 0):+.2f}% | {st.get('trend')} | {st.get('rsi_14')} | {st.get('volatility_20d')}% |")
    md.append("")

    md.append("## 4. Lowest Scoring Stocks (Weakest Setups)")
    md.append("| Symbol | Composite Score | Label | 1D Return | Trend | RSI (14) | Volatility |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for st in reversed(weak_stocks):
        md.append(f"| `{st.get('symbol')}` | **{st.get('composite_score')}** | {st.get('label')} | {st.get('daily_return', 0):+.2f}% | {st.get('trend')} | {st.get('rsi_14')} | {st.get('volatility_20d')}% |")
    md.append("")

    # 5. Technical Events (Breakouts, Breakdowns, Volume)
    md.append("## 5. Technical Events & Signals")
    breakouts = [st["symbol"] for st in stocks_summary if st.get("signals", {}).get("breakout")]
    breakdowns = [st["symbol"] for st in stocks_summary if st.get("signals", {}).get("breakdown")]
    unusual_vol = [f"{st['symbol']} ({st.get('relative_volume')}x)" for st in stocks_summary if st.get("signals", {}).get("unusual_volume")]

    md.append(f"- **Price Breakouts:** {', '.join(breakouts) if breakouts else 'None'}")
    md.append(f"- **Price Breakdowns:** {', '.join(breakdowns) if breakdowns else 'None'}")
    md.append(f"- **Unusual Volume Activity:** {', '.join(unusual_vol) if unusual_vol else 'None'}\n")

    # 6. Sample Historical Analogues & Probabilistic Forecasts
    md.append("## 6. Sample Historical Analogues & Forward Probabilities")
    if strong_stocks:
        sample_st = strong_stocks[0]
        md.append(f"### Historical Setup Analysis for `{sample_st.get('symbol')}`")
        analogues = sample_st.get("historical_analogues", {})
        md.append(f"- **Matching Historical Analogues Found:** {analogues.get('num_analogues', 0)}")

        horizons = analogues.get("horizons", {})
        md.append("| Horizon | Avg Return | Positive Win Rate | Max Gain | Max Loss | Directional Bias |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for h_key, h_data in horizons.items():
            bias_info = sample_st.get("signals_forecast", {}).get(h_key, {})
            md.append(f"| {h_key.upper()} | {h_data.get('avg_forward_return', 0):+.2f}% | {h_data.get('pos_probability_pct', 50)}% | +{h_data.get('max_gain', 0)}% | {h_data.get('max_loss', 0)}% | **{bias_info.get('directional_bias', 'Neutral')}** |")
        md.append("")

    # 7. Data Quality & Pipeline Health
    md.append("## 7. Data Quality & Pipeline Diagnostics")
    md.append(f"- **Total Records Processed:** {quality_report.get('records_processed', 0)}")
    md.append(f"- **Valid Records:** {quality_report.get('records_valid', 0)}")
    md.append(f"- **Quality Warnings:** {quality_report.get('total_warnings', 0)}")
    md.append(f"- **Quality Errors:** {quality_report.get('total_errors', 0)}\n")

    # 8. Research Notes
    md.append("## 8. Research Notes & Disclaimer")
    md.append("- All forward probabilities and directional bias labels represent empirical statistical distributions derived from past analogues.")
    md.append("- No outputs constitute guaranteed financial predictions or trading advice.")
    md.append("- Prevented look-ahead bias across feature engineering and walk-forward prediction layers.\n")

    return "\n".join(md)
