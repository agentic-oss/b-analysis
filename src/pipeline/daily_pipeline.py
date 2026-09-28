import os
import sys
import json
import argparse
import datetime
import logging
import pandas as pd

from src.utils.logger import setup_logger
from src.ingestion.provider import YFinanceProvider
from src.storage.store import StorageEngine
from src.validation.validator import DataValidator
from src.indicators.technical import TechnicalAnalysisEngine
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamental_analysis import FundamentalAnalyzer
from src.scoring.composite_score import CompositeScorer
from src.patterns.historical_analogue import HistoricalAnalogueEngine
from src.features.engineer import FeatureEngineer
from src.modeling.predictions import PredictionEngine
from src.backtesting.engine import BacktestEngine
from src.reporting.markdown_report import MarkdownReportGenerator
from src.reporting.json_output import JsonOutputGenerator
from src.utils.git_utils import git_commit_and_push

SECTOR_INDEX_MAP = {
    "INFORMATION TECHNOLOGY": "NIFTY IT",
    "BANKING": "NIFTY BANK",
    "AUTOMOBILE": "NIFTY AUTO",
    "PHARMACEUTICALS": "NIFTY PHARMA",
    "FMCG": "NIFTY FMCG",
    "METALS": "NIFTY METAL",
    "REALTY": "NIFTY REALTY",
    "ENERGY": "NIFTY ENERGY",
    "FINANCIAL SERVICES": "NIFTY FINANCIAL SERVICES"
}

