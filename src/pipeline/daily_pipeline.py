"""Daily Market Analysis Pipeline Orchestrator."""

import argparse
import datetime
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage import DataStorage
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeDetector
from src.sectors.sector import SectorAnalyzer
from src.fundamentals.fundamentals import FundamentalAnalyzer
from src.scoring.scorer import StockScorer
from src.patterns.analogue import HistoricalAnalogueFinder
from src.features.engineer import FeatureEngineer
from src.modeling.predictor import ProbabilisticPredictor
from src.reporting.generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DailyPipeline")


class DailyPipeline:
    """Orchestrates end-to-end stock market analysis pipeline."""

    def __init__(
        self,
        config_path: str = "config/config.json",
        stocks_path: str = "config/stocks.json",
        holidays_path: str = "config/holidays.json",
        data_dir: str = "data"
    ):
        self.config = self._load_json(config_path)
        self.stocks = self._load_json(stocks_path)
        self.holidays = self._load_json(holidays_path)
        self.storage = DataStorage(base_dir=data_dir)
        self.provider = YFinanceProvider(
            retries=self.config.get("provider", {}).get("retries", 3),
            retry_delay=self.config.get("provider", {}).get("retry_delay_seconds", 2.0),
            timeout=self.config.get("provider", {}).get("timeout_seconds", 30)
        )
        self.validator = DataValidator(holidays=self.holidays.get("2026", []))
        self.predictor = ProbabilisticPredictor()

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        logger.warning(f"Config file not found at {path}, returning empty dict.")
        return {}

    def is_trading_day(self, date_str: str) -> bool:
        """Check if date is a trading day (not weekend or listed holiday)."""
        dt = pd.to_datetime(date_str)
        if dt.weekday() >= 5:  # Saturday/Sunday
            return False
        year_str = str(dt.year)
        holiday_list = self.holidays.get(year_str, [])
        if date_str in holiday_list:
            return False
        return True

    def run(self, date_str: str, sample_limit: Optional[int] = None) -> bool:
        """Execute complete daily pipeline for given trading date."""
        logger.info(f"=== Starting Daily Indian Stock Market Analysis for {date_str} ===")

        if not self.is_trading_day(date_str):
            logger.info(f"Date {date_str} is a holiday or weekend. Pipeline execution skipped.")
            return True

        # Calculate historical start date
        lookback_years = self.config.get("pipeline", {}).get("lookback_years", 3)
        target_dt = pd.to_datetime(date_str)
        start_dt = target_dt - pd.DateOffset(years=lookback_years)
        start_date_str = start_dt.strftime("%Y-%m-%d")
        # Extend end_date to include full trading day
        end_date_str = (target_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        # Select indices and stock universe
        indices_list = [i for i in self.stocks.get("indices", []) if i.get("enabled", True)]
        stocks_list = [s for s in self.stocks.get("stocks", []) if s.get("enabled", True)]

        if sample_limit:
            stocks_list = stocks_list[:sample_limit]
            logger.info(f"Sample mode active: limited stock universe to {sample_limit} symbols.")

        validation_summaries = []
        stock_dfs = {}
        index_dfs = {}
        sector_dfs = {}
        stock_features_list = []

        # 1. Fetch & Validate Index Data
        for idx in indices_list:
            sym = idx["symbol"]
            logger.info(f"Fetching index data for {sym}...")
            try:
                raw_df = self.provider.get_index_data(sym, start_date_str, end_date_str)
                clean_df, summary = self.validator.validate_df(raw_df, ticker=sym)
                validation_summaries.append(summary)

                if not clean_df.empty:
                    calc_df = TechnicalIndicators.calculate_all(clean_df)
                    self.storage.update_processed_prices(calc_df, sym, is_index=True)
                    index_dfs[sym] = calc_df
                    if idx.get("category") == "Sector":
                        sector_name = idx.get("name", sym)
                        sector_dfs[sector_name] = calc_df
            except Exception as e:
                logger.error(f"Error processing index {sym}: {e}")

        # Benchmark NIFTY 50
        nifty_df = index_dfs.get("^NSEI", pd.DataFrame())

        # 2. Fetch & Validate Stock Data
        for st in stocks_list:
            sym = st["symbol"]
            exchange = st.get("exchange", "NSE")
            logger.info(f"Fetching stock data for {sym} ({exchange})...")
            try:
                raw_df = self.provider.get_historical_prices(sym, start_date_str, end_date_str, exchange=exchange)
                if not raw_df.empty:
                    self.storage.save_raw_prices(raw_df, sym, date_str)

                clean_df, summary = self.validator.validate_df(raw_df, ticker=sym)
                validation_summaries.append(summary)

                if not clean_df.empty:
                    calc_df = TechnicalIndicators.calculate_all(clean_df)
                    self.storage.update_processed_prices(calc_df, sym, is_index=False)
                    stock_dfs[sym] = calc_df
            except Exception as e:
                logger.error(f"Error processing stock {sym}: {e}")

        # Generate Data Quality Report
        quality_report_path = self.validator.generate_quality_report(
            date_str, validation_summaries, output_dir=os.path.join(self.storage.base_dir, "quality")
        )
        with open(quality_report_path, "r", encoding="utf-8") as f:
            quality_summary = json.load(f)

        # 3. Market Regime Analysis
        bank_nifty_df = index_dfs.get("^NSEBANK", pd.DataFrame())
        market_regime = MarketRegimeDetector.analyze_regime(nifty_df, bank_nifty_df, stock_dfs)

        # 4. Sector Analysis
        sector_analysis = SectorAnalyzer.analyze_sectors(sector_dfs, nifty_df)
        sector_map = {s["sector"]: s for s in sector_analysis}

        # 5. Stock Level Analysis, Scoring, Patterns & Features
        stocks_analysis_results = []

        for st in stocks_list:
            sym = st["symbol"]
            exchange = st.get("exchange", "NSE")
            s_sector = st.get("sector", "Other")

            if sym not in stock_dfs:
                continue

            s_df = stock_dfs[sym]
            tech_summary = TechnicalIndicators.get_latest_summary(s_df)

            # Fundamentals
            fund_data = FundamentalAnalyzer.fetch_fundamentals(sym, exchange=exchange)

            # Sector info
            sec_info = sector_map.get(s_sector, {})

            # Composite Score
            score_data = StockScorer.calculate_stock_score(
                s_df,
                nifty_df=nifty_df,
                market_regime_data=market_regime,
                sector_data=sec_info,
                fundamental_data=fund_data,
                weights=self.config.get("scoring_weights")
            )

            # Historical Analogues
            analogue_res = HistoricalAnalogueFinder.find_analogues(s_df)

            # Probabilistic Forward Signals
            forward_signals = self.predictor.predict_forward_signals(tech_summary, analogue_res)

            # ML Features Point-in-time
            sec_df = sector_dfs.get(s_sector, pd.DataFrame())
            feat_df = FeatureEngineer.build_features_for_stock(s_df, nifty_df=nifty_df, sector_df=sec_df, scoring_data=score_data)
            if not feat_df.empty:
                stock_features_list.append(feat_df)

            stocks_analysis_results.append({
                "symbol": sym,
                "exchange": exchange,
                "sector": s_sector,
                "composite_score": score_data["composite_score"],
                "label": score_data["label"],
                "components": score_data["components"],
                "technical_summary": tech_summary,
                "fundamentals": fund_data,
                "historical_analogues": analogue_res,
                "forward_probabilities": forward_signals
            })

        # Save Feature Dataset
        if stock_features_list:
            combined_features = pd.concat(stock_features_list, ignore_index=True)
            self.storage.save_features(combined_features, date_str)

        # 6. Generate Machine-Readable JSON & Human-Readable Markdown
        json_output = ReportGenerator.generate_json_output(
            date_str, market_regime, sector_analysis, stocks_analysis_results, quality_summary
        )
        self.storage.save_analysis_json(json_output, date_str)

        md_output = ReportGenerator.generate_markdown_report(
            date_str, market_regime, sector_analysis, stocks_analysis_results, quality_summary
        )
        self.storage.save_report_md(md_output, date_str)

        logger.info(f"=== Daily Pipeline Successfully Completed for {date_str} ===")
        return True


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Data & Deep Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Trading date YYYY-MM-DD (defaults to today)", default=None)
    parser.add_argument("--sample", action="store_true", help="Run in sample mode on limited stock universe")
    args = parser.parse_args()

    date_str = args.date or datetime.date.today().strftime("%Y-%m-%d")
    sample_limit = 5 if args.sample else None

    pipeline = DailyPipeline()
    success = pipeline.run(date_str, sample_limit=sample_limit)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
