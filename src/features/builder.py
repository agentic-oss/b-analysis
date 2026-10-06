import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class FeatureBuilder:
    """
    Builds ML feature datasets with strict look-ahead bias prevention.

    Prevention of Leakage:
    - All features on date T are computed strictly using price and volume observations up to and including date T.
    - Future target variables (future_return_1d, 3d, 5d, 10d, 20d) are shifted backward (leading returns from date T to T+h)
      and stored in separate target columns explicitly designated for training supervision.
    """

    @staticmethod
    def build_stock_features(
        stock_symbol: str,
        stock_df: pd.DataFrame,
        nifty_df: pd.DataFrame,
        sector_df: Optional[pd.DataFrame] = None,
        regime_info: Optional[Dict[str, Any]] = None,
        sector_rank: Optional[int] = None,
        technical_score: int = 50,
        fundamental_score: int = 50,
        include_targets: bool = True
    ) -> pd.DataFrame:
        """
        Constructs standardized ML feature row(s) for a stock.
        """
        if stock_df.empty or len(stock_df) < 5:
            return pd.DataFrame()

        df = stock_df.copy().sort_values('date').reset_index(drop=True)

        features = pd.DataFrame()
        features['date'] = df['date']
        features['symbol'] = stock_symbol

        # Standard OHLCV features
        features['price_open'] = df['open']
        features['price_high'] = df['high']
        features['price_low'] = df['low']
        features['price_close'] = df['close']
        features['volume'] = df['volume']

        # Historical return features (past looking)
        features['return_1d'] = df['close'].pct_change(1)
        features['return_5d'] = df['close'].pct_change(5)
        features['return_20d'] = df['close'].pct_change(20)

        # Technical Indicators
        features['rsi_14'] = df.get('rsi_14', 50.0)
        features['macd'] = df.get('macd', 0.0)
        features['macd_signal'] = df.get('macd_signal', 0.0)
        features['atr'] = df.get('atr_14', 0.0)
        features['volatility_20d'] = df.get('volatility_20d', 0.0)

        features['sma_20'] = df.get('sma_20', df['close'])
        features['sma_50'] = df.get('sma_50', df['close'])
        features['sma_200'] = df.get('sma_200', df['close'])
        features['ema_20'] = df.get('ema_20', df['close'])
        features['ema_50'] = df.get('ema_50', df['close'])

        features['relative_volume'] = df.get('relative_volume', 1.0)
        features['distance_from_52w_high'] = df.get('dist_52w_high', 0.0)
        features['distance_from_52w_low'] = df.get('dist_52w_low', 0.0)

        # Market & Sector relative features
        if not nifty_df.empty and len(nifty_df) == len(df):
            features['market_return_1d'] = nifty_df['close'].pct_change(1)
            features['market_volatility'] = nifty_df.get('volatility_20d', 0.15)
        else:
            features['market_return_1d'] = 0.0
            features['market_volatility'] = 0.15

        if sector_df is not None and not sector_df.empty and len(sector_df) == len(df):
            features['sector_return_1d'] = sector_df['close'].pct_change(1)
        else:
            features['sector_return_1d'] = 0.0

        regime_str = regime_info.get('regime', 'Neutral') if regime_info else 'Neutral'
        breadth_val = regime_info.get('breadth', {}).get('pct_above_50dma', 50.0) if regime_info else 50.0

        features['breadth'] = breadth_val
        features['market_regime'] = regime_str
        features['sector_rank'] = sector_rank if sector_rank else 0
        features['technical_score'] = technical_score
        features['fundamental_score'] = fundamental_score

        # Future Targets (for supervised model training, shifted into the future relative to date T)
        if include_targets:
            for h in [1, 3, 5, 10, 20]:
                features[f'future_return_{h}d'] = (df['close'].shift(-h) - df['close']) / df['close']

        return features