def load_json_config(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run_daily_pipeline(target_date: str = None, auto_commit: bool = False):
    """
    Master daily market pipeline execution orchestrator.
    """
    logger = setup_logger("daily_pipeline", level="INFO")
    logger.info("==================================================")
    logger.info("STARTING DAILY INDIAN STOCK MARKET ANALYSIS PIPELINE")
    logger.info("==================================================")

    # 1. Load Configurations
    stocks_cfg = load_json_config("config/stocks.json")
    sys_cfg = load_json_config("config/config.json")
    holidays_cfg = load_json_config("config/holidays.json")

    if not target_date:
        target_date = datetime.date.today().strftime("%Y-%m-%d")

    logger.info(f"Target Trading Date: {target_date}")

    # Check Indian Trading Holiday
    year_str = target_date.split("-")[0]
    if target_date in holidays_cfg.get(year_str, []):
        logger.info(f"Date {target_date} is a listed Indian trading holiday. Skipping execution.")
        return

    # Check Weekend
    dt_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    if dt_obj.weekday() >= 5: # Saturday/Sunday
        logger.info(f"Date {target_date} is a weekend ({dt_obj.strftime('%A')}). Skipping execution.")
        return

    # Initialize Components
    provider = YFinanceProvider()
    store = StorageEngine(base_dir="data")
    validator = DataValidator()

    enabled_indices = [idx for idx in stocks_cfg.get("indices", []) if idx.get("enabled", True)]
    enabled_stocks = [stk for stk in stocks_cfg.get("stocks", []) if stk.get("enabled", True)]

    logger.info(f"Loaded {len(enabled_indices)} indices and {len(enabled_stocks)} stocks from stock universe.")

    # 2. Ingestion & Historical Sync for Benchmark & Indices
    index_dfs = {}
    for idx in enabled_indices:
        sym = idx["symbol"]
        ticker = idx["yahoo_ticker"]
        logger.info(f"Fetching data for Index: {sym} ({ticker})")
        df_idx = provider.get_index_data(ticker, start_date=None, end_date=None)
        if not df_idx.empty:
            store.save_processed_prices(sym, df_idx)
            hist_idx = store.load_processed_prices(sym)
            hist_idx_calc = TechnicalAnalysisEngine.calculate_indicators(hist_idx)
            index_dfs[sym] = hist_idx_calc

    nifty_df = index_dfs.get("NIFTY 50", pd.DataFrame())
    banknifty_df = index_dfs.get("NIFTY BANK", pd.DataFrame())

    # 3. Ingestion & Processing for Equities Universe
    stock_dfs = []
    stock_analyses = []
    daily_raw_rows = []

    for stk in enabled_stocks:
        sym = stk["symbol"]
        exch = stk.get("exchange", "NSE")
        logger.info(f"Ingesting & processing stock: {sym}")

        df_raw = provider.get_historical_prices(sym, exchange=exch)
        if not df_raw.empty:
            daily_raw_rows.append(df_raw.iloc[[-1]])
            store.save_processed_prices(sym, df_raw)

        # Load accumulated history
        hist_stock = store.load_processed_prices(sym)
        if hist_stock.empty:
            logger.warning(f"No price history found for {sym}. Skipping.")
            continue

        # Calculate Indicators
        hist_stock_calc = TechnicalAnalysisEngine.calculate_indicators(hist_stock)
        stock_dfs.append(hist_stock_calc)

    # Combine Raw Daily Data & Validate Quality
    if daily_raw_rows:
        combined_raw_today = pd.concat(daily_raw_rows, ignore_index=True)
    else:
        combined_raw_today = pd.DataFrame()

    valid_today_df, quality_report = validator.validate_daily_prices(combined_raw_today, target_date)
    store.save_raw_data(combined_raw_today, target_date, "prices")
    store.save_json(f"quality/{target_date}.json", quality_report)

    # 4. Market Regime Analysis
    market_regime_info = MarketRegimeAnalyzer.analyze_regime(nifty_df, banknifty_df, stock_dfs)

    # 5. Sector Analysis
    sector_index_dfs = {k: v for k, v in index_dfs.items() if k.startswith("NIFTY ") and k != "NIFTY 50"}
    sector_rankings = SectorAnalyzer.analyze_sectors(sector_index_dfs, nifty_df)

    # 6. Per-Stock Analysis, Scoring, Historical Analogues, ML Features & Signals
    feature_matrices = []

    for df_stock in stock_dfs:
        sym = df_stock.iloc[-1]['symbol']
        sec_name = next((stk.get("sector") for stk in enabled_stocks if stk["symbol"] == sym), "General")

        # Technical Patterns
        patterns = TechnicalAnalysisEngine.identify_patterns(df_stock)

        # Fundamental Data Evaluation
        fund_data = provider.get_fundamentals(sym)
        fund_eval = FundamentalAnalyzer.evaluate_fundamentals(fund_data)

        # Composite Scoring
        score_res = CompositeScorer.calculate_stock_score(
            df_stock=df_stock,
            market_regime_info=market_regime_info,
            sector_info=None,
            fundamental_info=fund_eval
        )

        # Historical Analogue Forward Probabilities
        analogues = HistoricalAnalogueEngine.find_analogues_and_forward_returns(df_stock)

        # Feature Dataset for ML
        sec_idx_key = SECTOR_INDEX_MAP.get(sec_name.upper(), f"NIFTY {sec_name.upper()}")
        sec_df = sector_index_dfs.get(sec_idx_key, pd.DataFrame())
        feat_df = FeatureEngineer.create_feature_dataset(
            df_stock=df_stock,
            market_df=nifty_df,
            sector_df=sec_df
        )
        if not feat_df.empty:
            feature_matrices.append(feat_df)

        # Predictive Forward Directional Signals
        fwd_signals = PredictionEngine.generate_directional_signals(feat_df)

        stock_analyses.append({
            "symbol": sym,
            "sector": sec_name,
            "close": float(df_stock.iloc[-1]['close']),
            "technical_score": score_res["total_score"],
            "label": score_res["label"],
            "components": score_res["components"],
            "fundamental_score": fund_eval["fundamental_score"],
            "fundamental_metrics": fund_eval["metrics"],
            "signals": patterns.get("signals", []),
            "support_levels": [patterns.get("support_1"), patterns.get("support_2")],
            "resistance_levels": [patterns.get("resistance_1"), patterns.get("resistance_2")],
            "historical_analogues": analogues,
            "forward_signals": fwd_signals
        })

    # Save Consolidated Feature Dataset
    if feature_matrices:
        combined_features = pd.concat(feature_matrices, ignore_index=True)
        store.save_features(target_date, combined_features)

    # 7. Construct Consolidated Daily Machine-Readable Output
    daily_output_data = {
        "date": target_date,
        "market": market_regime_info,
        "sectors": sector_rankings,
        "stocks": stock_analyses,
        "quality": quality_report
    }

    # Save JSON & Markdown Reports
    json_path = os.path.join("data/analysis/daily", f"{target_date}.json")
    report_path = os.path.join("reports/daily", f"{target_date}.md")

    JsonOutputGenerator.generate_json_output(daily_output_data, json_path)
    MarkdownReportGenerator.generate_report(daily_output_data, report_path)

    logger.info(f"Daily analysis JSON saved to: {json_path}")
    logger.info(f"Daily markdown report generated at: {report_path}")

    # 8. Git Automation (Optional / Configured)
    if auto_commit:
        commit_msg = f"data: daily Indian market analysis {target_date}"
        git_commit_and_push(commit_msg, push=False)

    logger.info("==================================================")
    logger.info("DAILY PIPELINE COMPLETED SUCCESSFULLY.")
    logger.info("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--commit", action="store_true", help="Auto-commit generated artifacts to Git")
    args = parser.parse_args()

    run_daily_pipeline(target_date=args.date, auto_commit=args.commit)
