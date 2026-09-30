import pandas as pd
import numpy as np

class FeatureEngine:
    """
    Builds tabular ML features with strictly no look-ahead bias.
    Features for row T use only data up to date T.
    Future target columns (future_return_1d ... future_return_20d) are constructed separately for offline ML training.
    """

    @staticmethod
    def build_feature_set(df: pd.DataFrame, market_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Calculates normalized features on stock history DataFrame.
        `df` must already have technical indicators calculated.
        """
        if df.empty or len(df) < 5:
            return pd.DataFrame()

        f = pd.DataFrame()
        f['symbol'] = df['symbol']
        f['date'] = df['date']
        f['price_open'] = df['open']
        f['price_high'] = df['high']
        f['price_low'] = df['low']
        f['price_close'] = df['close']
        f['volume'] = df['volume']

        f['return_1d'] = df['daily_return']
        f['return_5d'] = df['close'].pct_change(5)
        f['return_20d'] = df['close'].pct_change(20)

        f['rsi_14'] = df.get('rsi_14', 50.0)
        f['macd'] = df.get('macd', 0.0)
        f['macd_signal'] = df.get('macd_signal', 0.0)
        f['atr'] = df.get('atr_14', 0.0)
        f['volatility_20d'] = df.get('volatility_20d', 0.0)

        f['sma_20'] = df.get('sma_20', df['close'])
        f['sma_50'] = df.get('sma_50', df['close'])
        f['sma_200'] = df.get('sma_200', df['close'])
        f['ema_20'] = df.get('ema_20', df['close'])
        f['ema_50'] = df.get('ema_50', df['close'])

        f['relative_volume'] = df.get('relative_volume', 1.0)
        f['distance_from_52w_high'] = df.get('dist_52w_high', 0.0)
        f['distance_from_52w_low'] = df.get('dist_52w_low', 0.0)

        # Market-relative features if market_df provided
        if market_df is not None and not market_df.empty and 'date' in market_df.columns:
            m_merged = pd.merge(f[['date']], market_df[['date', 'daily_return', 'volatility_20d']], on='date', how='left')
            f['market_return_1d'] = m_merged['daily_return'].fillna(0.0)
            f['market_volatility'] = m_merged['volatility_20d'].fillna(0.15)
        else:
            f['market_return_1d'] = 0.0
            f['market_volatility'] = 0.15

        # Future Target columns (Look-Ahead ONLY for supervised training datasets)
        # Note: Targets shift backwards in time (shift(-N))
        f['future_return_1d'] = (df['close'].shift(-1) - df['close']) / df['close']
        f['future_return_3d'] = (df['close'].shift(-3) - df['close']) / df['close']
        f['future_return_5d'] = (df['close'].shift(-5) - df['close']) / df['close']
        f['future_return_10d'] = (df['close'].shift(-10) - df['close']) / df['close']
        f['future_return_20d'] = (df['close'].shift(-20) - df['close']) / df['close']

        return f
