import json
from typing import Dict, Any, List

class ReportGenerator:
    """
    Generates human-readable Markdown daily report (`reports/daily/YYYY-MM-DD.md`)
    and stable machine-readable JSON output (`data/analysis/daily/YYYY-MM-DD.json`).
    """

    def generate_markdown_report(
        self,
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_analysis: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> str:
        md = []
        md.append(f"# Daily Indian Stock Market Research Report ({date_str})\n")

        # 1. Market Summary
        md.append("## Market Summary")
        regime = market_analysis.get('regime', 'Neutral')
        reg_score = market_analysis.get('regime_score', 50.0)
        nifty_close = market_analysis.get('nifty_close', 0.0)
        nifty_ret = market_analysis.get('nifty_return_1d', 0.0) * 100
        nifty_vol = market_analysis.get('nifty_volatility_20d', 0.0) * 100
        breadth = market_analysis.get('market_breadth', {})

        md.append(f"- **Market Regime:** {regime} (Regime Score: {reg_score}/100)")
        md.append(f"- **NIFTY 50:** {nifty_close:,.2f} ({nifty_ret:+.2f}%)")
        md.append(f"- **BANK NIFTY:** {market_analysis.get('bank_nifty_close', 0.0):,.2f}")
        md.append(f"- **NIFTY 20-Day Annualized Volatility:** {nifty_vol:.2f}%")
        md.append(f"- **Market Breadth:** Advances: {breadth.get('advances', 0)} | Declines: {breadth.get('declines', 0)} (A/D Ratio: {breadth.get('advance_decline_ratio', 1.0)})")
        md.append(f"- **Stocks above 50 DMA:** {breadth.get('pct_above_50dma', 0.0)}%\n")

        # 2. Sector Performance
        md.append("## Sector Performance Rankings")
        md.append("| Rank | Sector | Daily Return | Weekly Return | Rel. Strength vs NIFTY | Momentum Score |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for s in sector_analysis:
            r = s.get('rank', '-')
            sec = s.get('sector', '')
            d_ret = s.get('daily_return', 0.0) * 100
            w_ret = s.get('weekly_return', 0.0) * 100
            rs = s.get('relative_strength_vs_nifty', 0.0) * 100
            score = s.get('momentum_score', 50.0)
            md.append(f"| {r} | {sec} | {d_ret:+.2f}% | {w_ret:+.2f}% | {rs:+.2f}% | {score:.1f} |")
        md.append("\n")

        # 3. Top & Bottom Performing / Scoring Stocks
        sorted_stocks = sorted(stock_analyses, key=lambda x: x.get('composite_score', 0), reverse=True)
        top_stocks = sorted_stocks[:5]
        bottom_stocks = sorted_stocks[-5:]

        md.append("## Strongest Stocks (Top Composite Scores)")
        md.append("| Symbol | Sector | Composite Score | Rating | Daily Return | RSI (14) | Events |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in top_stocks:
            sym = st.get('symbol', '')
            sec = st.get('sector', '')
            sc = st.get('composite_score', 0)
            lbl = st.get('rating', '')
            ret = st.get('daily_return', 0.0) * 100
            rsi = st.get('rsi_14', 50.0)
            evts = ", ".join(st.get('technical_events', [])) or "None"
            md.append(f"| {sym} | {sec} | {sc:.1f} | {lbl} | {ret:+.2f}% | {rsi:.1f} | {evts} |")
        md.append("\n")

        md.append("## Weakest Stocks (Bottom Composite Scores)")
        md.append("| Symbol | Sector | Composite Score | Rating | Daily Return | RSI (14) | Events |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in bottom_stocks:
            sym = st.get('symbol', '')
            sec = st.get('sector', '')
            sc = st.get('composite_score', 0)
            lbl = st.get('rating', '')
            ret = st.get('daily_return', 0.0) * 100
            rsi = st.get('rsi_14', 50.0)
            evts = ", ".join(st.get('technical_events', [])) or "None"
            md.append(f"| {sym} | {sec} | {sc:.1f} | {lbl} | {ret:+.2f}% | {rsi:.1f} | {evts} |")
        md.append("\n")

        # 4. Historical Analogues & Probabilistic Forecast Summary
        md.append("## Probabilistic Historical Analogue Forward Expectations")
        md.append("*(Empirical probabilities based on historical matching setups)*\n")
        md.append("| Symbol | 1D Bias | 1D Pos. Prob | 5D Bias | 5D Pos. Prob | 20D Bias | 20D Pos. Prob |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for st in sorted_stocks[:8]:
            sym = st.get('symbol', '')
            sig = st.get('signals', {}).get('signals', {})
            d1 = sig.get('1d', {})
            d5 = sig.get('5d', {})
            d20 = sig.get('20d', {})
            md.append(f"| {sym} | {d1.get('directional_bias', 'Neutral')} | {d1.get('blended_positive_probability', 0.5)*100:.1f}% | {d5.get('directional_bias', 'Neutral')} | {d5.get('blended_positive_probability', 0.5)*100:.1f}% | {d20.get('directional_bias', 'Neutral')} | {d20.get('blended_positive_probability', 0.5)*100:.1f}% |")
        md.append("\n")

        # 5. Data Quality Report
        md.append("## Data Quality Summary")
        md.append(f"- **Records Processed:** {quality_report.get('records_processed', 0)}")
        md.append(f"- **Valid Records:** {quality_report.get('records_valid', 0)}")
        md.append(f"- **Warnings:** {len(quality_report.get('warnings', []))}")
        md.append(f"- **Errors:** {len(quality_report.get('errors', []))}\n")

        # 6. Research Notes & Disclaimer
        md.append("## Research Notes & Methodology")
        md.append("This daily report is generated automatically using deterministic technical indicators, historical analogue pattern matching, transparent component scoring, and walk-forward validation.")
        md.append("**Disclaimer:** All forward outputs represent probabilistic statistical estimates based on historical observations. They are intended for market research and analytics purposes and do not constitute financial advice or guaranteed price forecasts.")

        return "\n".join(md)

    def generate_json_output(
        self,
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_analysis: List[Dict[str, Any]],
        stock_analyses: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates machine-readable JSON schema output.
        """
        clean_stocks = []
        for s in stock_analyses:
            clean_stocks.append({
                "symbol": s.get("symbol"),
                "sector": s.get("sector"),
                "close": s.get("close"),
                "daily_return": s.get("daily_return"),
                "rsi_14": s.get("rsi_14"),
                "composite_score": s.get("composite_score"),
                "rating": s.get("rating"),
                "score_components": s.get("score_components"),
                "technical_events": s.get("technical_events"),
                "support_levels": s.get("support_levels"),
                "resistance_levels": s.get("resistance_levels"),
                "fundamentals": s.get("fundamentals"),
                "historical_analogues": s.get("historical_analogues"),
                "forward_probabilities": s.get("signals")
            })

        return {
            "date": date_str,
            "market": market_analysis,
            "sectors": sector_analysis,
            "stocks": clean_stocks,
            "data_quality": quality_report
        }
