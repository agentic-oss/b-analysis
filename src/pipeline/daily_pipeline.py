"""
Daily Indian Stock Market Pipeline Orchestrator.
Executes ingestion, validation, technical analysis, regime detection, sector ranking,
fundamental evaluation, analogue pattern lookup, feature engineering, prediction,
and report generation.
"""

import argparse
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import sys

from src.ingestion.provider import YFinanceProvider, MockDataProvider
from src.validation.quality import DataValidator, QualityReportGenerator
from src.storage.store import DataStore
from src.indicators.technical import calculate_technical_indicators, detect_technical_signals
from src.market.regime import analyze_market_regime
from src.sectors.analysis import analyze_sectors
from src.fundamentals.analysis import analyze_fundamentals
from src.scoring.composite import calculate_composite_score
from src.patterns.analogues import find_historical_analogues
from src.features.engineering import generate_ml_features_and_targets
from src.modeling.prediction import ProbabilisticForecastModel
from src.reporting.report_generator import generate_json_analysis, generate_markdown_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("daily_pipeline")


class DailyPipeline:
    def __init__(self, run_date: str, use_mock: bool = False, config_path: str = "config/config.json", stocks_path: str = "config/stocks.json"):
        self.run_date = run_date
        self.use_mock = use_mock

        # Load configs
        with open(config_path) as f:
            self.config = json.load(f)

        with open(stocks_path) as f:
            self.stocks_config = json.load(f)

        # Select provider
        if use_mock:
            self.provider = MockDataProvider()
            logger.info("Using MockDataProvider for execution.")
        else:
            self.provider = YFinanceProvider()
            logger.info("Using YFinanceProvider for execution.")

        self.validator = DataValidator()
        self.store = DataStore()
        self.forecast_model = ProbabilisticForecastModel()

    def run(self):
        logger.info(f"=== STARTING DAILY PIPELINE FOR {self.run_date} ===")
        quality_gen = QualityReportGenerator(self.run_date)

        # Calculate historical date bounds
        lookback_days = self.config.get("historical_lookback_days", 730)
        dt_end = datetime.strptime(self.run_date, "%Y-%m-%d") + timedelta(days=1)
        dt_start = dt_end - timedelta(days=lookback_days)
        start_str = dt_start.strftime("%Y-%m-%d")
        end_str = dt_end.strftime("%Y-%m-%d")

        # 1. Process Index Data
        logger.info("--- Ingesting Benchmark & Sector Indices ---")
        indices_data = {}
        for idx_item in self.stocks_config.get("indices", []):
            if not idx_item.get("enabled", True):
                continue
            symbol = idx_item["symbol"]
            df_raw = self.provider.get_index_data(symbol, start_str, end_str)

            df_val, warnings, errors = self.validator.validate_stock_dataframe(symbol, df_raw)
            quality_gen.add_validation_result(symbol, df_val, warnings, errors)

            if not df_val.empty:
                df_updated = self.store.update_processed_dataset(symbol, df_val, category="indices")
                df_ind = calculate_technical_indicators(df_updated)
                indices_data[symbol] = df_ind

        nifty_df = indices_data.get("^NSEI")
        banknifty_df = indices_data.get("^NSEBANK")

        if nifty_df is None or nifty_df.empty:
            logger.warning("NIFTY 50 data unavailable; generating fallback.")
            nifty_df = MockDataProvider().get_historical_prices("^NSEI", start_str, end_str)
            nifty_df = calculate_technical_indicators(nifty_df)

        if banknifty_df is None or banknifty_df.empty:
            banknifty_df = nifty_df

        # 2. Process Equities Data
        logger.info("--- Ingesting Equities Data ---")
        stock_dfs = {}
        stocks_summary = []
        all_features = []

        for st_item in self.stocks_config.get("stocks", []):
            if not st_item.get("enabled", True):
                continue

            symbol = st_item["symbol"]
            yahoo_ticker = st_item.get("yahoo_ticker", symbol)

            df_raw = self.provider.get_historical_prices(yahoo_ticker, start_str, end_str)
            df_val, warnings, errors = self.validator.validate_stock_dataframe(symbol, df_raw)
            quality_gen.add_validation_result(symbol, df_val, warnings, errors)

            if df_val.empty:
                logger.error(f"No valid data available for stock {symbol}")
                continue

            # Save raw & update processed
            self.store.save_raw_snapshot(self.run_date, symbol, df_val)
            df_updated = self.store.update_processed_dataset(symbol, df_val, category="prices")
            df_ind = calculate_technical_indicators(df_updated)
            stock_dfs[symbol] = df_ind

            # 3. Technical Signals
            tech_signals = detect_technical_signals(df_ind)

            # 4. Fundamentals
            raw_fund_info = self.provider.get_corporate_actions(symbol) if not self.use_mock else None
            fund_res = analyze_fundamentals(symbol, raw_fund_info)

            # 5. Historical Analogues
            analogues_res = find_historical_analogues(df_ind)

            # 6. Feature Matrix Engineering
            sector_df = indices_data.get(st_item.get("sector_index", "^NSEI"))
            feat_df = generate_ml_features_and_targets(df_ind, symbol, market_df=nifty_df, sector_df=sector_df)
            if not feat_df.empty:
                all_features.append(feat_df)

            # Temporary interim summary
            latest = df_ind.iloc[-1]
            stocks_summary.append({
                "symbol": symbol,
                "sector": st_item.get("sector"),
                "close": float(round(latest["Close"], 2)),
                "daily_return": round(float(latest.get("daily_return", 0.0) * 100.0), 2),
                "trend": tech_signals["trend"],
                "rsi_14": round(float(latest.get("rsi_14", 50.0)), 1),
                "volatility_20d": round(float(latest.get("volatility_20d", 15.0)), 1),
                "relative_volume": round(float(latest.get("relative_volume", 1.0)), 2),
                "signals": tech_signals,
                "fundamentals": fund_res,
                "historical_analogues": analogues_res,
                "stock_df_ref": df_ind
            })

        # 7. Analyze Market Regime & Sectors
        logger.info("--- Analyzing Market Regime & Sector Rotation ---")
        market_regime = analyze_market_regime(nifty_df, banknifty_df, stock_dfs)

        sector_dfs_mapped = {}
        for idx_item in self.stocks_config.get("indices", []):
            if idx_item.get("category") == "sector" and idx_item["symbol"] in indices_data:
                sector_dfs_mapped[idx_item["name"]] = indices_data[idx_item["symbol"]]

        sector_rankings = analyze_sectors(sector_dfs_mapped, nifty_df)

        # 8. Compute Composite Stock Scores & Probabilistic Forecasts
        logger.info("--- Computing Composite Stock Scores & Forecast Signals ---")
        for st_data in stocks_summary:
            symbol = st_data["symbol"]
            df_ind = st_data.pop("stock_df_ref")

            # Match sector info
            sec_info = next((s for s in sector_rankings if s["sector"] == st_data.get("sector")), None)

            # Composite score
            score_res = calculate_composite_score(
                df_ind,
                market_regime,
                sector_info=sec_info,
                fundamental_info=st_data["fundamentals"]
            )
            st_data["composite_score"] = score_res["composite_score"]
            st_data["label"] = score_res["label"]
            st_data["score_components"] = score_res["components"]

            # Forecast signals
            st_data["signals_forecast"] = self.forecast_model.generate_directional_signals(
                df_ind,
                st_data["historical_analogues"],
                score_res
            )

        # 9. Save Features & Reports
        logger.info("--- Saving Engineered Features & Generating Reports ---")
        quality_report_dict = quality_gen.to_dict()
        self.store.save_quality_report(self.run_date, quality_report_dict)

        if all_features:
            combined_feat_df = pd.concat(all_features, ignore_index=True)
            self.store.save_features(self.run_date, combined_feat_df)

        json_analysis = generate_json_analysis(
            self.run_date, market_regime, sector_rankings, stocks_summary, quality_report_dict
        )
        self.store.save_daily_analysis_json(self.run_date, json_analysis)

        markdown_report = generate_markdown_report(
            self.run_date, market_regime, sector_rankings, stocks_summary, quality_report_dict
        )
        self.store.save_daily_report_md(self.run_date, markdown_report)

        logger.info(f"=== DAILY PIPELINE COMPLETED SUCCESSFULLY FOR {self.run_date} ===")


def main():
    parser = argparse.ArgumentParser(description="Run Daily Indian Stock Market Data & Analysis Pipeline")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Run date (YYYY-MM-DD)")
    parser.add_argument("--mock", action="store_true", help="Use mock data provider for fast offline execution")
    args = parser.parse_args()

    pipeline = DailyPipeline(run_date=args.date, use_mock=args.mock)
    pipeline.run()


if __name__ == "__main__":
    main()
