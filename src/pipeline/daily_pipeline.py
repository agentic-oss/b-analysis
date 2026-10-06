import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.manager import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.scoring.composite import StockScorer
from src.patterns.analogue import PatternAnalogueFinder
from src.modeling.signals import ProbabilisticSignalGenerator
from src.features.builder import FeatureBuilder
from src.reporting.generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DailyPipeline")


class DailyPipeline:
    """Master orchestrator for the Daily Indian Stock Market Analysis Pipeline."""

    def __init__(self, config_path: str = "config/config.json", stocks_path: str = "config/stocks.json", holidays_path: str = "config/holidays.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        with open(stocks_path) as f:
            self.stocks_config = json.load(f)
        with open(holidays_path) as f:
            self.holidays_config = json.load(f)

        self.provider = YFinanceProvider(
            max_retries=self.config['pipeline'].get('max_retries', 3),
            retry_backoff=self.config['pipeline'].get('retry_backoff_sec', 2.0)
        )
        self.validator = DataValidator()
        self.storage = StorageManager(base_dir=self.config['storage'].get('base_dir', 'data'))
        self.market_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.scorer = StockScorer(custom_weights=self.config['scoring'].get('weights'))
        self.pattern_finder = PatternAnalogueFinder(
            top_k=self.config['patterns'].get('analogue_top_k', 25)
        )
        self.signal_generator = ProbabilisticSignalGenerator()

    def is_trading_holiday(self, date_str: str) -> bool:
        """Checks if given date is a weekend or scheduled market holiday."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() in (5, 6): # Saturday, Sunday
            return True
        year = dt.year
        holidays = self.holidays_config.get(f"holidays_{year}", [])
        return date_str in holidays

    def run(self, target_date_str: Optional[str] = None) -> bool:
        """Executes full end-to-end daily market analysis pipeline."""
        if not target_date_str:
            target_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        logger.info(f"Starting daily pipeline for target date: {target_date_str}")

        if self.is_trading_holiday(target_date_str):
            logger.info(f"Target date {target_date_str} is a weekend or market holiday. Pipeline execution skipped.")
            return True

        start_dt = (datetime.strptime(target_date_str, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")

        # 1. Ingest & Validate Indices
        index_dfs = {}
        for idx in self.stocks_config.get("indices", []):
            if not idx.get("enabled", True):
                continue
            sym = idx["symbol"]
            df_raw = self.provider.get_historical_prices(sym, start_dt, target_date_str)
            if not df_raw.empty:
                df_clean, _, _ = self.validator.validate_stock_dataframe(sym, df_raw)
                if not df_clean.empty:
                    df_ind = TechnicalIndicators.calculate_indicators(df_clean)
                    self.storage.append_processed_prices(sym, df_ind, category="indices")
                    index_dfs[idx["name"]] = df_ind

        nifty_df = index_dfs.get("NIFTY 50", pd.DataFrame())
        banknifty_df = index_dfs.get("NIFTY BANK", pd.DataFrame())

        # Sector indices dict
        sector_indices = {k: v for k, v in index_dfs.items() if "NIFTY" in k and k not in ["NIFTY 50", "NIFTY NEXT 50", "NIFTY 500"]}

        # 2. Ingest & Validate Stocks
        stock_dfs = {}
        all_warnings = []
        all_errors = []
        records_processed = 0
        records_valid = 0

        enabled_stocks = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]

        for st in enabled_stocks:
            sym = st["symbol"]
            ticker = st.get("yahoo_ticker", f"{sym}.NS")
            records_processed += 1

            df_raw = self.provider.get_historical_prices(ticker, start_dt, target_date_str)
            if df_raw.empty:
                all_errors.append({"ticker": sym, "type": "DOWNLOAD_FAILED", "message": f"Could not fetch data for {ticker}"})
                continue

            # Save raw
            self.storage.save_raw_daily(target_date_str, sym, df_raw)

            # Validate
            df_clean, warnings, errors = self.validator.validate_stock_dataframe(sym, df_raw)
            all_warnings.extend(warnings)
            all_errors.extend(errors)

            if not df_clean.empty:
                records_valid += 1
                df_ind = TechnicalIndicators.calculate_indicators(df_clean)
                self.storage.append_processed_prices(sym, df_ind, category="prices")
                stock_dfs[sym] = df_ind

        # Save Quality Report
        quality_report = self.validator.generate_quality_report(
            target_date_str, records_processed, records_valid, all_warnings, all_errors
        )
        self.storage.save_quality_report(target_date_str, quality_report)

        # 3. Market Regime & Sector Analysis
        market_analysis = self.market_analyzer.analyze_regime(nifty_df, banknifty_df, stock_dfs)
        sector_rankings = self.sector_analyzer.analyze_sectors(sector_indices, nifty_df)

        sector_rank_map = {sec['sector']: sec['rank'] for sec in sector_rankings}

        # 4. Process Each Stock Analysis & Feature Extraction
        stock_outputs = []
        feature_rows = []

        for st in enabled_stocks:
            sym = st["symbol"]
            if sym not in stock_dfs or stock_dfs[sym].empty:
                continue

            sdf = stock_dfs[sym]
            fund_raw = self.provider.get_fundamental_data(st.get("yahoo_ticker", f"{sym}.NS"))
            fund_analysis = FundamentalAnalyzer.analyze_fundamentals(fund_raw)

            # Scoring
            score_res = self.scorer.calculate_stock_score(sdf, nifty_df, market_analysis, fund_analysis)

            # Signal Identifiers
            signals = TechnicalIndicators.identify_signals(sdf)

            # Pattern Analogues
            analogues = self.pattern_finder.find_analogues(sdf)

            # Probabilistic Signals
            fwd_signals = self.signal_generator.generate_signals(score_res['composite_score'], analogues)

            # Stock analysis record
            stock_record = {
                "symbol": sym,
                "composite_score": score_res['composite_score'],
                "score_label": score_res['label'],
                "technical_score": score_res['components']['technical_trend'],
                "fundamental_score": fund_analysis['score'],
                "market_regime": market_analysis['regime'],
                "signals": signals,
                "historical_analogues": analogues,
                "forward_probabilities": fwd_signals
            }
            stock_outputs.append(stock_record)

            # ML Features
            sec_name = st.get("sector")
            sec_df = sector_indices.get(sec_name, pd.DataFrame())
            sec_rank = sector_rank_map.get(sec_name, 0)

            features = FeatureBuilder.build_stock_features(
                stock_symbol=sym,
                stock_df=sdf,
                nifty_df=nifty_df,
                sector_df=sec_df,
                regime_info=market_analysis,
                sector_rank=sec_rank,
                technical_score=score_res['components']['technical_trend'],
                fundamental_score=fund_analysis['score']
            )

            if not features.empty:
                # Extract daily feature row for target_date_str
                daily_feature = features.tail(1)
                feature_rows.append(daily_feature)

        # 5. Save Combined Daily Features
        if feature_rows:
            combined_features = pd.concat(feature_rows, ignore_index=True)
            feat_parquet = os.path.join(self.storage.features_dir, "daily", f"{target_date_str}.parquet")
            feat_csv = os.path.join(self.storage.features_dir, "daily", f"{target_date_str}.csv")
            combined_features.to_parquet(feat_parquet, index=False)
            combined_features.to_csv(feat_csv, index=False)

        # 6. Save Daily JSON & Markdown Analysis
        daily_json = ReportGenerator.generate_daily_json(
            target_date_str, market_analysis, sector_rankings, stock_outputs
        )
        self.storage.save_daily_analysis(target_date_str, daily_json)

        daily_md = ReportGenerator.generate_daily_markdown(
            target_date_str, market_analysis, sector_rankings, stock_outputs, quality_report
        )
        self.storage.save_daily_report(target_date_str, daily_md)

        logger.info(f"Daily pipeline completed successfully for {target_date_str}.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    args = parser.parse_args()

    pipeline = DailyPipeline()
    success = pipeline.run(args.date)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
