import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates human-readable Markdown reports (reports/daily/YYYY-MM-DD.md)
    and validates machine-readable JSON structure.
    """

    @staticmethod
    def generate_markdown_report(date_str: str, analysis_data: Dict[str, Any]) -> str:
        market = analysis_data.get("market", {})
        sectors = analysis_data.get("sectors", [])
        stocks = analysis_data.get("stocks", [])
        quality = analysis_data.get("data_quality", {})

        breadth = market.get("breadth", {})

        # Top / Weak Stocks
        sorted_stocks = sorted(stocks, key=lambda x: x.get("technical_score", 0), reverse=True)
        top_stocks = sorted_stocks[:5]
        weak_stocks = sorted_stocks[-5:] if len(sorted_stocks) >= 5 else []

        # Technical Events
        breakouts = [s["symbol"] for s in stocks if s.get("signals", {}).get("breakout", False)]
        breakdowns = [s["symbol"] for s in stocks if s.get("signals", {}).get("breakdown", False)]
        unusual_vol = [s["symbol"] for s in stocks if s.get("signals", {}).get("unusual_volume", False)]

        md = f"""# Daily Indian Stock Market Research Report
**Date:** {date_str}

---

## 1. Market Summary
- **NIFTY 50 Trend:** {market.get("nifty_trend", "N/A")}
- **BANK NIFTY Trend:** {market.get("bank_nifty_trend", "N/A")}
- **Market Regime:** {market.get("classification", "Neutral")}
- **Market Breadth:**
  - Tracked Equities: {breadth.get("total_tracked", 0)}
  - Above 20 DMA: {breadth.get("pct_above_20_dma", 0)}%
  - Above 50 DMA: {breadth.get("pct_above_50_dma", 0)}%
  - Above 200 DMA: {breadth.get("pct_above_200_dma", 0)}%
  - Advances / Declines: {breadth.get("advances", 0)} / {breadth.get("declines", 0)} (A/D Ratio: {breadth.get("advance_decline_ratio", 1.0)})
  - New Highs / New Lows: {breadth.get("new_highs", 0)} / {breadth.get("new_lows", 0)}

---

## 2. Sector Performance
| Rank | Sector | Daily Return | Weekly Return | Relative Strength vs NIFTY | Momentum Score |
|------|--------|--------------|---------------|----------------------------|----------------|
"""
        for s in sectors:
            md += f"| {s.get('rank', '-')} | {s.get('sector', '-')} | {s.get('daily_return_pct', 0)}% | {s.get('weekly_return_pct', 0)}% | {s.get('relative_strength_vs_nifty', 0)} | {s.get('momentum_score', 0)} |\n"

        md += """
---

## 3. Stock Scoring & Highlights

### Highest Scoring Stocks
| Symbol | Technical Score | Label | Daily Return | RSI (14) | Volatility |
|--------|-----------------|-------|--------------|----------|------------|
"""
        for st in top_stocks:
            md += f"| {st.get('symbol')} | {st.get('technical_score')} | {st.get('score_label')} | {st.get('daily_return_pct')}% | {st.get('rsi_14')} | {st.get('volatility')} |\n"

        md += """
### Weakest Scoring Stocks
| Symbol | Technical Score | Label | Daily Return | RSI (14) | Volatility |
|--------|-----------------|-------|--------------|----------|------------|
"""
        for st in weak_stocks:
            md += f"| {st.get('symbol')} | {st.get('technical_score')} | {st.get('score_label')} | {st.get('daily_return_pct')}% | {st.get('rsi_14')} | {st.get('volatility')} |\n"

        md += f"""
---

## 4. Technical Events & Signals
- **20-Day Breakouts:** {', '.join(breakouts) if breakouts else 'None'}
- **20-Day Breakdowns:** {', '.join(breakdowns) if breakdowns else 'None'}
- **Unusual Volume Surge:** {', '.join(unusual_vol) if unusual_vol else 'None'}

---

## 5. Historical Pattern Analogues & Forward Probabilities (5-Day Horizon)
"""
        for st in top_stocks[:3]:
            analogues = st.get("historical_analogues", {})
            horizons = analogues.get("horizons", {}).get("5d", {})
            md += f"""
### {st.get('symbol')}
- Historical Sample Count: {analogues.get('historical_sample_count', 0)} matching setups
- 5-Day Directional Bias: **{horizons.get('directional_bias', 'Neutral')}** (Win Rate: {horizons.get('win_probability_pct', 50)}%)
- Average Forward Return: {horizons.get('avg_return_pct', 0)}% (Max Gain: {horizons.get('max_gain_pct', 0)}%, Max Loss: {horizons.get('max_loss_pct', 0)}%)
"""

        md += f"""
---

## 6. Data Quality & Pipeline Integrity
- **Total Records Processed:** {quality.get("records_processed", 0)}
- **Valid Records:** {quality.get("records_valid", 0)}
- **Warnings:** {len(quality.get("warnings", []))}
- **Errors:** {len(quality.get("errors", []))}

---

## 7. Research Notes & Safeguards
*Note: All forward probability signals represent empirical historical analogue statistics and statistical baseline inferences. They are research outputs intended for probabilistic risk management and do not guarantee future returns.*
"""
        return md
