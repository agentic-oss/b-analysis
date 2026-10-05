"""
Orchestration Daily Market Pipeline.
Executes ingestion -> validation -> storage -> indicator calculation -> market & sector analysis -> scoring -> analogues & features -> predictions -> backtest -> daily report & JSON output.
"""

import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

from src.ingestion.provider import YFinanceProvider
from src.validation.data_validator import DataValidator
from src.storage.storage_manager import StorageManager
from src.indicators.technical import TechnicalAnalyzer
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.fundamentals.fundamental_analyzer import FundamentalAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.patterns.analogue_finder import HistoricalAnalogueFinder
from src.features.feature_builder import FeatureBuilder
from src.modeling.predictor import DirectionalPredictor
from src.backtesting.backtester import BacktestingEngine
from src.reporting.report_generator import ReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DailyPipeline")


def load_json_config(file_path: str) -> Dict:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def is_trading_holiday(date_str: str, holidays_file: str = "config/holidays.json") -> bool:
    holidays_data = load_json_config(holidays_file)
    trading_holidays = holidays_data.get("trading_holidays", [])
    return date_str in trading_holidays


def run_pipeline(date_str: Optional[str] = None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Starting Daily Market Pipeline for date: {date_str}")

    # 0. Check Trading Holiday
    if is_trading_holiday(date_str):
        logger.info(f"Date {date_str} is a scheduled NSE trading holiday. Skipping execution.")
        return

    # Load configurations
    stocks_cfg = load_json_config("config/stocks.json")
    main_cfg = load_json_config("config/config.json")

    provider = YFinanceProvider()
    validator = DataValidator()
    storage = StorageManager()
    backtester = BacktestingEngine()
    predictor = DirectionalPredictor()

    indices_cfg = stocks_cfg.get("indices", [])
    equities_cfg = stocks_cfg.get("stocks", [])

    all_warnings = []
    all_errors = []
    processed_count = 0
    valid_count = 0

    processed_indices = {}
    processed_stocks = {}
    stock_analysis_results = []
    all_features_list = []

    # 1. Fetch & Process Benchmark Indices
    nifty_df = pd.DataFrame()
    bank_nifty_df = pd.DataFrame()

    for idx in indices_cfg:
        if not idx.get("enabled", True):
            continue
        symbol = idx["symbol"]
        name = idx["name"]
        processed_count += 1

        df_raw = provider.get_index_data(symbol)
        if not df_raw.empty:
            storage.save_raw_data(df_raw, symbol, date_str)
            df_valid, warn, err = validator.validate_df(df_raw, symbol)
            all_warnings.extend(warn)
            all_errors.extend(err)

            if not df_valid.empty:
                valid_count += 1
                df_hist = storage.update_historical_dataset(df_valid, symbol, category="indices")
                df_ind = TechnicalAnalyzer.calculate_indicators(df_hist)
                processed_indices[name] = df_ind

                if name == "NIFTY 50":
                    nifty_df = df_ind
                elif name == "NIFTY BANK":
                    bank_nifty_df = df_ind

    # 2. Fetch & Process Equities
    for st in equities_cfg:
        if not st.get("enabled", True):
            continue
        ticker = st["ticker"]
        symbol = st["symbol"]
        sector = st.get("sector", "General")
        processed_count += 1

        df_raw = provider.get_historical_prices(ticker)
        if not df_raw.empty:
            storage.save_raw_data(df_raw, symbol, date_str)
            df_valid, warn, err = validator.validate_df(df_raw, symbol)
            all_warnings.extend(warn)
            all_errors.extend(err)

            if not df_valid.empty:
                valid_count += 1
                df_hist = storage.update_historical_dataset(df_valid, symbol, category="prices")
                df_ind = TechnicalAnalyzer.calculate_indicators(df_hist)
                processed_stocks[symbol] = df_ind

                # Fundamental Analysis
                fund_data = FundamentalAnalyzer.get_fundamentals(ticker)
                fund_score, _ = FundamentalAnalyzer.calculate_fundamental_score(fund_data)

                # Feature Set Construction
                sec_df = processed_indices.get(f"NIFTY {sector.upper()}", pd.DataFrame())
                feat_df = FeatureBuilder.build_feature_set(df_ind, symbol, sec_df, nifty_df)
                if not feat_df.empty:
                    all_features_list.append(feat_df.iloc[-1:])

    # 3. Market Regime Analysis
    market_regime = MarketRegimeAnalyzer.analyze_market_regime(nifty_df, bank_nifty_df, processed_stocks)

    # 4. Sector Analysis
    sector_indices = {k: v for k, v in processed_indices.items() if k != "NIFTY 50"}
    sector_results = SectorAnalyzer.analyze_sectors(sector_indices, nifty_df)

    # 5. Individual Stock Analysis & Predictions
    regime_score = market_regime.get("score", 0.0)

    for symbol, df_ind in processed_stocks.items():
        signals_data = TechnicalAnalyzer.identify_signals(df_ind)
        score_data = StockScorer.score_stock(df_ind, market_regime_score=regime_score)
        analogues = HistoricalAnalogueFinder.find_analogues(df_ind)

        # Features and Forward Prediction
        sec_name = next((s.get("sector", "General") for s in equities_cfg if s["symbol"] == symbol), "General")
        sec_df = processed_indices.get(f"NIFTY {sec_name.upper()}", pd.DataFrame())
        feat_df = FeatureBuilder.build_feature_set(df_ind, symbol, sec_df, nifty_df)
        pred_signals = predictor.predict_signals(feat_df)

        # Backtest summary on stock
        bt_results = backtester.run_sma_crossover_backtest(df_ind)

        stock_analysis_results.append({
            "symbol": symbol,
            "market_regime": market_regime.get("regime", "Neutral"),
            "score": score_data,
            "signals": signals_data.get("signals", []),
            "support_resistance": signals_data.get("support_resistance", {}),
            "historical_analogues": analogues,
            "forward_probabilities": pred_signals,
            "backtest_summary": bt_results
        })

    # Save Feature Dataset
    if all_features_list:
        combined_features = pd.concat(all_features_list, ignore_index=True)
        storage.save_features(combined_features, date_str)

    # 6. Quality Report
    quality_report = validator.create_quality_report(date_str, processed_count, valid_count, all_warnings, all_errors)
    storage.save_quality_report(quality_report, date_str)

    # 7. Machine-Readable Daily Output
    json_output = ReportGenerator.generate_json_output(
        date_str, market_regime, sector_results, stock_analysis_results, quality_report
    )
    storage.save_daily_analysis_json(json_output, date_str)

    # 8. Human-Readable Daily Markdown Report
    md_report = ReportGenerator.generate_markdown_report(
        date_str, market_regime, sector_results, stock_analysis_results, quality_report
    )
    storage.save_daily_report_md(md_report, date_str)

    logger.info(f"Pipeline run completed for {date_str}. Processed: {processed_count}, Valid: {valid_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format", default=None)
    args = parser.parse_args()
    run_pipeline(args.date)
