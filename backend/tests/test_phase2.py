"""
Validation test for Phase 2: Feature Engineering, Market Regime, and Triple Barrier Labeling.
"""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.data_loader.data_manager import DataManager
from src.features.market_regime import MarketRegimeDetector
from src.features.technical_features import TechnicalFeatureExtractor
from src.features.labeling import TripleBarrierLabeler
from src.features.feature_pipeline import FeaturePipeline


def test_phase2():
    print("=== Testing Phase 2: Market Detection & Feature Engineering ===")
    dm = DataManager()
    
    # 1. Load cached EURUSD
    print("\n1. Loading cached EURUSD data...")
    df = dm.get_ohlcv("EURUSD", timeframe="1h")
    assert not df.empty, "Data should not be empty!"
    print(f"   [PASS] Loaded {len(df)} candles.")

    # 2. Test Market Regime Detector
    print("\n2. Testing Market Regime Detector...")
    regime_detector = MarketRegimeDetector()
    df_regime = regime_detector.compute_regime_features(df)
    assert "adx_14" in df_regime.columns
    assert "regime_trend" in df_regime.columns
    assert "regime_volatility" in df_regime.columns
    assert "is_tradeable_session" in df_regime.columns
    
    current_regime = regime_detector.get_current_regime_summary(df_regime)
    print(f"   [PASS] Current Regime: {current_regime['trend_state']}, Volatility: {current_regime['volatility_state']}")
    print(f"          ADX: {current_regime['adx_strength']:.1f}, Active Session: {current_regime['session']}")

    # 3. Test Technical & SMC Features
    print("\n3. Testing Technical & Price Action Features...")
    tech_extractor = TechnicalFeatureExtractor()
    df_tech = tech_extractor.compute_features(df_regime)
    assert "rsi_14" in df_tech.columns
    assert "macd_hist" in df_tech.columns
    assert "is_bullish_fvg" in df_tech.columns
    assert "dist_to_swing_high" in df_tech.columns
    fvg_count = df_tech["is_bullish_fvg"].sum() + df_tech["is_bearish_fvg"].sum()
    print(f"   [PASS] Technical indicators & Fair Value Gaps extracted (Total FVGs detected: {fvg_count}).")

    # 4. Test Triple Barrier Labeling
    print("\n4. Testing Triple Barrier Labeling...")
    labeler = TripleBarrierLabeler(atr_multiplier_tp=2.0, atr_multiplier_sl=1.0, max_holding_bars=24)
    df_labeled = labeler.apply_triple_barrier(df_tech)
    assert "target_buy" in df_labeled.columns
    assert "target_sell" in df_labeled.columns
    assert "target_signal" in df_labeled.columns
    buy_signals = (df_labeled["target_signal"] == 1).sum()
    sell_signals = (df_labeled["target_signal"] == -1).sum()
    print(f"   [PASS] Triple Barrier Labels created. BUY targets: {buy_signals}, SELL targets: {sell_signals}.")

    # 5. Test Unified Feature Pipeline & ML Data Split
    print("\n5. Testing End-to-End Feature Pipeline & Train/Test Split...")
    pipeline = FeaturePipeline()
    processed_df = pipeline.extract_features(df, include_labels=True)
    feature_cols = pipeline.get_feature_column_names(processed_df)
    
    assert len(feature_cols) >= 20, f"Expected at least 20 features, got {len(feature_cols)}"
    assert not processed_df[feature_cols].isnull().any().any(), "Features should not contain any NaN values!"

    X_train, X_test, y_train, y_test = pipeline.prepare_train_test_split(processed_df, target_col="target_buy")
    print(f"   [PASS] Total ML Features generated: {len(feature_cols)}")
    print(f"   [PASS] X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")
    print(f"   [PASS] Training label distribution: {y_train.value_counts().to_dict()}")

    print("\n[SUCCESS] ALL PHASE 2 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_phase2()
