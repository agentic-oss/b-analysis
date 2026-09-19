"""
Daily Indian Stock Market Data & Deep Analysis Pipeline Orchestrator.
Automates end-to-end execution: Ingestion, Validation, Storage, Technicals,
Market Regime, Sector Analysis, Scoring, Historical Patterns, Feature Engineering,
ML evaluation, Backtesting, Reporting, and Git Committing.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage import StorageManager
from src.indicators.indicators import TechnicalAnalysisEngine
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.scoring.scorer import StockScorer
from src.patterns.matcher import PatternAnalogueMatcher
from src.features.builder import FeatureEngineer
from src.modeling.pipeline import PredictiveModelPipeline
from src.backtesting.engine import BacktestEngine
from src.reporting.generator import DailyReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("DailyPipeline")


class DailyMarketPipeline:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.stocks_config = self._load_json(os.path.join(config_dir, "stocks.json"))
        self.app_config = self._load_json(os.path.join(config_dir, "config.json"))
        self.holidays_config = self._load_json(os.path.join(config_dir, "holidays.json"))

        self.provider = YFinanceProvider(
            max_retries=self.app_config["pipeline"]["max_retries"],
            retry_backoff_sec=self.app_config["pipeline"]["retry_backoff_sec"]
        )
        self.validator = DataValidator()
        self.storage = StorageManager(
            base_dir=self.app_config["storage"]["base_dir"],
            reports_dir=self.app_config["storage"]["reports_dir"]
        )
        self.tech_engine = TechnicalAnalysisEngine(self.app_config.get("indicator_params"))
        self.fund_analyzer = FundamentalAnalyzer()
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.scorer = StockScorer()
        self.pattern_matcher = PatternAnalogueMatcher()
        self.feature_builder = FeatureEngineer()
        self.ml_pipeline = PredictiveModelPipeline()
        self.report_generator = DailyReportGenerator()

    def _load_json(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_trading_holiday(self, date_str: str) -> bool:
        return date_str in self.holidays_config.get("holidays", [])

    def run(self, target_date: str, commit_results: bool = False) -> Dict[str, Any]:
        logger.info(f"Starting daily pipeline for target date: {target_date}")

        if self.is_trading_holiday(target_date):
            logger.info(f"Target date {target_date} is a configured Indian trading holiday. Exiting.")
            return {"status": "skipped", "reason": "trading_holiday"}

        lookback_days = self.app_config["pipeline"]["historical_lookback_days"]
        start_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        # 1. Fetch & Process Benchmark Index Data
        logger.info("Fetching index data...")
        indices_dfs = {}
        for idx in self.stocks_config.get("indices", []):
            if not idx.get("enabled", True):
                continue
            sym = idx["symbol"]
            df_raw = self.provider.get_historical_prices(sym, start_date, target_date)
            df_val, _ = self.validator.validate_ohlcv(df_raw, sym)
            if not df_val.empty:
                df_ind = self.tech_engine.calculate_indicators(df_val)
                self.storage.save_processed_prices(df_ind, sym, category="indices")
                indices_dfs[idx.get("name", sym)] = df_ind

        benchmark_df = indices_dfs.get("NIFTY 50", list(indices_dfs.values())[0] if indices_dfs else None)

        # 2. Fetch & Process Stock Data
        logger.info("Fetching stock data...")
        stocks_dfs = {}
        stock_quality_reports = []
        stock_analysis_list = []
        feature_frames = []

        for st in self.stocks_config.get("stocks", []):
            if not st.get("enabled", True):
                continue

            sym = st["symbol"]
            ticker = st.get("ticker", sym)
            sector = st.get("sector", "Market")

            # Fetch OHLCV & Fundamentals
            df_raw = self.provider.get_historical_prices(sym, start_date, target_date)
            df_val, q_report = self.validator.validate_ohlcv(df_raw, ticker)
            stock_quality_reports.append(q_report)

            if df_val.empty:
                continue

            self.storage.save_raw_data(df_raw, ticker, target_date)
            df_ind = self.tech_engine.calculate_indicators(df_val)
            self.storage.save_processed_prices(df_ind, ticker, category="prices")
            stocks_dfs[ticker] = df_ind

            # Fundamentals
            raw_fund = self.provider.get_fundamental_summary(sym)
            fund_res = self.fund_analyzer.analyze(raw_fund)

            # Feature Building
            feat_df = self.feature_builder.build_features(df_ind, ticker, sector)
            if not feat_df.empty:
                feature_frames.append(feat_df)

        # Combine Features
        if feature_frames:
            combined_features = pd.concat(feature_frames, ignore_index=True)
            self.storage.save_features(combined_features, target_date)

        # 3. Market Regime & Sector Analysis
        logger.info("Running Market Regime & Sector Analysis...")
        market_regime_info = self.regime_analyzer.analyze_regime(
            benchmark_df if benchmark_df is not None else pd.DataFrame(),
            stocks_dfs
        )

        sector_rankings = self.sector_analyzer.analyze_sectors(
            indices_dfs,
            benchmark_df if benchmark_df is not None else pd.DataFrame()
        )
        sector_lookup = {s["sector"]: s for s in sector_rankings}

        # 4. Stock Scoring & Pattern Matching
        logger.info("Running Scoring & Historical Pattern Analogue Engine...")
        for st in self.stocks_config.get("stocks", []):
            ticker = st.get("ticker", st["symbol"])
            if ticker not in stocks_dfs:
                continue

            df_st = stocks_dfs[ticker]
            latest_events = self.tech_engine.extract_latest_events(df_st)
            latest_ind = df_st.iloc[-1].to_dict()
            latest_ind.update(latest_events)

            sec_info = sector_lookup.get(st.get("sector"))
            fund_info = self.fund_analyzer.analyze({})

            score_res = self.scorer.compute_score(latest_ind, market_regime_info, sec_info, fund_info)
            analogue_res = self.pattern_matcher.find_analogues_and_forward_returns(df_st)

            stock_analysis_list.append({
                "symbol": ticker,
                "name": st.get("name", ticker),
                "sector": st.get("sector", "Market"),
                "technical_score": score_res["composite_score"],
                "score_label": score_res["label"],
                "score_components": score_res["components"],
                "rsi_14": latest_events.get("rsi_14", 50.0),
                "volatility_regime": latest_events.get("volatility_regime", "Normal"),
                "signals": latest_events,
                "historical_analogue_matches": analogue_res.get("observations_count", 0),
                "forward_probabilities": analogue_res.get("forward_probabilities", {})
            })

        # Quality Aggregation
        total_processed = sum(q["records_processed"] for q in stock_quality_reports)
        total_valid = sum(q["records_valid"] for q in stock_quality_reports)
        all_warnings = [w for q in stock_quality_reports for w in q.get("warnings", [])]
        all_errors = [e for q in stock_quality_reports for e in q.get("errors", [])]

        overall_quality = {
            "date": target_date,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "warnings": all_warnings,
            "errors": all_errors
        }
        self.storage.save_quality_report(overall_quality, target_date)

        # 5. Generate Outputs & Reports
        full_analysis_data = {
            "date": target_date,
            "market": market_regime_info,
            "sectors": sector_rankings,
            "stocks": stock_analysis_list,
            "data_quality": overall_quality
        }

        json_path = self.storage.save_daily_analysis(full_analysis_data, target_date)
        markdown_content = self.report_generator.generate_markdown_report(full_analysis_data)
        md_path = self.storage.save_daily_report(markdown_content, target_date)

        logger.info(f"Generated Analysis JSON: {json_path}")
        logger.info(f"Generated Markdown Report: {md_path}")

        # 6. Commit to Git if enabled
        if commit_results:
            self._git_commit_artifacts(target_date)

        return {
            "status": "success",
            "date": target_date,
            "json_path": str(json_path),
            "report_path": str(md_path)
        }

    def _git_commit_artifacts(self, date_str: str):
        try:
            logger.info("Executing Git automated commit for daily outputs...")
            subprocess.run(["git", "add", "data/", "reports/"], check=True)
            msg = f"data: daily Indian market analysis {date_str}"
            subprocess.run(["git", "commit", "-m", msg], check=False)
        except Exception as e:
            logger.error(f"Git commit failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Pipeline")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Target date YYYY-MM-DD")
    parser.add_argument("--commit", action="store_true", help="Commit results to git repository")
    args = parser.parse_args()

    pipeline = DailyMarketPipeline()
    result = pipeline.run(target_date=args.date, commit_results=args.commit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
