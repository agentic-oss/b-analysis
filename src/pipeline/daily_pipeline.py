import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage import DataStorage
from src.indicators.indicators import TechnicalIndicators
from src.fundamentals.fundamentals import FundamentalsCollector
from src.market.regime import MarketRegimeDetector
from src.sectors.sectors import SectorAnalyzer
from src.scoring.scoring import StockScorer
from src.patterns.analogues import HistoricalPatternMatcher
from src.features.builder import FeatureBuilder
from src.modeling.baselines import PredictionResearchLayer
from src.backtesting.backtest import Backtester
from src.reporting.report import DailyReportGenerator
from src.utils.git_utils import GitIntegrator

def setup_logging(config: dict):
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO"))
    fmt = log_config.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.basicConfig(level=level, format=fmt)

def is_market_holiday(date_str: str, holidays_path: str = "config/holidays.json") -> bool:
    if os.path.exists(holidays_path):
        with open(holidays_path, "r") as f:
            data = json.load(f)
            return date_str in data.get("holidays", [])
    return False

def run_pipeline(
    target_date: str = None,
    config_path: str = "config/config.json",
    stocks_path: str = "config/stocks.json",
    dry_run: bool = False
):
    if target_date is None:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load configurations
    with open(config_path, "r") as f:
        config = json.load(f)
    with open(stocks_path, "r") as f:
        stocks_config = json.load(f)

    setup_logging(config)
    logger = logging.getLogger("DailyPipeline")
    logger.info(f"Starting Daily Market Analysis Pipeline for date: {target_date}")

    # Check holiday calendar
    if is_market_holiday(target_date):
        logger.info(f"Date {target_date} is a declared Indian stock market holiday. Pipeline execution halted gracefully.")
        return

    storage = DataStorage(base_dir=config.get("pipeline", {}).get("data_dir", "data"))
    provider = YFinanceProvider(
        max_retries=config["provider"]["max_retries"],
        retry_backoff=config["provider"]["retry_backoff_factor"],
        timeout=config["provider"]["timeout_seconds"]
    )
    validator = DataValidator()

    lookback_days = config.get("pipeline", {}).get("lookback_days", 730)
    start_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # 1. Ingest Indices Data
    indices_dfs = {}
    nifty_df = pd.DataFrame()
    banknifty_df = pd.DataFrame()

    for idx_info in stocks_config.get("indices", []):
        if not idx_info.get("enabled", True):
            continue
        sym = idx_info["symbol"]
        logger.info(f"Ingesting index: {sym} ({idx_info.get('name')})")
        try:
            raw_idx = provider.get_index_data(sym, start_date=start_date, end_date=target_date)
            if not raw_idx.empty:
                ind_df = TechnicalIndicators.calculate_all(raw_idx, config=config.get("indicators"))
                storage.save_processed_prices(ind_df, sym.replace("^", ""), is_index=True)
                indices_dfs[idx_info.get("name", sym)] = ind_df
                if idx_info.get("name") == "NIFTY 50" or sym == "^NSEI":
                    nifty_df = ind_df
                if idx_info.get("name") == "NIFTY Bank" or sym == "^NSEBANK":
                    banknifty_df = ind_df
        except Exception as e:
            logger.error(f"Error fetching index {sym}: {str(e)}")

    # 2. Ingest Stocks Data & Validate
    stocks_dfs = {}
    quality_warnings = []
    quality_errors = []
    processed_count = 0
    valid_count = 0

    stock_list = stocks_config.get("stocks", [])
    for st_info in stock_list:
        if not st_info.get("enabled", True):
            continue
        processed_count += 1
        sym = st_info["symbol"]
        ticker = st_info.get("ticker", sym)
        logger.info(f"Ingesting stock: {ticker} ({sym})")

        try:
            raw_stock = provider.get_historical_prices(sym, start_date=start_date, end_date=target_date)
            if raw_stock.empty:
                quality_errors.append(f"No price data received for {sym}")
                continue

            storage.save_raw_data(raw_stock, ticker, target_date)
            v_res = validator.validate_ohlc(raw_stock, sym)
            quality_warnings.extend(v_res.get("warnings", []))
            quality_errors.extend(v_res.get("errors", []))

            if v_res["is_valid"]:
                valid_count += 1

            calc_df = TechnicalIndicators.calculate_all(raw_stock, config=config.get("indicators"))
            storage.save_processed_prices(calc_df, ticker, is_index=False)
            stocks_dfs[ticker] = calc_df

        except Exception as e:
            logger.error(f"Error processing stock {sym}: {str(e)}")
            quality_errors.append(f"Exception during ingestion of {sym}: {str(e)}")

    # Save Quality Report
    quality_report = {
        "date": target_date,
        "records_processed": processed_count,
        "records_valid": valid_count,
        "warnings": quality_warnings,
        "errors": quality_errors
    }
    storage.save_quality_report(quality_report, target_date)

    # 3. Market Regime & Sector Analysis
    regime_info = MarketRegimeDetector.detect_regime(nifty_df, banknifty_df, stocks_dfs)
    sector_indices_dfs = {k: v for k, v in indices_dfs.items() if k.startswith("NIFTY") and k != "NIFTY 50"}
    sectors_ranking = SectorAnalyzer.analyze_sectors(sector_indices_dfs, nifty_df)
    sector_map = {s["sector"]: s for s in sectors_ranking}

    # 4. Stock Scoring, Pattern Analogues, Features & Forecast Signals
    daily_stock_outputs = []
    all_feature_dfs = []

    for st_info in stock_list:
        if not st_info.get("enabled", True):
            continue
        ticker = st_info.get("ticker", st_info["symbol"])
        df = stocks_dfs.get(ticker)
        if df is None or df.empty:
            continue

        sec_name = st_info.get("sector", "")
        sec_info = sector_map.get(sec_name)
        fund_info = FundamentalsCollector.get_fundamentals(st_info["symbol"])

        score_res = StockScorer.calculate_score(
            df, nifty_df, regime_info, sec_info, fund_info, config.get("scoring_weights")
        )
        analogues_res = HistoricalPatternMatcher.find_analogues(df, horizons=config.get("horizons", [1, 3, 5, 10, 20]))
        signals_res = PredictionResearchLayer.generate_directional_bias(score_res["composite_score"], analogues_res)

        sec_df = sector_indices_dfs.get(sec_name)
        feat_df = FeatureBuilder.build_features(df, ticker, nifty_df, sec_df, include_targets=True)
        all_feature_dfs.append(feat_df)

        last = df.iloc[-1]
        daily_stock_outputs.append({
            "symbol": st_info["symbol"],
            "ticker": ticker,
            "sector": sec_name,
            "composite_score": score_res["composite_score"],
            "label": score_res["label"],
            "score_components": score_res["components"],
            "relative_volume": float(last.get("relative_volume", 1.0)),
            "rsi_14": float(last.get("rsi_14", 50.0)),
            "breakout_20d": bool(last.get("breakout_20d", False)),
            "breakdown_20d": bool(last.get("breakdown_20d", False)),
            "historical_analogues": analogues_res,
            "signals": signals_res,
            "fundamentals": fund_info
        })

    # Combine and save feature dataset
    if all_feature_dfs:
        combined_features = pd.concat(all_feature_dfs, ignore_index=True)
        storage.save_features(combined_features, target_date)

    # 5. Machine-Readable Daily Analysis Export
    analysis_payload = {
        "date": target_date,
        "market": regime_info,
        "sectors": sectors_ranking,
        "stocks": daily_stock_outputs,
        "quality": quality_report
    }
    storage.save_daily_analysis(analysis_payload, target_date)

    # 6. Human-Readable Daily Markdown Report
    report_path = os.path.join(config.get("pipeline", {}).get("reports_dir", "reports"), "daily", f"{target_date}.md")
    DailyReportGenerator.generate_markdown(analysis_payload, report_path)
    logger.info(f"Daily analysis and Markdown report generated at {report_path}")

    # 7. Git Integration Auto Commit
    if not dry_run:
        GitIntegrator.commit_and_push(target_date)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Data & Deep Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Target date YYYY-MM-DD (defaults to UTC today)")
    parser.add_argument("--dry-run", action="store_true", help="Run without committing to Git")
    args = parser.parse_args()

    run_pipeline(target_date=args.date, dry_run=args.dry_run)
