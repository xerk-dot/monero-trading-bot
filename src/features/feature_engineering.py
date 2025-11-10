import pandas as pd
import numpy as np
from typing import List, Optional
from .technical_indicators import TechnicalIndicators
from .market_regime import MarketRegimeDetector


class FeatureEngineer:
    def __init__(self):
        self.technical_indicators = TechnicalIndicators()
        self.regime_detector = MarketRegimeDetector()
        self.feature_columns = []

    def engineer_features(
        self,
        df: pd.DataFrame,
        include_lagged: bool = True,
        include_multi_timeframe: bool = False
    ) -> pd.DataFrame:
        df = df.copy()

        df = TechnicalIndicators.add_all_indicators(df)

        df = self.regime_detector.get_regime_features(df)

        if include_lagged:
            df = self._add_lagged_features(df)

        if include_multi_timeframe:
            df = self._add_multi_timeframe_features(df)

        df = self._add_interaction_features(df)

        df = self._add_rolling_statistics(df)

        self.feature_columns = [col for col in df.columns if col not in
                               ['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        return df

    def _add_lagged_features(self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5, 10]) -> pd.DataFrame:
        df = df.copy()

        for lag in lags:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)

            if 'rsi' in df.columns:
                df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)

        return df

    def _add_multi_timeframe_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        for period in [4, 12, 24]:
            df[f'high_{period}h'] = df['high'].rolling(window=period).max()
            df[f'low_{period}h'] = df['low'].rolling(window=period).min()
            df[f'close_ma_{period}h'] = df['close'].rolling(window=period).mean()
            df[f'volume_sum_{period}h'] = df['volume'].rolling(window=period).sum()

        return df

    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if 'rsi' in df.columns and 'bb_pct' in df.columns:
            df['rsi_bb_interaction'] = df['rsi'] * df['bb_pct']

        if 'macd' in df.columns and 'adx' in df.columns:
            df['macd_adx_interaction'] = df['macd'] * df['adx']

        if 'volume_ratio' in df.columns and 'atr' in df.columns:
            df['volume_volatility_interaction'] = df['volume_ratio'] * df['atr']

        return df

    def _add_rolling_statistics(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        df = df.copy()

        for window in windows:
            df[f'returns_mean_{window}'] = df['returns'].rolling(window=window).mean()
            df[f'returns_std_{window}'] = df['returns'].rolling(window=window).std()
            df[f'returns_skew_{window}'] = df['returns'].rolling(window=window).skew()
            df[f'returns_kurt_{window}'] = df['returns'].rolling(window=window).kurt()

            df[f'volume_mean_{window}'] = df['volume'].rolling(window=window).mean()
            df[f'volume_std_{window}'] = df['volume'].rolling(window=window).std()

        return df

    def normalize_features(self, df: pd.DataFrame, method: str = 'zscore') -> pd.DataFrame:
        df = df.copy()
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        exclude_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        columns_to_normalize = [col for col in numeric_columns if col not in exclude_columns]

        if method == 'zscore':
            for col in columns_to_normalize:
                mean = df[col].mean()
                std = df[col].std()
                if std != 0:
                    df[f'{col}_normalized'] = (df[col] - mean) / std
                else:
                    df[f'{col}_normalized'] = 0

        elif method == 'minmax':
            for col in columns_to_normalize:
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val != min_val:
                    df[f'{col}_normalized'] = (df[col] - min_val) / (max_val - min_val)
                else:
                    df[f'{col}_normalized'] = 0

        return df

    def select_features(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        method: str = 'correlation',
        threshold: float = 0.1
    ) -> List[str]:
        if target_col is None:
            target_col = 'returns'

        if target_col not in df.columns:
            df[target_col] = df['close'].pct_change().shift(-1)

        numeric_columns = df.select_dtypes(include=[np.number]).columns
        feature_columns = [col for col in numeric_columns if col not in
                         ['timestamp', 'open', 'high', 'low', 'close', 'volume', target_col]]

        if method == 'correlation':
            correlations = df[feature_columns].corrwith(df[target_col]).abs()
            selected_features = correlations[correlations > threshold].index.tolist()

        elif method == 'variance':
            variances = df[feature_columns].var()
            threshold_var = variances.quantile(threshold)
            selected_features = variances[variances > threshold_var].index.tolist()

        else:
            selected_features = feature_columns

        return selected_features