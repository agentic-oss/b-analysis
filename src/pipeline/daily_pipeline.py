"""
Daily Market Pipeline Orchestrator.
Executes end-to-end ingestion, validation, indicators computation, market regime & sector analysis,
scoring, pattern analogue matching, feature engineering, prediction, and report generation.
"""
import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.manager import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.scoring.scorer import StockScorer
from src.patterns.analogues import HistoricalPatternEngine
from src.modeling.predictor import PredictorModule
from src.features.builder import FeatureBuilder
from src.backtesting.engine import Backtester
from src.reporting.generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DailyPipeline")


class DailyPipeline:
    """
    Main orchestrator for daily Indian stock market analysis pipeline.
    """

    def __init__(
        self,
        config_path: str = "config/config.json",
        stocks_path: str = "config/stocks.json",
        holidays_path: str = "config/holidays.json"
    ):
        self.config_path = config_path
        self.stocks_path = stocks_path
        self.holidays_path = holidays_path

        with open(config_path) as f:
            self.config = json.load(f)
        with open(stocks_path) as f:
            self.stocks_config = json.load(f)
        with open(holidays_path) as f:
            self.holidays_config = json.load(f)

        self.storage = StorageManager(base_dir=self.config.get("storage", {}).get("base_dir", "data"))
        self.provider = YFinanceProvider(
            max_retries=self.config.get("data_provider", {}).get("max_retries", 3),
            timeout=self.config.get("data_provider", {}).get("timeout_seconds", 30)
        )
        self.validator = DataValidator(quality_dir=self.storage.quality_dir)

    def is_trading_holiday(self, date_str: str) -> bool:
        """
        Checks if given YYYY-MM-DD is listed in Indian market holiday calendar.
        """
        year = date_str.split("-")[0]
        holidays = self.holidays_config.get(year, [])
        return date_str in holidays

    def run(self, run_date: str = None) -> Dict[str, Any]:
        """
        Runs the daily analysis pipeline for the given trading date.
        """
        if run_date is None:
            run_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"=== Starting Daily Pipeline Execution for Date: {run_date} ===")

        if self.is_trading_holiday(run_date):
            logger.info(f"Date {run_date} is a designated market holiday. Skipping pipeline execution.")
            return {"status": "skipped", "reason": "market_holiday", "date": run_date}

        # 1. Fetch Benchmark Index & Sector Indices
        indices_list = [i for i in self.stocks_config.get("indices", []) if i.get("enabled", True)]
        sector_dfs = {}
        nifty_df = pd.DataFrame()
        banknifty_df = pd.DataFrame()

        for idx_item in indices_list:
            sym = idx_item["symbol"]
            logger.info(f"Fetching index data for {sym}...")
            raw_idx = self.provider.get_index_data(sym, period="1y")
            if not raw_idx.empty:
                clean_idx, _ = self.validator.validate_dataframe(raw_idx, ticker=sym)
                enriched_idx = TechnicalIndicators.compute_all(clean_idx)
                if sym == "^NSEI":
                    nifty_df = enriched_idx
                elif sym == "^NSEBANK":
                    banknifty_df = enriched_idx
                else:
                    sector_dfs[sym] = enriched_idx

        # 2. Fetch and Validate Equities Data
        stocks_list = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]
        stocks_dfs = {}
        quality_summaries = []

        for stock_item in stocks_list:
            sym = stock_item["symbol"]
            exchange = stock_item.get("exchange", "NSE")
            logger.info(f"Processing stock data for {sym} ({exchange})...")

            raw_df = self.provider.get_historical_prices(sym, period="1y", exchange=exchange)
            if raw_df.empty:
                quality_summaries.append({
                    "ticker": sym,
                    "records_processed": 0,
                    "records_valid": 0,
                    "warnings": [f"Failed to fetch historical data for {sym}"],
                    "errors": [f"Empty dataframe returned for {sym}"]
                })
                continue

            self.storage.save_raw_data(raw_df, sym, run_date)
            clean_df, summary = self.validator.validate_dataframe(raw_df, ticker=sym)
            quality_summaries.append(summary)

            enriched_df = TechnicalIndicators.compute_all(clean_df)
            self.storage.save_processed_prices(enriched_df, sym)
            stocks_dfs[sym] = enriched_df

        # Generate Quality Report
        quality_report_path = self.validator.generate_quality_report(run_date, quality_summaries)

        # 3. Market Regime Analysis
        market_regime_res = MarketRegimeAnalyzer.analyze(nifty_df, banknifty_df, stocks_dfs)
        logger.info(f"Market Regime: {market_regime_res['market_regime']} (Confidence: {market_regime_res['confidence']}%)")

        # 4. Sector Performance Analysis
        sector_ranks = SectorAnalyzer.analyze_sectors(sector_dfs, nifty_df)

        # 5. Individual Stock Analysis & Scoring
        stock_analyses = []
        all_features = []

        for stock_item in stocks_list:
            sym = stock_item["symbol"]
            df = stocks_dfs.get(sym, pd.DataFrame())
            if df.empty:
                continue

            sec_name = stock_item.get("sector", "")
            matching_sec = next((s for s in sector_ranks if s["symbol"] == sec_name or s["name"] == sec_name), {})

            # Fundamental Data
            fund_info = FundamentalAnalyzer.get_fundamentals(sym, exchange=stock_item.get("exchange", "NSE"))

            # Calculate Composite Score
            scores = StockScorer.calculate_scores(df, market_regime_res, matching_sec, fund_info)

            # Historical Pattern Analogues
            analogues = HistoricalPatternEngine.find_analogues(df)

            # Forward Probabilities & Signals
            forward_signals = PredictorModule.generate_forward_signals(scores["composite_score"], analogues)

            # Feature Matrix for ML
            sec_df = sector_dfs.get(sec_name, pd.DataFrame())
            feat_df = FeatureBuilder.build_feature_matrix(df, nifty_df, sec_df, scores)
            if not feat_df.empty:
                feat_df["ticker"] = sym
                all_features.append(feat_df)

            latest_row = df.iloc[-1]
            stock_analyses.append({
                "symbol": sym,
                "exchange": stock_item.get("exchange", "NSE"),
                "sector": sec_name,
                "latest_close": float(latest_row.get("close", 0)),
                "daily_return_pct": round(float(latest_row.get("daily_return", 0) * 100), 2),
                "composite_score": scores["composite_score"],
                "score_label": scores["label"],
                "score_components": scores["components"],
                "technical_events": {
                    "golden_cross": bool(latest_row.get("golden_cross", False)),
                    "death_cross": bool(latest_row.get("death_cross", False)),
                    "breakout_20d": bool(latest_row.get("breakout_20d", False)),
                    "breakdown_20d": bool(latest_row.get("breakdown_20d", False)),
                    "unusual_volume": bool(latest_row.get("unusual_volume", False))
                },
                "historical_analogues": analogues,
                "forward_signals": forward_signals
            })

        # Save Feature Dataset
        if all_features:
            combined_features = pd.concat(all_features, ignore_index=True)
            self.storage.save_features(combined_features, run_date)

        # 6. Generate Daily Reports & Machine-Readable Output
        quality_summary_agg = {
            "records_processed": sum(s["records_processed"] for s in quality_summaries),
            "records_valid": sum(s["records_valid"] for s in quality_summaries),
            "warnings_count": sum(len(s.get("warnings", [])) for s in quality_summaries),
            "errors_count": sum(len(s.get("errors", [])) for s in quality_summaries)
        }

        markdown_report = ReportGenerator.generate_markdown_report(
            run_date=run_date,
            market_regime=market_regime_res,
            sector_ranks=sector_ranks,
            stock_analyses=stock_analyses,
            quality_summary=quality_summary_agg
        )
        report_file = self.storage.save_daily_report(markdown_report, run_date)

        machine_output = {
            "date": run_date,
            "market": market_regime_res,
            "sectors": sector_ranks,
            "stocks": stock_analyses
        }
        analysis_file = self.storage.save_daily_analysis(machine_output, run_date)

        logger.info(f"=== Pipeline execution complete. Outputs saved: {report_file}, {analysis_file} ===")
        return {
            "status": "success",
            "date": run_date,
            "report_path": report_file,
            "analysis_path": analysis_file,
            "quality_report": quality_report_path
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Execution date (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    pipeline = DailyPipeline()
    res = pipeline.run(run_date=args.date)
    print("Execution Result:", json.dumps(res, indent=2))
