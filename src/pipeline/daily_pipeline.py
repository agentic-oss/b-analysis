"""Daily Market Analysis Pipeline Orchestrator."""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
import pandas as pd

from src.ingestion.yfinance_provider import YahooFinanceProvider
from src.ingestion.mock_provider import MockMarketDataProvider
from src.validation.validator import DataValidator
from src.storage.storage import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.fundamentals.fundamentals import FundamentalAnalyzer
from src.scoring.scorer import StockScorer
from src.features.engineer import FeatureEngineer
from src.patterns.analogues import HistoricalAnalogueAnalyzer
from src.modeling.predictor import PredictionModule
from src.reporting.generator import ReportGenerator
from src.utils.git_utils import GitIntegration

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

class DailyPipeline:
    """Orchestrates end-to-end data ingestion, validation, technical analysis, scoring, pattern matching, prediction, reporting, and storage."""

    def __init__(self, stocks_config_path: str = "config/stocks.json", config_path: str = "config/config.json", holidays_config_path: str = "config/holidays.json"):
        with open(stocks_config_path, "r") as f:
            self.stocks_config = json.load(f)

        with open(config_path, "r") as f:
            self.pipeline_config = json.load(f)

        with open(holidays_config_path, "r") as f:
            self.holidays_config = json.load(f)

        provider_type = self.pipeline_config.get("pipeline", {}).get("data_provider", "yfinance")
        fallback_mock = self.pipeline_config.get("pipeline", {}).get("fallback_to_mock_on_error", True)

        if provider_type == "mock":
            self.provider = MockMarketDataProvider()
        else:
            self.provider = YahooFinanceProvider(fallback_to_mock=fallback_mock)

        self.validator = DataValidator()
        self.storage = StorageManager()
        self.market_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.scorer = StockScorer(weights=self.pipeline_config.get("scoring", {}).get("weights"))
        self.analogue_analyzer = HistoricalAnalogueAnalyzer()
        self.predictor = PredictionModule()

    def is_trading_day(self, date_str: str) -> bool:
        """Checks if date is a weekend or listed Indian market holiday."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5: # Saturday or Sunday
            return False
        if date_str in self.holidays_config.get("holidays", []):
            return False
        return True

    def run(self, date_str: str, force_run: bool = False, auto_commit: bool = False) -> bool:
        """Executes full daily pipeline for target date_str (YYYY-MM-DD)."""
        logger.info(f"Starting Daily Pipeline execution for target date: {date_str}")

        if not force_run and not self.is_trading_day(date_str):
            logger.info(f"Date {date_str} is a holiday or weekend. Skipping pipeline execution.")
            return True

        # Calculate historical start date
        lookback_years = self.pipeline_config.get("pipeline", {}).get("historical_lookback_years", 3)
        target_dt = datetime.strptime(date_str, "%Y-%m-%d")
        start_dt = target_dt - timedelta(days=lookback_years * 365)
        start_date_str = start_dt.strftime("%Y-%m-%d")

        # 1. Ingest Stock Data
        tracked_stocks = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]
        stock_dfs = []
        raw_today_rows = []

        for stock in tracked_stocks:
            sym = stock["symbol"]
            df_hist = self.provider.get_historical_prices(sym, start_date_str, date_str)
            if not df_hist.empty:
                df_hist['raw_symbol'] = stock.get("raw_symbol", sym)
                df_hist['sector'] = stock.get("sector", "Unknown")

                # Calculate indicators
                df_ind = TechnicalIndicators.calculate_indicators(df_hist)
                df_feat = FeatureEngineer.build_features_and_targets(df_ind)
                stock_dfs.append((stock, df_feat))

                # Extract target date row for validation and snapshot
                today_row = df_feat[df_feat['date'] == date_str]
                if not today_row.empty:
                    raw_today_rows.append(today_row.iloc[0].to_dict())

        # Combine today raw snapshot for validation
        today_raw_df = pd.DataFrame(raw_today_rows) if raw_today_rows else pd.DataFrame()

        # 2. Ingest Index Data
        indices_dfs = {}
        nifty_df = pd.DataFrame()
        for idx in self.stocks_config.get("indices", []):
            sym = idx["symbol"]
            sec_name = idx.get("sector", idx.get("name"))
            df_idx = self.provider.get_historical_prices(sym, start_date_str, date_str)
            if not df_idx.empty:
                df_idx_ind = TechnicalIndicators.calculate_indicators(df_idx)
                indices_dfs[sec_name] = df_idx_ind
                if idx.get("name") == "NIFTY 50" or sym == "^NSEI":
                    nifty_df = df_idx_ind

        # 3. Validate Today's Ingested Data
        quality_report = self.validator.validate_df(today_raw_df, date_str)
        self.storage.save_quality_report(quality_report, date_str)
        if not today_raw_df.empty:
            self.storage.save_raw_prices(today_raw_df, date_str)

        # 4. Market Regime & Sector Analysis
        latest_stock_rows = [df[1].iloc[-1] for df in stock_dfs if not df[1].empty]
        latest_stocks_df = pd.DataFrame(latest_stock_rows) if latest_stock_rows else pd.DataFrame()

        market_regime = self.market_analyzer.analyze_regime(latest_stocks_df, nifty_df)
        sectors_analysis = self.sector_analyzer.analyze_sectors(indices_dfs, nifty_df)
        sector_lookup = {s['sector']: s for s in sectors_analysis}

        # 5. Stock Level Deep Analysis
        analyzed_stocks_json = []

        for stock_cfg, df_feat in stock_dfs:
            if df_feat.empty:
                continue

            latest_row = df_feat.iloc[-1]
            sym = stock_cfg["symbol"]
            sec = stock_cfg.get("sector", "Unknown")
            sec_info = sector_lookup.get(sec)

            # Fundamentals
            fund_res = self.fundamental_analyzer.analyze_fundamentals(sym)

            # Composite Score
            score_res = self.scorer.score_stock(latest_row, market_regime, sec_info, fund_res["score"])

            # Historical Analogues
            analogues_res = self.analogue_analyzer.find_analogues(df_feat)

            # Forward Probabilities / Prediction Signals
            pred_res = self.predictor.train_and_predict(df_feat)

            analyzed_stocks_json.append({
                "symbol": stock_cfg.get("raw_symbol", sym),
                "ticker": sym,
                "exchange": stock_cfg.get("exchange", "NSE"),
                "sector": sec,
                "close": float(latest_row.get("close", 0)),
                "daily_return_pct": round(float(latest_row.get("daily_return", 0)) * 100, 2),
                "composite_score": score_res["composite_score"],
                "score_label": score_res["label"],
                "components": score_res["components"],
                "breakout_20d": bool(latest_row.get("breakout_20d", False)),
                "breakdown_20d": bool(latest_row.get("breakdown_20d", False)),
                "relative_volume": round(float(latest_row.get("relative_volume", 1.0)), 2),
                "historical_analogues": analogues_res,
                "forward_probabilities": pred_res,
                "fundamentals": fund_res
            })

            # Save historical processed data
            self.storage.save_processed_prices(df_feat)

        # 6. Generate Reports & JSON
        daily_json = ReportGenerator.generate_json_output(date_str, market_regime, sectors_analysis, analyzed_stocks_json, quality_report)
        daily_md = ReportGenerator.generate_markdown_report(date_str, market_regime, sectors_analysis, analyzed_stocks_json, quality_report)

        self.storage.save_daily_analysis_json(daily_json, date_str)
        self.storage.save_daily_report_markdown(daily_md, date_str)

        logger.info(f"Daily pipeline completed successfully for {date_str}")

        # 7. Git Integration
        if auto_commit:
            GitIntegration.commit_daily_results(date_str)
            GitIntegration.push_changes()

        return True


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Target date YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Force execution even on holidays/weekends")
    parser.add_argument("--auto-commit", action="store_true", help="Automatically commit generated data and reports to git")
    args = parser.parse_args()

    pipeline = DailyPipeline()
    pipeline.run(date_str=args.date, force_run=args.force, auto_commit=args.auto_commit)

if __name__ == "__main__":
    main()
