"""
Master Daily Pipeline Execution Script.
Runs end-to-end stock market ingestion, validation, indicators, regime analysis, sector scoring,
historical pattern matching, feature engineering, ML baseline evaluation, reporting, and Git integration.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.fundamentals.fundamentals import FundamentalAnalyzer
from src.scoring.scorer import StockScorer
from src.patterns.analogue_finder import PatternAnalogueFinder
from src.features.builder import FeatureBuilder
from src.modeling.models import PredictiveModelEngine
from src.backtesting.backtester import Backtester
from src.reporting.report_generator import ReportGenerator

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DailyPipeline")


class DailyPipeline:
    """End-to-end daily Indian stock market analysis pipeline."""

    def __init__(
        self,
        config_path: str = "config/config.json",
        stocks_path: str = "config/stocks.json",
        holidays_path: str = "config/holidays.json",
        base_dir: str = ".",
    ):
        self.base_dir = Path(base_dir)

        # Load configs
        with open(self.base_dir / config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        with open(self.base_dir / stocks_path, "r", encoding="utf-8") as f:
            self.stocks_config = json.load(f)
        with open(self.base_dir / holidays_path, "r", encoding="utf-8") as f:
            self.holidays = json.load(f).get("holidays", [])

        self.provider = YFinanceProvider(
            timeout=self.config["provider"]["timeout"],
            max_retries=self.config["provider"]["max_retries"],
            backoff_factor=self.config["provider"]["backoff_factor"],
        )
        self.validator = DataValidator()
        self.storage = StorageManager(base_dir=self.base_dir)
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.scorer = StockScorer(weights=self.config["scoring"]["weights"])
        self.analogue_finder = PatternAnalogueFinder()
        self.feature_builder = FeatureBuilder()
        self.model_engine = PredictiveModelEngine()

    def is_holiday(self, date_str: str) -> bool:
        """Checks if date_str is a listed market holiday."""
        return date_str in self.holidays

    def run(self, target_date: str) -> bool:
        """Executes full pipeline for target_date (YYYY-MM-DD)."""
        logger.info(f"Starting daily pipeline execution for date: {target_date}")

        if self.is_holiday(target_date):
            logger.info(f"Date {target_date} is a market holiday. Skipping execution.")
            return True

        lookback_days = self.config["lookback"]["historical_days"]
        end_dt = pd.to_datetime(target_date) + pd.Timedelta(days=1)
        start_dt = end_dt - pd.Timedelta(days=lookback_days)

        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")

        # 1. Ingestion & Validation for Indices
        logger.info("Ingesting Index Data...")
        indices_list = [idx for idx in self.stocks_config["indices"] if idx.get("enabled", True)]
        index_dfs = {}
        index_validation_summaries = []

        for idx_meta in indices_list:
            sym = idx_meta["symbol"]
            df_raw = self.provider.get_index_data(sym, start_str, end_str)
            if not df_raw.empty:
                self.storage.save_raw_data(df_raw, sym, target_date)
                val_df, val_sum = self.validator.validate_df(df_raw, ticker=sym)
                index_validation_summaries.append(val_sum)

                if not val_df.empty:
                    val_df = TechnicalIndicators.calculate_indicators(val_df)
                    index_dfs[sym] = val_df
                    self.storage.update_processed_dataset(val_df, dataset_type="indices", filename=sym.replace("^", ""))

        # 2. Ingestion & Validation for Equities
        logger.info("Ingesting Stock Data...")
        stocks_list = [s for s in self.stocks_config["stocks"] if s.get("enabled", True)]
        stock_dfs = {}
        stock_validation_summaries = []

        for stock_meta in stocks_list:
            sym = stock_meta["symbol"]
            exch = stock_meta.get("exchange", "NSE")
            ticker_ovr = stock_meta.get("ticker_yf")

            df_raw = self.provider.get_historical_prices(sym, start_str, end_str, exchange=exch, ticker_override=ticker_ovr)
            if not df_raw.empty:
                self.storage.save_raw_data(df_raw, sym, target_date)
                val_df, val_sum = self.validator.validate_df(df_raw, ticker=sym)
                stock_validation_summaries.append(val_sum)

                if not val_df.empty:
                    val_df = TechnicalIndicators.calculate_indicators(val_df)
                    stock_dfs[sym] = val_df

        # Save cumulative processed prices
        if stock_dfs:
            combined_stock_prices = pd.concat(list(stock_dfs.values()), ignore_index=True)
            self.storage.update_processed_dataset(combined_stock_prices, dataset_type="prices", filename="historical_prices")

        # Consolidated Quality Report
        quality_report = self.validator.build_quality_report(
            target_date, index_validation_summaries + stock_validation_summaries
        )
        self.storage.save_quality_report(quality_report, target_date)

        # 3. Market Regime Analysis
        logger.info("Analyzing Market Regime...")
        market_info = self.regime_analyzer.analyze_regime(index_dfs, stock_dfs, target_date)

        # 4. Sector Analysis
        logger.info("Analyzing Sectors...")
        sector_indices = [idx for idx in indices_list if idx.get("category") == "sector"]
        sectors_info = self.sector_analyzer.analyze_sectors(sector_indices, index_dfs, target_date)
        sector_lookup = {s["sector_id"]: s for s in sectors_info}

        # 5. Stock Deep Analysis, Pattern Analogue Matching & Scoring
        logger.info("Analyzing Equities, Signals & Pattern Analogues...")
        analyzed_stocks = []
        all_features_list = []

        for stock_meta in stocks_list:
            sym = stock_meta["symbol"]
            s_df = stock_dfs.get(sym)
            if s_df is None or s_df.empty:
                continue

            s_sub = s_df[s_df["date"] <= target_date]
            if s_sub.empty:
                continue

            latest_row = s_sub.iloc[-1]
            signals = TechnicalIndicators.detect_signals(s_sub)

            # Fundamentals
            fund_info = self.fundamental_analyzer.get_fundamentals(sym)

            # Sector Info
            sec_id = stock_meta.get("sector")
            sec_info = sector_lookup.get(sec_id)

            # Scoring
            score_res = self.scorer.calculate_score(
                latest_row, market_info, sector_info=sec_info, fundamental_info=fund_info
            )

            # Historical Pattern Analogue Finder
            analogues_res = self.analogue_finder.find_analogues(s_sub)

            # Feature Engineering
            mkt_df = index_dfs.get("^NSEI", pd.DataFrame())
            sec_sym = sec_info.get("symbol") if sec_info else None
            sec_df = index_dfs.get(sec_sym, pd.DataFrame()) if sec_sym else None

            features_df = self.feature_builder.build_feature_dataset(
                s_sub, market_df=mkt_df, sector_df=sec_df, scoring_info=score_res, fundamental_info=fund_info
            )

            if not features_df.empty:
                all_features_list.append(features_df)

            # Forward Movements Inference
            signals_fwd = self.model_engine.predict_signals(features_df, analogues_res)

            analyzed_stocks.append({
                "symbol": sym,
                "exchange": stock_meta.get("exchange", "NSE"),
                "date": target_date,
                "close": float(latest_row["close"]),
                "daily_return": round(float(latest_row.get("daily_return", 0.0)) * 100, 2),
                "technical_score": score_res["composite_score"],
                "label": score_res["label"],
                "score_components": score_res["components"],
                "signals": signals,
                "fundamentals": fund_info,
                "historical_analogues": analogues_res,
                "forward_probabilities": signals_fwd,
            })

        # Save Engineered Daily Features
        if all_features_list:
            daily_features_df = pd.concat(all_features_list, ignore_index=True)
            self.storage.save_features(daily_features_df, target_date)

        # 6. Generate Reports
        logger.info("Generating Machine-Readable JSON and Human-Readable Markdown Reports...")
        json_output = ReportGenerator.generate_json_output(
            target_date, market_info, sectors_info, analyzed_stocks, quality_report
        )
        self.storage.save_json_output(json_output, f"data/analysis/daily/{target_date}.json")

        markdown_content = ReportGenerator.generate_markdown_report(
            target_date, market_info, sectors_info, analyzed_stocks, quality_report
        )
        self.storage.save_markdown_report(markdown_content, target_date)

        logger.info(f"Daily Pipeline completed successfully for date {target_date}.")
        return True


def commit_generated_results(date_str: str) -> None:
    """Helper to perform automated git commit of generated outputs."""
    try:
        cmd_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not cmd_status.stdout.strip():
            logger.info("No git changes detected to commit.")
            return

        subprocess.run(["git", "add", "data/", "reports/"], check=True)
        commit_msg = f"data: daily Indian market analysis {date_str}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        logger.info(f"Successfully committed generated results: '{commit_msg}'")
    except Exception as e:
        logger.warning(f"Git commit failed or no changes to commit: {e}")


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Pipeline")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Target date YYYY-MM-DD")
    parser.add_argument("--auto-commit", action="store_true", help="Automatically commit generated artifacts to git")
    args = parser.parse_args()

    pipeline = DailyPipeline()
    success = pipeline.run(args.date)

    if success and args.auto_commit:
        commit_generated_results(args.date)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
