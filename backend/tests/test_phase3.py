"""
Validation test for Phase 3: Autonomous Machine Learning Training Engine.
"""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.data_loader.data_manager import DataManager
from src.features.feature_pipeline import FeaturePipeline
from src.models.model_trainer import ForexMLModel
from src.models.evaluator import ModelEvaluator


def test_phase3():
    print("=== Testing Phase 3: Learning Engine (LightGBM & Walk-Forward CV) ===")
    dm = DataManager()
    
    # 1. Load data & extract features
    print("\n1. Preparing dataset for EURUSD...")
    df = dm.get_ohlcv("EURUSD", timeframe="1h")
    pipeline = FeaturePipeline()
    processed_df = pipeline.extract_features(df, include_labels=True)
    feature_cols = pipeline.get_feature_column_names(processed_df)
    print(f"   [PASS] Processed {len(processed_df)} samples with {len(feature_cols)} features.")

    # 2. Split train & test sets (80% train, 20% out-of-sample test)
    X_train, X_test, y_train, y_test = pipeline.prepare_train_test_split(processed_df, target_col="target_buy", test_size=0.2)
    train_df = processed_df.iloc[:len(X_train)]
    test_df = processed_df.iloc[len(X_train):]
    print(f"   [PASS] Train size: {len(train_df)}, Test size: {len(test_df)}")

    # 3. Train ML Model
    print("\n2. Training LightGBM Dual Model with Purged Walk-Forward CV...")
    model = ForexMLModel(symbol="EURUSD", timeframe="1h", confidence_threshold=0.55)
    metadata = model.train(train_df, feature_cols=feature_cols, n_splits=3)
    print(f"   [PASS] Model trained successfully!")
    print(f"          Walk-Forward AUC (Buy): {metadata['walk_forward_cv_auc_buy']:.4f}")
    print(f"          Walk-Forward AUC (Sell): {metadata['walk_forward_cv_auc_sell']:.4f}")

    # 4. Check Top Features
    print("\n3. Top Predictive Features:")
    for rank, f in enumerate(metadata["top_features"][:5], 1):
        print(f"   {rank}. {f['feature']} (Importance: {f['importance']:.1f})")

    # 5. Evaluate on Out-Of-Sample Test Set
    print("\n4. Evaluating Model on Out-Of-Sample Test Set...")
    test_features = test_df[feature_cols]
    buy_probs = model.model_buy.predict_proba(test_features)[:, 1]
    metrics = ModelEvaluator.evaluate_predictions(test_df["target_buy"], buy_probs, threshold=0.55, tp_pips=40.0, sl_pips=20.0)
    print(f"   [PASS] Out-Of-Sample ROC-AUC: {metrics['roc_auc']}")
    print(f"          Triggered Trades: {metrics['total_trades_triggered']}")
    print(f"          Win Rate (Precision): {metrics['win_rate_precision']}%")
    print(f"          Expected Value (EV): {metrics['expected_value_pips_per_trade']} pips/trade")
    print(f"          Profit Factor: {metrics['profit_factor']}")

    # 6. Test Real-Time Single Signal Prediction
    print("\n5. Testing Live Signal Generation on Current Candle...")
    latest_candle = processed_df.iloc[-1]
    current_price = float(latest_candle["close"])
    current_atr = float(latest_candle.get("atr_14", 0.0015))
    signal = model.predict_signal(latest_candle, current_price=current_price, current_atr=current_atr)

    print(f"   [PASS] Signal Generated for {signal['symbol']}:")
    print(f"          Action: {signal['action']} (Confidence: {signal['confidence']:.1%})")
    print(f"          P(BUY): {signal['p_buy']:.1%}, P(SELL): {signal['p_sell']:.1%}")
    print(f"          Take Profit: {signal['take_profit']:.5f} ({signal['tp_pips']:.1f} pips)")
    print(f"          Stop Loss:   {signal['stop_loss']:.5f} ({signal['sl_pips']:.1f} pips)")
    print(f"          Reason:      {signal['reason']}")

    # 7. Test Model Persistence (Load from disk)
    print("\n6. Testing Model Persistence (Save & Load)...")
    loaded_model = ForexMLModel(symbol="EURUSD", timeframe="1h")
    success = loaded_model.load()
    assert success, "Model file should be loaded successfully from disk!"
    assert len(loaded_model.feature_names) == len(feature_cols)
    print(f"   [PASS] Model loaded from disk with {len(loaded_model.feature_names)} features.")

    print("\n[SUCCESS] ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_phase3()
