import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.manager import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamentals import FundamentalAnalyzer
from src.scoring.composite_score import CompositeScorer
from src.patterns.historical_analogues import HistoricalPatternAnalyzer
from src.features.feature_engineering import FeatureEngineer
from src.modeling.prediction import DirectionalPredictor
from src.reporting.report_generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DailyPipeline")


class DailyMarketPipeline:
    """Orchestrates end-to-end Indian stock market analysis pipeline execution."""

    def __init__(self, config_dir: str = "config", base_data_dir: str = "data"):
        self.config_dir = config_dir
        self.stocks_config = self._load_json(os.path.join(config_dir, "stocks.json"))
        self.app_config = self._load_json(os.path.join(config_dir, "config.json"))
        self.holidays = self._load_json(os.path.join(config_dir, "holidays.json"))

        self.provider = YFinanceProvider()
        self.validator = DataValidator()
        self.storage = StorageManager(base_dir=base_data_dir)

    def _load_json(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def is_trading_holiday(self, date_str: str) -> bool:
        year = date_str.split("-")[0]
        year_holidays = self.holidays.get(year, [])
        return date_str in year_holidays

    def run(self, date_str: Optional[str] = None):
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Starting daily market analysis pipeline for date: {date_str}")

        if self.is_trading_holiday(date_str):
            logger.info(f"Date {date_str} is a scheduled NSE market holiday. Pipeline execution skipped.")
            return

        lookback_years = self.app_config.get("historical_lookback_years", 5)
        start_date = (pd.to_datetime(date_str) - pd.DateOffset(years=lookback_years)).strftime("%Y-%m-%d")
        end_date = (pd.to_datetime(date_str) + pd.DateOffset(days=1)).strftime("%Y-%m-%d")

        stock_validations = {}
        processed_stock_dfs = {}
        processed_index_dfs = {}
        stock_scores_list = []
        stock_sector_map = {}

        # 1. Ingest Indices Data
        logger.info("Ingesting Index Data...")
        indices = [idx for idx in self.stocks_config.get("indices", []) if idx.get("enabled", True)]
        nifty_df = pd.DataFrame()
        banknifty_df = pd.DataFrame()

        for idx_info in indices:
            sym = idx_info["symbol"]
            ticker = idx_info["ticker"]
            df_idx = self.provider.get_historical_prices(sym, ticker, start_date, end_date)
            if not df_idx.empty:
                df_idx = TechnicalIndicators.calculate_indicators(df_idx)
                self.storage.save_processed_prices(df_idx, sym, is_index=True)
                processed_index_dfs[sym] = df_idx
                if sym == "NIFTY 50":
                    nifty_df = df_idx
                elif sym == "NIFTY BANK":
                    banknifty_df = df_idx

        # 2. Ingest Equities Data
        logger.info("Ingesting Stock Data...")
        stocks = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]

        all_daily_features = []

        for s_info in stocks:
            sym = s_info["symbol"]
            ticker = s_info["ticker"]
            sector = s_info.get("sector", "Other")
            stock_sector_map[sym] = sector

            df = self.provider.get_historical_prices(sym, ticker, start_date, end_date)
            if df.empty:
                logger.warning(f"Skipping {sym} due to empty price data.")
                continue

            # Save raw price slice
            self.storage.save_raw_price_data(df, sym, date_str)

            # Validate Data
            val_res = self.validator.validate_ohlc(df)
            stock_validations[sym] = val_res

            # Calculate Technical Indicators
            df = TechnicalIndicators.calculate_indicators(df)
            self.storage.save_processed_prices(df, sym, is_index=False)
            processed_stock_dfs[sym] = df

            # Feature Engineering for ML dataset
            sec_df = processed_index_dfs.get(sector, pd.DataFrame())
            feat_df = FeatureEngineer.build_features(df, nifty_df, sec_df, include_targets=True)
            if not feat_df.empty:
                latest_feat = feat_df.iloc[[-1]].copy()
                all_daily_features.append(latest_feat)

        # Combine & Save Daily ML Feature Dataset
        if all_daily_features:
            daily_features_df = pd.concat(all_daily_features, ignore_index=True)
            self.storage.save_daily_features(daily_features_df, date_str)

        # 3. Market Regime Analysis
        logger.info("Calculating Market Regime...")
        market_regime = MarketRegimeAnalyzer.analyze_regime(nifty_df, banknifty_df, processed_stock_dfs)

        # 4. Sector Analysis
        logger.info("Performing Sector Analysis...")
        sector_analysis = SectorAnalyzer.analyze_sectors(
            processed_index_dfs, nifty_df, processed_stock_dfs, stock_sector_map
        )

        # 5. Stock Analysis, Scoring, Historical Analogues & Research Prediction
        logger.info("Computing Stock Scores, Patterns, and Research Signals...")
        for s_info in stocks:
            sym = s_info["symbol"]
            ticker = s_info["ticker"]
            if sym not in processed_stock_dfs:
                continue

            df = processed_stock_dfs[sym]
            latest_signals = TechnicalIndicators.get_latest_signals(df)

            # Fundamentals
            fund_raw = self.provider.get_fundamental_data(sym, ticker)
            fund_analysis = FundamentalAnalyzer.analyze_fundamentals(fund_raw)

            # Sector info
            sec_name = stock_sector_map.get(sym)
            sec_info = next((sec for sec in sector_analysis.get("sectors", []) if sec["sector"] == sec_name), None)

            # Composite Score
            score_res = CompositeScorer.compute_stock_score(
                latest_signals, market_regime, sec_info, fund_analysis
            )

            # Historical Analogues
            pattern_res = HistoricalPatternAnalyzer.find_analogues(df)

            # Directional Research Model Prediction
            pred_res = DirectionalPredictor.train_and_evaluate(df, horizon_days=5)

            stock_scores_list.append({
                "symbol": sym,
                "technical_score": score_res["composite_score"],
                "composite_label": score_res["label"],
                "component_scores": score_res["component_scores"],
                "fundamental_score": fund_analysis["fundamental_score"],
                "signals": latest_signals,
                "historical_analogues": pattern_res,
                "forward_probabilities": pred_res
            })

        # 6. Quality Report
        quality_report = self.validator.create_quality_report(date_str, stock_validations)
        self.storage.save_quality_report(date_str, quality_report)

        # 7. Machine-Readable Daily JSON Analysis Output
        json_output = ReportGenerator.build_daily_json_schema(
            date_str, market_regime, sector_analysis, stock_scores_list
        )
        self.storage.save_daily_analysis(date_str, json_output)

        # 8. Human-Readable Daily Markdown Summary Report
        md_report = ReportGenerator.generate_markdown_report(
            date_str, market_regime, sector_analysis, stock_scores_list, quality_report
        )
        self.storage.save_daily_report(date_str, md_report)

        logger.info(f"Daily pipeline completed successfully for date {date_str}.")


def main():
    parser = argparse.ArgumentParser(description="Run Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format (default: today)")
    args = parser.parse_args()

    pipeline = DailyMarketPipeline()
    pipeline.run(date_str=args.date)


if __name__ == "__main__":
    main()
