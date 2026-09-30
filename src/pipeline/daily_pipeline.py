import os
import json
import logging
import argparse
import datetime
import pandas as pd
import numpy as np

from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.data_validator import DataValidator
from src.storage.storage_manager import StorageManager
from src.indicators.technical import TechnicalIndicators
from src.patterns.pattern_engine import PatternEngine
from src.patterns.analogue_finder import AnalogueFinder
from src.market.market_regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.fundamentals.fundamental_analyzer import FundamentalAnalyzer
from src.features.feature_engine import FeatureEngine
from src.modeling.prediction_engine import PredictionEngine
from src.backtesting.backtester import Backtester
from src.reporting.report_generator import ReportGenerator

# Setup structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DailyPipeline")

def load_config():
    with open("config/stocks.json", "r") as f:
        stocks_cfg = json.load(f)
    with open("config/config.json", "r") as f:
        app_cfg = json.load(f)
    with open("config/holidays.json", "r") as f:
        holidays_cfg = json.load(f)
    return stocks_cfg, app_cfg, holidays_cfg

def run_pipeline(target_date: str = None, force_run: bool = False):
    if not target_date:
        target_date = datetime.datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Starting Daily Stock Market Pipeline for date: {target_date}")

    stocks_cfg, app_cfg, holidays_cfg = load_config()

    # Check holiday calendar
    if not force_run and target_date in holidays_cfg.get("holidays", []):
        logger.info(f"Date {target_date} is a scheduled market holiday. Skipping automated run.")
        return

    # Initialize modules
    provider = YFinanceProvider(
        retry_attempts=app_cfg.get("retry_attempts", 3),
        retry_delay=app_cfg.get("retry_delay_seconds", 2),
        timeout=app_cfg.get("timeout_seconds", 30)
    )
    validator = DataValidator()
    storage = StorageManager()
    analogue_finder = AnalogueFinder(
        rsi_tolerance=app_cfg.get("analogue_matching", {}).get("rsi_tolerance", 7.5),
        volatility_tolerance=app_cfg.get("analogue_matching", {}).get("volatility_tolerance", 0.10),
        top_k=app_cfg.get("analogue_matching", {}).get("similarity_top_k", 30)
    )
    regime_analyzer = MarketRegimeAnalyzer()
    sector_analyzer = SectorAnalyzer()
    scorer = StockScorer(weights=app_cfg.get("score_weights"))
    fund_analyzer = FundamentalAnalyzer()
    prediction_engine = PredictionEngine()
    reporter = ReportGenerator()

    # 1. Fetch & Ingest Historical Data
    lookback_days = app_cfg.get("default_fetch_days", 365)
    start_date = (pd.Timestamp(target_date) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    indices_list = stocks_cfg.get("indices", [])
    stocks_list = stocks_cfg.get("stocks", [])

    all_raw_dfs = []
    processed_stock_dfs = {}
    processed_index_dfs = {}

    warnings = []
    errors = []
    total_records = 0
    valid_records = 0

    logger.info("Ingesting index price data...")
    nifty_df = pd.DataFrame()
    bank_nifty_df = pd.DataFrame()

    for idx in indices_list:
        if not idx.get("enabled", True):
            continue
        sym = idx["symbol"]
        df = provider.get_index_data(sym, start_date=start_date, end_date=target_date)
        if not df.empty:
            all_raw_dfs.append(df)
            calc_df = TechnicalIndicators.calculate_all(df)
            processed_index_dfs[idx["name"]] = calc_df
            if sym == "^NSEI":
                nifty_df = calc_df
            elif sym == "^NSEBANK":
                bank_nifty_df = calc_df

    logger.info("Ingesting stock price & fundamental data...")
    for st in stocks_list:
        if not st.get("enabled", True):
            continue
        sym = st["symbol"]
        df = provider.get_historical_prices(sym, start_date=start_date, end_date=target_date)
        if not df.empty:
            total_records += len(df)
            is_valid, w, e = validator.validate_price_data(df, date_str=target_date)
            warnings.extend(w)
            errors.extend(e)

            if is_valid:
                valid_records += len(df)

            all_raw_dfs.append(df)
            calc_df = TechnicalIndicators.calculate_all(df)
            processed_stock_dfs[sym] = calc_df

    # 2. Save Raw & Processed Historical Data
    if all_raw_dfs:
        combined_raw = pd.concat(all_raw_dfs, ignore_index=True)
        storage.save_raw_data(combined_raw, target_date)
        storage.save_processed_prices(combined_raw)

    # Save Data Quality Report
    quality_report = validator.generate_quality_report(target_date, total_records, valid_records, warnings, errors)
    storage.save_quality_report(quality_report, target_date)

    # 3. Market Regime & Sector Analysis
    logger.info("Analyzing Market Regime and Sectors...")
    market_analysis = regime_analyzer.analyze_market_regime(nifty_df, bank_nifty_df, processed_stock_dfs)
    sector_analysis = sector_analyzer.analyze_sectors(processed_index_dfs, nifty_df)

    # 4. Stock Analysis, Scoring, Historical Analogues, and Forward Signals
    logger.info("Generating stock analyses and forward predictions...")
    stock_analyses = []
    all_features = []

    for st in stocks_list:
        if not st.get("enabled", True):
            continue
        sym = st["symbol"]
        sec = st.get("sector", "General")
        df = processed_stock_dfs.get(sym)

        if df is None or df.empty:
            continue

        latest = df.iloc[-1]

        # Pattern detection & Historical Analogues
        events_res = PatternEngine.detect_events(df)
        analogues = analogue_finder.find_analogues(df)

        # Fundamentals
        fund_raw = provider.get_fundamental_data(sym)
        fund_res = fund_analyzer.analyze_fundamentals(fund_raw)

        # Scoring
        score_res = scorer.score_stock(
            df,
            market_regime_score=market_analysis.get("regime_score", 50.0),
            fundamental_data=fund_raw
        )

        # Forward Probabilities Signals
        signals = prediction_engine.generate_forward_signals(analogues, score_res["composite_score"])

        # ML Features
        f_df = FeatureEngine.build_feature_set(df, nifty_df)
        if not f_df.empty:
            all_features.append(f_df)

        stock_analyses.append({
            "symbol": sym,
            "sector": sec,
            "close": round(float(latest.get('close', 0.0)), 2),
            "daily_return": round(float(latest.get('daily_return', 0.0)), 4),
            "rsi_14": round(float(latest.get('rsi_14', 50.0)), 2),
            "composite_score": score_res["composite_score"],
            "rating": score_res["label"],
            "score_components": score_res["components"],
            "technical_events": events_res["events"],
            "support_levels": events_res["support_levels"],
            "resistance_levels": events_res["resistance_levels"],
            "fundamentals": fund_res,
            "historical_analogues": analogues,
            "signals": signals
        })

    # Save daily ML features
    if all_features:
        combined_features = pd.concat(all_features, ignore_index=True)
        storage.save_features(combined_features, target_date)

    # 5. Generate Outputs & Reports
    logger.info("Generating daily Markdown & JSON reports...")
    json_output = reporter.generate_json_output(target_date, market_analysis, sector_analysis, stock_analyses, quality_report)
    storage.save_daily_analysis(json_output, target_date)

    md_report = reporter.generate_markdown_report(target_date, market_analysis, sector_analysis, stock_analyses, quality_report)
    storage.save_daily_report(md_report, target_date)

    logger.info(f"Pipeline completed successfully for {target_date}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Pipeline")
    parser.add_argument("--date", type=str, help="Target date YYYY-MM-DD", default=None)
    parser.add_argument("--force", action="store_true", help="Force run even on scheduled holidays")
    args = parser.parse_args()

    run_pipeline(target_date=args.date, force_run=args.force)
