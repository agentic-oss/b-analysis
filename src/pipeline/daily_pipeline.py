import os
import json
import logging
import argparse
from datetime import datetime
import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.store import DataStore
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamental_analysis import FundamentalAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.patterns.historical_analogues import HistoricalAnalogueAnalyzer
from src.features.feature_builder import FeatureBuilder
from src.modeling.predictor import MarketPredictor
from src.reporting.generator import DailyReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DailyPipeline")

class DailyMarketPipeline:
    """End-to-end orchestrator for daily stock market analysis."""

    def __init__(self, config_path: str = "config/config.json", stocks_path: str = "config/stocks.json", holidays_path: str = "config/holidays.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        with open(stocks_path) as f:
            self.stocks_config = json.load(f)
        with open(holidays_path) as f:
            self.holidays = json.load(f).get("holidays", [])

        self.provider = YFinanceProvider()
        self.validator = DataValidator()
        self.store = DataStore()

    def is_trading_holiday(self, date_str: str) -> bool:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5: # Saturday or Sunday
            return True
        return date_str in self.holidays

    def run(self, date_str: str = None) -> bool:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Starting daily pipeline execution for date: {date_str}")

        if self.is_trading_holiday(date_str):
            logger.info(f"{date_str} is a weekend or trading holiday. Skipping market execution.")
            return True

        # 1. Ingest & Validate Indices
        indices = self.stocks_config.get("indices", [])
        index_dfs = {}
        for idx in indices:
            if not idx.get("enabled", True):
                continue
            symbol = idx["yahoo_symbol"]
            df_raw = self.provider.get_historical_prices(symbol, period="3y")
            df_clean, report = self.validator.validate_ohlcv(df_raw, ticker=symbol)
            if not df_clean.empty:
                df_calc = TechnicalIndicators.compute_all(df_clean)
                index_dfs[idx["symbol"]] = df_calc
                self.store.save_processed_prices(idx["symbol"], df_calc)

        # 2. Ingest & Validate Stocks
        stocks = self.stocks_config.get("stocks", [])
        stock_dfs = {}
        all_reports = []
        all_features = []
        stock_analysis_list = []

        for stk in stocks:
            if not stk.get("enabled", True):
                continue
            symbol = stk["symbol"]
            yahoo_sym = stk["yahoo_symbol"]

            df_raw = self.provider.get_historical_prices(yahoo_sym, period="3y")
            df_clean, report = self.validator.validate_ohlcv(df_raw, ticker=symbol)
            all_reports.append(report)

            if df_clean.empty:
                logger.warning(f"Skipping {symbol} due to empty validated dataset.")
                continue

            # Indicators & Storage
            df_calc = TechnicalIndicators.compute_all(df_clean)
            stock_dfs[symbol] = df_calc
            self.store.save_processed_prices(symbol, df_calc)

            # Features
            feat_df = FeatureBuilder.build_features(df_calc, ticker=symbol)
            if not feat_df.empty:
                all_features.append(feat_df)

            # Fundamentals
            fund_data = self.provider.get_fundamentals(yahoo_sym)
            fund_eval = FundamentalAnalyzer.evaluate(fund_data)

            # Signals & Analogues
            signals = TechnicalIndicators.detect_signals(df_calc)
            analogues = HistoricalAnalogueAnalyzer.find_analogues(df_calc)
            directional_bias = MarketPredictor.generate_directional_bias(analogues)

            # Stock Scoring
            score_res = StockScorer.calculate_score(df_calc, fundamental_score=fund_eval["score"])

            stock_analysis_list.append({
                "symbol": symbol,
                "exchange": stk.get("exchange", "NSE"),
                "sector": stk.get("sector", "Unknown"),
                "composite_score": score_res["composite_score"],
                "score_label": score_res["label"],
                "score_components": score_res["components"],
                "signals": signals,
                "historical_analogues": analogues,
                "forward_probabilities": directional_bias,
                "fundamentals": fund_eval
            })

        # Save aggregated Quality Report
        total_processed = sum(r["records_processed"] for r in all_reports)
        total_valid = sum(r["records_valid"] for r in all_reports)
        combined_quality = {
            "date": date_str,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "warnings": [w for r in all_reports for w in r["warnings"]],
            "errors": [e for r in all_reports for e in r["errors"]]
        }
        self.store.save_quality_report(date_str, combined_quality)

        # Save Combined Daily Features
        if all_features:
            combined_feat = pd.concat(all_features, ignore_index=True)
            self.store.save_features(date_str, combined_feat)

        # 3. Market Regime Analysis
        nifty_df = index_dfs.get("NIFTY 50", pd.DataFrame())
        bank_df = index_dfs.get("NIFTY BANK", pd.DataFrame())
        regime_res = MarketRegimeAnalyzer.analyze_regime(nifty_df, bank_df, stock_dfs)

        # 4. Sector Performance Analysis
        sector_dfs = {k: v for k, v in index_dfs.items() if k != "NIFTY 50"}
        sector_res = SectorAnalyzer.analyze_sectors(sector_dfs, nifty_df)

        # 5. Assemble Daily Machine-Readable Analysis JSON
        daily_analysis_data = {
            "date": date_str,
            "market": regime_res,
            "sectors": sector_res,
            "stocks": stock_analysis_list,
            "data_quality": combined_quality
        }
        self.store.save_daily_analysis(date_str, daily_analysis_data)

        # 6. Generate Human-Readable Markdown Report
        md_report = DailyReportGenerator.generate_markdown_report(date_str, daily_analysis_data)
        self.store.save_daily_report(date_str, md_report)

        logger.info(f"Daily pipeline execution for {date_str} completed successfully!")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Daily Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (defaults to today)")
    args = parser.parse_args()

    pipeline = DailyMarketPipeline()
    pipeline.run(args.date)
