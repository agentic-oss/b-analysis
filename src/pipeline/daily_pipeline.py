import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any

import pandas as pd

from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage_manager import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.fundamentals.fundamental import FundamentalAnalysis
from src.market.market_sector import MarketRegime, SectorAnalysis
from src.scoring.scorer import StockScorer
from src.patterns.pattern_engine import PatternAnalogueEngine
from src.features.feature_engineer import FeatureEngineer
from src.reporting.report_generator import ReportGenerator

logger = logging.getLogger("DailyPipeline")


class DailyPipeline:
    """
    End-to-End Orchestrator for Indian Stock Market Data & Deep Analysis Pipeline.
    """

    def __init__(self, config_dir: str = "config", data_dir: str = "data"):
        self.config_dir = config_dir
        self.storage = StorageManager(base_dir=data_dir)

        # Load configs
        with open(os.path.join(config_dir, "config.json")) as f:
            self.config = json.load(f)
        with open(os.path.join(config_dir, "stocks.json")) as f:
            self.stocks_config = json.load(f)
        with open(os.path.join(config_dir, "holidays.json")) as f:
            self.holidays = json.load(f).get("holidays", {})

        p_conf = self.config.get("pipeline", {})
        self.provider = YFinanceProvider(
            max_retries=p_conf.get("max_retries", 3),
            retry_backoff=p_conf.get("retry_backoff_seconds", 2.0),
            timeout=p_conf.get("timeout_seconds", 30.0),
        )
        self.validator = DataValidator()
        self.pattern_engine = PatternAnalogueEngine()

    def is_holiday(self, date_str: str) -> bool:
        year = date_str.split("-")[0]
        holiday_list = self.holidays.get(year, [])
        return date_str in holiday_list

    def run(self, target_date: str, auto_commit: bool = False):
        logger.info(f"--- Starting Daily Pipeline for Date: {target_date} ---")

        if self.is_holiday(target_date):
            logger.info(f"Target date {target_date} is an Indian market holiday. Exiting cleanly.")
            return

        quality_reports = []
        all_stock_features: Dict[str, pd.DataFrame] = {}
        all_stock_latest: Dict[str, pd.DataFrame] = {}

        # 1. Ingest Indices
        indices_data: Dict[str, pd.DataFrame] = {}
        for idx in self.stocks_config.get("indices", []):
            if not idx.get("enabled", True):
                continue
            sym = idx["symbol"]
            name = idx["name"]
            logger.info(f"Ingesting index data: {name} ({sym})")
            df_raw = self.provider.get_historical_prices(sym, period="5y")
            df_clean, q_rep = self.validator.validate(name, df_raw, target_date)
            quality_reports.append(q_rep)

            if not df_clean.empty:
                df_ind = TechnicalIndicators.compute_all(df_clean)
                self.storage.save_processed_prices(df_ind, sym, idx.get("exchange", "NSE"))
                # Filter by target_date to avoid look-ahead bias if running historical dates
                df_ind_filtered = df_ind[df_ind["date"] <= target_date].copy()
                indices_data[name] = df_ind_filtered

        nifty_df = indices_data.get("NIFTY 50", pd.DataFrame())
        bank_nifty_df = indices_data.get("NIFTY Bank", pd.DataFrame())

        # 2. Ingest Stocks
        stocks_data: Dict[str, pd.DataFrame] = {}

        for st in self.stocks_config.get("stocks", []):
            if not st.get("enabled", True):
                continue
            sym = st["symbol"]
            ticker = st.get("ticker", sym)
            exchange = st.get("exchange", "NSE")
            sector = st.get("sector", "Uncategorized")

            logger.info(f"Ingesting equity data: {ticker} ({sym})")
            df_raw = self.provider.get_historical_prices(sym, period="5y")

            # Save Raw Data
            self.storage.save_raw_data(df_raw, ticker, exchange, target_date)

            # Validate
            df_clean, q_rep = self.validator.validate(ticker, df_raw, target_date)
            quality_reports.append(q_rep)

            if df_clean.empty:
                continue

            # Compute Technical Indicators
            df_ind = TechnicalIndicators.compute_all(df_clean)

            # Save Processed Prices
            self.storage.save_processed_prices(df_ind, ticker, exchange)

            # Feature Engineering
            sector_df = indices_data.get(sector, pd.DataFrame())
            df_feat = FeatureEngineer.generate_features(df_ind, nifty_df, sector_df)
            self.storage.save_features(df_feat, ticker)

            # Filter data strictly up to target_date for analysis
            df_ind_filtered = df_ind[df_ind["date"] <= target_date].copy()
            df_feat_filtered = df_feat[df_feat["date"] <= target_date].copy()

            if not df_ind_filtered.empty:
                all_stock_features[ticker] = df_feat_filtered
                all_stock_latest[ticker] = df_ind_filtered
                stocks_data[ticker] = df_ind_filtered

        # 3. Market Regime Analysis
        market_regime = MarketRegime.analyze_regime(nifty_df, bank_nifty_df, all_stock_latest, target_date)

        # 4. Sector Analysis
        sector_indices = {
            k: v for k, v in indices_data.items() if k not in ["NIFTY 50", "NIFTY Bank"]
        }
        sectors_analysis = SectorAnalysis.analyze_sectors(sector_indices, nifty_df)
        sector_rank_map = {s["sector"]: s for s in sectors_analysis}

        # 5. Stock Scoring, Pattern Analogues & Fundamentals
        analyzed_stocks = []
        for st in self.stocks_config.get("stocks", []):
            if not st.get("enabled", True):
                continue
            ticker = st.get("ticker", st["symbol"])
            sym = st["symbol"]
            sector = st.get("sector", "Uncategorized")

            if ticker not in all_stock_latest or all_stock_latest[ticker].empty:
                continue

            df_ind = all_stock_latest[ticker]
            latest_row = df_ind.iloc[-1].to_dict()
            latest_row["ticker"] = ticker

            sec_info = sector_rank_map.get(sector, {"rank": 10})
            score_res = StockScorer.calculate_score(latest_row, market_regime, sec_info)

            # Pattern Analogues
            analogues_res = self.pattern_engine.find_analogues(df_ind, latest_row)

            # Fundamentals
            f_info = FundamentalAnalysis.get_fundamentals(sym)

            stock_analysis = {
                "symbol": ticker,
                "exchange": st.get("exchange", "NSE"),
                "sector": sector,
                "technical_score": score_res["total_score"],
                "score_label": score_res["label"],
                "score_components": score_res["components"],
                "daily_return_pct": round(float(latest_row.get("return_1d", 0.0)) * 100.0, 2),
                "rsi_14": round(float(latest_row.get("rsi_14", 50.0)), 2),
                "volatility": latest_row.get("volatility_regime", "Normal"),
                "signals": {
                    "breakout": bool(latest_row.get("breakout", False)),
                    "breakdown": bool(latest_row.get("breakdown", False)),
                    "unusual_volume": bool(latest_row.get("relative_volume", 1.0) > 2.0),
                    "golden_cross": bool(latest_row.get("golden_cross", False)),
                    "death_cross": bool(latest_row.get("death_cross", False)),
                },
                "historical_analogues": analogues_res,
                "fundamentals": f_info,
            }
            analyzed_stocks.append(stock_analysis)

        # 6. Aggregate Data Quality Report
        total_proc = sum(q["total_records"] for q in quality_reports)
        valid_proc = sum(q["valid_records"] for q in quality_reports)
        all_warns = [w for q in quality_reports for w in q["warnings"]]
        all_errs = [e for q in quality_reports for e in q["errors"]]

        aggregate_quality = {
            "date": target_date,
            "records_processed": total_proc,
            "records_valid": valid_proc,
            "warnings": all_warns,
            "errors": all_errs,
        }
        self.storage.save_quality_report(target_date, aggregate_quality)

        # 7. Machine-Readable Analysis JSON
        daily_analysis_json = {
            "date": target_date,
            "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
            "market": market_regime,
            "sectors": sectors_analysis,
            "stocks": analyzed_stocks,
            "data_quality": aggregate_quality,
        }
        self.storage.save_daily_analysis(target_date, daily_analysis_json)

        # 8. Human-Readable Markdown Report
        md_report = ReportGenerator.generate_markdown_report(target_date, daily_analysis_json)
        self.storage.save_daily_report(target_date, md_report)

        logger.info(f"--- Completed Daily Pipeline for Date: {target_date} ---")

        if auto_commit:
            self._commit_results(target_date)

    def _commit_results(self, date_str: str):
        try:
            subprocess.run(["git", "add", "data/analysis/", "data/quality/", "reports/"], check=True)
            msg = f"data: daily Indian market analysis {date_str}"
            subprocess.run(["git", "commit", "-m", msg], check=True)
            logger.info(f"Successfully committed generated analysis for {date_str}")
        except Exception as e:
            logger.warning(f"Git commit failed or no changes to commit: {e}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Pipeline")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Target Date YYYY-MM-DD")
    parser.add_argument("--auto-commit", action="store_true", help="Auto commit generated data")
    args = parser.parse_args()

    pipeline = DailyPipeline()
    pipeline.run(target_date=args.date, auto_commit=args.auto_commit)


if __name__ == "__main__":
    main()
