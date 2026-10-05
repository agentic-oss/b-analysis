"""
Daily Analysis Report Generator for Machine-Readable JSON and Markdown Reports.
"""

from typing import Dict, List, Any
import json
import pandas as pd


class ReportGenerator:
    """Generates structured machine-readable JSON analysis and human-readable Markdown report."""

    @staticmethod
    def generate_json_output(
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_analysis: List[Dict[str, Any]],
        stock_results: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates machine-readable daily analysis dictionary matching schema."""
        return {
            "date": date_str,
            "market": market_analysis,
            "sectors": sector_analysis,
            "stocks": stock_results,
            "data_quality": {
                "records_processed": quality_report.get("records_processed", 0),
                "records_valid": quality_report.get("records_valid", 0),
                "warnings_count": quality_report.get("warnings_count", 0),
                "errors_count": quality_report.get("errors_count", 0)
            }
        }

    @staticmethod
    def generate_markdown_report(
        date_str: str,
        market_analysis: Dict[str, Any],
        sector_analysis: List[Dict[str, Any]],
        stock_results: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> str:
        """Generates human-readable Markdown report."""
        breadth = market_analysis.get("breadth", {})

        # Sort stocks by score
        sorted_stocks = sorted(stock_results, key=lambda x: x.get("score", {}).get("composite_score", 0), reverse=True)
        strong_stocks = sorted_stocks[:5]
        weak_stocks = sorted_stocks[-5:][::-1] if len(sorted_stocks) >= 5 else []

        md = []
        md.append(f"# Daily Indian Stock Market Deep Analysis Report - {date_str}\n")

        # 1. Market Summary
        md.append("## 1. Market Summary & Regime Analysis\n")
        md.append(f"- **Market Regime:** `{market_analysis.get('regime', 'Neutral')}` (Confidence: {market_analysis.get('confidence', 50)}%)")
        md.append(f"- **NIFTY Trend:** {market_analysis.get('nifty_trend', 'N/A')}")
        md.append(f"- **BANK NIFTY Trend:** {market_analysis.get('bank_nifty_trend', 'N/A')}")
        md.append(f"- **Annualized Volatility:** {market_analysis.get('nifty_volatility_annualized', 0)}%\n")

        md.append("### Market Breadth")
        md.append(f"- **Advances / Declines:** {breadth.get('advances', 0)} / {breadth.get('declines', 0)} (A/D Ratio: {breadth.get('advance_decline_ratio', 0)})")
        md.append(f"- **Stocks > 20 DMA:** {breadth.get('pct_above_20_dma', 0)}%")
        md.append(f"- **Stocks > 50 DMA:** {breadth.get('pct_above_50_dma', 0)}%")
        md.append(f"- **Stocks > 200 DMA:** {breadth.get('pct_above_200_dma', 0)}%")
        md.append(f"- **20-Day New Highs / Lows:** {breadth.get('new_highs_20d', 0)} / {breadth.get('new_lows_20d', 0)}\n")

        # 2. Sector Performance
        md.append("## 2. Sector Performance & Ranking\n")
        md.append("| Rank | Sector | Daily Return | Weekly Return | RS vs NIFTY (1D) | Momentum Score |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for sec in sector_analysis:
            md.append(
                f"| {sec.get('rank', '-')} | {sec.get('sector')} | {sec.get('daily_return_pct')}% | "
                f"{sec.get('weekly_return_pct')}% | {sec.get('relative_strength_1d')} | {sec.get('momentum_score')} |"
            )
        md.append("\n")

        # 3. Strong & Weak Stocks
        md.append("## 3. Stock Score Highlights\n")
        md.append("### Top Scoring Stocks")
        md.append("| Symbol | Composite Score | Label | Regime | 5D Directional Bias |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for st in strong_stocks:
            sc = st.get("score", {})
            pred = st.get("forward_probabilities", {})
            md.append(f"| {st.get('symbol')} | {sc.get('composite_score')} | {sc.get('label')} | {st.get('market_regime')} | {pred.get('bias_5d', 'Neutral')} |")
        md.append("\n")

        if weak_stocks:
            md.append("### Weakest Stocks")
            md.append("| Symbol | Composite Score | Label | Regime | 5D Directional Bias |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for st in weak_stocks:
                sc = st.get("score", {})
                pred = st.get("forward_probabilities", {})
                md.append(f"| {st.get('symbol')} | {sc.get('composite_score')} | {sc.get('label')} | {st.get('market_regime')} | {pred.get('bias_5d', 'Neutral')} |")
            md.append("\n")

        # 4. Breakouts & Technical Events
        md.append("## 4. Technical Breakouts & Unusual Signals\n")
        has_signals = False
        for st in stock_results:
            signals = st.get("signals", [])
            if signals:
                has_signals = True
                md.append(f"- **{st.get('symbol')}:** {', '.join(signals)}")
        if not has_signals:
            md.append("- No major technical breakout or unusual volume signals detected today.")
        md.append("\n")

        # 5. Data Quality Diagnostics
        md.append("## 5. Data Quality Diagnostics\n")
        md.append(f"- **Total Records Processed:** {quality_report.get('records_processed', 0)}")
        md.append(f"- **Valid Records:** {quality_report.get('records_valid', 0)}")
        md.append(f"- **Warnings Count:** {quality_report.get('warnings_count', 0)}")
        md.append(f"- **Errors Count:** {quality_report.get('errors_count', 0)}\n")

        # 6. Research Notes & Safeguards
        md.append("## 6. Research Notes & Disclaimer\n")
        md.append("This analysis engine generates empirical probabilistic signals derived from historical analogues and quantitative indicator models. Outputs represent statistical research observations and must **not** be treated as guaranteed price forecasts or financial advice.")

        return "\n".join(md)
