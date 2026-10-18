"""
Unified Feature Pipeline.
Orchestrates Market Regime Detection, Technical Feature Extraction, and Triple Barrier Labeling.
"""
from typing import Tuple, List, Optional
import pandas as pd
from .market_regime import MarketRegimeDetector
from .technical_features import TechnicalFeatureExtractor
from .labeling import TripleBarrierLabeler


class FeaturePipeline:
    """
    Transforms raw OHLCV DataFrame into a feature-rich, labeled dataset ready for Machine Learning.
    """

    def __init__(
        self,
        adx_threshold: float = 25.0,
        rsi_period: int = 14,
        pivot_window: int = 10,
        tp_mult: float = 2.0,
        sl_mult: float = 1.0,
        max_holding_bars: int = 24,
    ):
        self.regime_detector = MarketRegimeDetector(adx_threshold=adx_threshold)
        self.tech_extractor = TechnicalFeatureExtractor(rsi_period=rsi_period, pivot_window=pivot_window)
        self.labeler = TripleBarrierLabeler(atr_multiplier_tp=tp_mult, atr_multiplier_sl=sl_mult, max_holding_bars=max_holding_bars)

    def extract_features(self, df: pd.DataFrame, include_labels: bool = True, pip_value: float = 0.0001) -> pd.DataFrame:
        """
        Runs raw OHLCV through the full transformation pipeline.
        """
        # 1. Market Regime Features
        data = self.regime_detector.compute_regime_features(df)

        # 2. Technical & Price Action Features
        data = self.tech_extractor.compute_features(data)

        # 3. Triple Barrier Labeling (Only during training/historical data)
        if include_labels:
            data = self.labeler.apply_triple_barrier(data, pip_value=pip_value)

        # Drop initial warmup window where moving averages/RSI are NaN
        warmup_period = 50
        data = data.iloc[warmup_period:].copy()
        data.ffill(inplace=True)
        data.bfill(inplace=True)

        return data

    @staticmethod
    def get_feature_column_names(df: pd.DataFrame) -> List[str]:
        """
        Returns list of ML feature columns (excluding raw prices, metadata, and labels).
        """
        exclude_cols = {
            "open", "high", "low", "close", "volume",
            "target_buy", "target_sell", "target_signal", "realized_pips",
            "swing_high", "swing_low",
        }
        return [c for c in df.columns if c not in exclude_cols]

    def prepare_train_test_split(
        self,
        df: pd.DataFrame,
        target_col: str = "target_buy",
        test_size: float = 0.2,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Time-series split (strictly chronological to prevent future lookahead bias).
        """
        feature_cols = self.get_feature_column_names(df)
        split_idx = int(len(df) * (1 - test_size))

        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        X_test = test_df[feature_cols]
        y_test = test_df[target_col]

        return X_train, X_test, y_train, y_test
