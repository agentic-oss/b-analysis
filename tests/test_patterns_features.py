import pandas as pd
import numpy as np
import pytest
from src.indicators.technical import TechnicalAnalysisEngine
from src.patterns.historical_analogue import HistoricalAnalogueEngine
from src.features.engineer import FeatureEngineer

def test_historical_analogue_engine():
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=120).strftime('%Y-%m-%d')
    closes = 100 + np.cumsum(np.random.randn(120))

    df = pd.DataFrame({
        'date': dates,
        'symbol': ['RELIANCE'] * 120,
        'open': closes,
        'high': closes + 1,
        'low': closes - 1,
        'close': closes,
        'volume': [10000] * 120
    })

    df_calc = TechnicalAnalysisEngine.calculate_indicators(df)
    res = HistoricalAnalogueEngine.find_analogues_and_forward_returns(df_calc)

    assert res['historical_matches_count'] > 0
    assert '1d' in res['horizons']
    assert 'win_probability' in res['horizons']['1d']

def test_feature_engineer_anti_lookahead():
    dates = pd.date_range('2025-01-01', periods=20).strftime('%Y-%m-%d')
    closes = list(range(100, 120))

    df = pd.DataFrame({
        'date': dates,
        'symbol': ['TCS'] * 20,
        'open': closes,
        'high': [c + 1 for c in closes],
        'low': [c - 1 for c in closes],
        'close': closes,
        'volume': [5000] * 20
    })

    df_feat = FeatureEngineer.create_feature_dataset(df)
    assert not df_feat.empty

    # Check that feature at date T=0 uses close=100 and target_future_return_1d is (101-100)/100 = 0.01
    assert df_feat.iloc[0]['price_close'] == 100
    assert round(df_feat.iloc[0]['target_future_return_1d'], 4) == 0.01
    assert df_feat.iloc[0]['target_direction_1d'] == 1
    # Last row target should be NaN because future price isn't available
    assert pd.isnull(df_feat.iloc[-1]['target_future_return_1d'])
