"""
Master daily market analysis pipeline runner.
Orchestrates ingestion, validation, storage, feature engineering, regime analysis, sector analysis,
stock scoring, historical analogue pattern analysis, prediction research, and daily reporting.
"""
import argparse
import datetime
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.manager import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.indicators.patterns import PatternDetector
from src.market.regime import MarketRegimeDetector
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.patterns.analogue import HistoricalAnalogueEngine
from src.scoring.evaluator import StockScorer
from src.features.builder import FeatureEngine
from src.modeling.baselines import BaselinePredictor
from src.reporting.generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("DailyPipeline")


class DailyPipeline:
    """Master pipeline orchestrator."""

    def __init__(self, config_dir: str = "config", base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.config_dir = Path(config_dir)

        # Load configs
        with open(self.config_dir / "stocks.json", "r", encoding="utf-8") as f:
            self.stocks_config = json.load(f)

        with open(self.config_dir / "config.json", "r", encoding="utf-8") as f:
            self.pipeline_config = json.load(f)

        self.provider = YFinanceProvider(
            max_retries=self.pipeline_config["data_provider"]["max_retries"],
            timeout=self.pipeline_config["data_provider"]["timeout"],
        )
        self.validator = DataValidator()
        self.storage = StorageManager(base_dir=base_dir)

    def run(self, date_str: str, sample_mode: bool = False) -> Dict[str, Any]:
        logger.info(f"--- Starting Daily Pipeline Execution for Date: {date_str} (Sample Mode: {sample_mode}) ---")

        # Determine start date for historical lookback
        target_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        start_dt = target_dt - datetime.timedelta(days=365 * 3)
        start_date_str = start_dt.strftime("%Y-%m-%d")
        fetch_end_date = (target_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        all_warnings = []
        all_errors = []

        # 1. Ingest Indices
        indices = [i for i in self.stocks_config.get("indices", []) if i.get("enabled", True)]
        if sample_mode:
            indices = indices[:2]

        index_dfs = {}
        for idx_info in indices:
            symbol = idx_info["symbol"]
            yahoo_sym = idx_info["yahoo_symbol"]
            logger.info(f"Fetching index data: {symbol} ({yahoo_sym})")
            df = self.provider.get_index_data(yahoo_sym, start_date_str, fetch_end_date)
            clean_df, warn, err = self.validator.validate_dataframe(df, symbol)
            all_warnings.extend(warn)
            all_errors.extend(err)

            if not clean_df.empty:
                enriched_df = TechnicalIndicators.calculate_all(clean_df)
                index_dfs[symbol] = enriched_df
                self.storage.save_raw_data(df, yahoo_sym, date_str)
                self.storage.save_processed_prices(enriched_df, yahoo_sym, is_index=True)

        nifty_df = index_dfs.get("NIFTY 50", pd.DataFrame())

        # Sector Indices mapping
        sector_indices = {k: v for k, v in index_dfs.items() if k != "NIFTY 50" and k != "NIFTY NEXT 50"}

        # 2. Ingest Equity Stocks Universe
        stocks = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]
        if sample_mode:
            stocks = stocks[:5]

        stock_dfs = {}
        processed_stocks_data = []
        technical_events = []
        all_feature_rows = []

        total_symbols = len(stocks)
        valid_symbols = 0

        for st_info in stocks:
            symbol = st_info["symbol"]
            yahoo_sym = st_info["yahoo_symbol"]
            sector = st_info.get("sector", "General")

            logger.info(f"Fetching stock data: {symbol} ({yahoo_sym})")
            df = self.provider.get_historical_prices(yahoo_sym, start_date_str, fetch_end_date)
            clean_df, warn, err = self.validator.validate_dataframe(df, symbol)
            all_warnings.extend(warn)
            all_errors.extend(err)

            if clean_df.empty:
                logger.warning(f"Skipping {symbol} due to empty data after validation.")
                continue

            valid_symbols += 1
            enriched_df = TechnicalIndicators.calculate_all(clean_df)
            enriched_df["ticker"] = symbol
            enriched_df["sector"] = sector
            stock_dfs[symbol] = enriched_df

            # Save raw & processed
            self.storage.save_raw_data(df, yahoo_sym, date_str)
            self.storage.save_processed_prices(enriched_df, yahoo_sym, is_index=False)

            # Detect Events
            events = PatternDetector.detect_events(enriched_df)
            technical_events.extend(events)

            # Fundamentals
            fund_data = FundamentalAnalyzer.fetch_and_evaluate(yahoo_sym)

            # Feature Engineering
            sector_df = sector_indices.get(f"NIFTY {sector.upper()}", pd.DataFrame())
            feature_df = FeatureEngine.build_feature_set(enriched_df, nifty_df, sector_df)
            if not feature_df.empty:
                latest_feature = feature_df.iloc[-1:].copy()
                all_feature_rows.append(latest_feature)

            # Historical Analogues
            analogue_results = HistoricalAnalogueEngine.find_analogues(enriched_df)

            # Modeling baseline
            feature_cols = [
                c
                for c in ["rsi_14", "volatility_20d", "dist_sma_50_pct", "relative_volume"]
                if c in feature_df.columns
            ]
            predictor = BaselinePredictor()
            ml_eval = predictor.evaluate_walk_forward(feature_df, feature_cols)

            # Stock Scoring (preliminary before market regime aggregation)
            processed_stocks_data.append({
                "symbol": symbol,
                "sector": sector,
                "df": enriched_df,
                "fundamentals": fund_data,
                "analogues": analogue_results,
                "ml_eval": ml_eval,
            })

        # 3. Market Regime Analysis
        market_regime = MarketRegimeDetector.analyze_regime(nifty_df, stock_dfs)

        # 4. Sector Analysis
        sector_analysis = SectorAnalyzer.analyze_sectors(sector_indices, nifty_df)
        sector_lookup = {s["sector"]: s for s in sector_analysis}

        # 5. Finalize Stock Scores & Structured JSON Output
        final_stock_outputs = []
        for item in processed_stocks_data:
            sym = item["symbol"]
            sec = item["sector"]
            e_df = item["df"]
            f_data = item["fundamentals"]
            a_data = item["analogues"]
            ml_eval = item["ml_eval"]

            sec_data = sector_lookup.get(f"NIFTY {sec.upper()}", None)
            scoring_res = StockScorer.score_stock(
                stock_df=e_df,
                market_regime_data=market_regime,
                sector_data=sec_data,
                fundamental_data=f_data,
                config_weights=self.pipeline_config["scoring"]["weights"],
            )

            latest_row = e_df.iloc[-1]
            final_stock_outputs.append({
                "symbol": sym,
                "sector": sec,
                "price_close": round(float(latest_row["Close"]), 2),
                "daily_return_pct": round(float(latest_row.get("return_1d", 0.0) * 100), 2),
                "technical_score": scoring_res["composite_score"],
                "score_label": scoring_res["label"],
                "score_components": scoring_res["components"],
                "fundamental_score": f_data.get("score"),
                "market_regime": market_regime["regime"],
                "historical_analogues": a_data,
                "predictive_signals": ml_eval,
            })

        # 6. Save Data Quality Report
        quality_report = self.validator.generate_quality_report(
            date_str, total_symbols, valid_symbols, all_warnings, all_errors
        )
        self.storage.save_quality_report(quality_report, date_str)

        # 7. Consolidate and Save Daily Features
        if all_feature_rows:
            combined_features = pd.concat(all_feature_rows, ignore_index=True)
            self.storage.save_features(combined_features, date_str)

        # 8. Create & Save Structured Daily Analysis JSON
        daily_analysis = {
            "date": date_str,
            "market": market_regime,
            "sectors": sector_analysis,
            "stocks": final_stock_outputs,
            "technical_events": technical_events,
            "quality": quality_report,
        }
        self.storage.save_daily_analysis(daily_analysis, date_str)

        # 9. Generate & Save Markdown Report
        md_content = ReportGenerator.generate_markdown(daily_analysis)
        self.storage.save_daily_report_md(md_content, date_str)

        logger.info(f"--- Completed Daily Pipeline Execution for Date: {date_str} Successfully ---")
        return daily_analysis


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.date.today().strftime("%Y-%m-%d"),
        help="Trading date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run in sample mode on a small subset of universe for quick testing",
    )
    args = parser.parse_args()

    pipeline = DailyPipeline()
    pipeline.run(date_str=args.date, sample_mode=args.sample)


if __name__ == "__main__":
    main()
