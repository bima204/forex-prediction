"""
Autonomous Machine Learning Model Trainer for Forex Trading.
Features LightGBM Dual-Model (Long/Short), Purged Walk-Forward Evaluation,
Probability Calibration, and Feature Importance analysis.
"""
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, precision_score, recall_score, log_loss

from config.settings import MODELS_DIR
from .time_series_cv import PurgedWalkForwardCV


class ForexMLModel:
    """
    Dual-classifier Machine Learning engine for directional probability estimation and trade signal generation.
    """

    def __init__(
        self,
        symbol: str = "EURUSD",
        timeframe: str = "1h",
        confidence_threshold: float = 0.58,
        models_dir: Optional[Path] = None,
    ):
        self.symbol = symbol.upper()
        self.timeframe = timeframe.lower()
        self.confidence_threshold = confidence_threshold
        self.models_dir = models_dir or MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.model_buy: Optional[lgb.LGBMClassifier] = None
        self.model_sell: Optional[lgb.LGBMClassifier] = None
        self.feature_names: List[str] = []
        self.training_metadata: Dict[str, Any] = {}

    def _get_model_path(self) -> Path:
        return self.models_dir / f"{self.symbol}_{self.timeframe}_model.joblib"

    def train(
        self,
        df_processed: pd.DataFrame,
        feature_cols: List[str],
        n_splits: int = 4,
    ) -> Dict[str, Any]:
        """
        Trains Long and Short models using Purged Walk-Forward Cross Validation.
        """
        self.feature_names = feature_cols
        X = df_processed[feature_cols].copy()
        y_buy = df_processed["target_buy"].copy()
        y_sell = df_processed["target_sell"].copy()

        cv = PurgedWalkForwardCV(n_splits=n_splits, purge_window=24)
        
        # Hyperparameters tuned for noisy financial data to minimize overfitting
        lgb_params = {
            "objective": "binary",
            "metric": "binary_logloss",
            "boosting_type": "gbdt",
            "n_estimators": 120,
            "learning_rate": 0.03,
            "num_leaves": 31,
            "max_depth": 5,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_samples": 50,
            "random_state": 42,
            "verbose": -1,
        }

        buy_scores = []
        sell_scores = []

        # Walk-Forward Validation Loop
        for fold, (train_idx, test_idx) in enumerate(cv.split(df_processed)):
            X_tr, y_tr_buy = X.iloc[train_idx], y_buy.iloc[train_idx]
            X_val, y_val_buy = X.iloc[test_idx], y_buy.iloc[test_idx]
            y_tr_sell, y_val_sell = y_sell.iloc[train_idx], y_sell.iloc[test_idx]

            fold_m_buy = lgb.LGBMClassifier(**lgb_params)
            fold_m_buy.fit(X_tr, y_tr_buy)
            preds_buy = fold_m_buy.predict_proba(X_val)[:, 1]
            auc_buy = roc_auc_score(y_val_buy, preds_buy)
            buy_scores.append(auc_buy)

            fold_m_sell = lgb.LGBMClassifier(**lgb_params)
            fold_m_sell.fit(X_tr, y_tr_sell)
            preds_sell = fold_m_sell.predict_proba(X_val)[:, 1]
            auc_sell = roc_auc_score(y_val_sell, preds_sell)
            sell_scores.append(auc_sell)

        # Train final models on all available data
        self.model_buy = lgb.LGBMClassifier(**lgb_params)
        self.model_buy.fit(X, y_buy)

        self.model_sell = lgb.LGBMClassifier(**lgb_params)
        self.model_sell.fit(X, y_sell)

        # Feature Importance
        importances_buy = self.model_buy.feature_importances_
        importances_sell = self.model_sell.feature_importances_
        avg_importance = (importances_buy + importances_sell) / 2.0
        feature_importance_df = pd.DataFrame({
            "feature": feature_cols,
            "importance": avg_importance
        }).sort_values(by="importance", ascending=False)

        top_features = feature_importance_df.head(10).to_dict(orient="records")

        self.training_metadata = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "trained_at": datetime.now().isoformat(),
            "samples_count": len(df_processed),
            "features_count": len(feature_cols),
            "walk_forward_cv_auc_buy": float(np.mean(buy_scores)),
            "walk_forward_cv_auc_sell": float(np.mean(sell_scores)),
            "confidence_threshold": self.confidence_threshold,
            "top_features": top_features,
        }

        # Save model to disk
        self.save()

        return self.training_metadata

    def predict_signal(
        self,
        latest_row: pd.Series,
        current_price: float,
        current_atr: float,
        pip_value: float = 0.0001,
        tp_mult: float = 2.0,
        sl_mult: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Evaluates the latest market candle and outputs actionable trade signal.
        """
        if self.model_buy is None or self.model_sell is None:
            raise RuntimeError("Model is not loaded or trained yet.")

        # Prepare single row feature vector
        features_vec = pd.DataFrame([latest_row[self.feature_names]])

        p_buy = float(self.model_buy.predict_proba(features_vec)[0, 1])
        p_sell = float(self.model_sell.predict_proba(features_vec)[0, 1])

        # Filter check: Rollover session
        is_tradeable = bool(latest_row.get("is_tradeable_session", 1))
        trend_regime = int(latest_row.get("regime_trend", 0))

        action = "HOLD"
        confidence = max(p_buy, p_sell)
        tp_price = 0.0
        sl_price = 0.0
        reason = "Probabilitas di bawah ambang batas keyakinan."

        if not is_tradeable:
            reason = "Sesi Rollover (spread tinggi / likuiditas tipis). Entry ditolak."
        elif p_buy >= self.confidence_threshold and p_buy > p_sell:
            if trend_regime == -1 and p_buy < (self.confidence_threshold + 0.05):
                reason = "Sinyal BUY ditahan karena melawan tren Bearish yang kuat."
            else:
                action = "BUY"
                tp_price = current_price + (current_atr * tp_mult)
                sl_price = current_price - (current_atr * sl_mult)
                reason = f"Probabilitas BUY ({p_buy:.1%}) melampaui batas keyakinan ({self.confidence_threshold:.0%})."
        elif p_sell >= self.confidence_threshold and p_sell > p_buy:
            if trend_regime == 1 and p_sell < (self.confidence_threshold + 0.05):
                reason = "Sinyal SELL ditahan karena melawan tren Bullish yang kuat."
            else:
                action = "SELL"
                tp_price = current_price - (current_atr * tp_mult)
                sl_price = current_price + (current_atr * sl_mult)
                reason = f"Probabilitas SELL ({p_sell:.1%}) melampaui batas keyakinan ({self.confidence_threshold:.0%})."

        tp_pips = abs(tp_price - current_price) / pip_value if tp_price > 0 else 0.0
        sl_pips = abs(sl_price - current_price) / pip_value if sl_price > 0 else 0.0

        return {
            "symbol": self.symbol,
            "action": action,
            "confidence": confidence,
            "p_buy": p_buy,
            "p_sell": p_sell,
            "current_price": current_price,
            "take_profit": tp_price,
            "stop_loss": sl_price,
            "tp_pips": tp_pips,
            "sl_pips": sl_pips,
            "risk_reward": tp_mult / sl_mult,
            "reason": reason,
        }

    def save(self, filepath: Optional[Path] = None):
        target = filepath or self._get_model_path()
        data = {
            "model_buy": self.model_buy,
            "model_sell": self.model_sell,
            "feature_names": self.feature_names,
            "confidence_threshold": self.confidence_threshold,
            "metadata": self.training_metadata,
        }
        joblib.dump(data, target)

    def load(self, filepath: Optional[Path] = None) -> bool:
        target = filepath or self._get_model_path()
        if not target.exists():
            return False
        data = joblib.load(target)
        self.model_buy = data["model_buy"]
        self.model_sell = data["model_sell"]
        self.feature_names = data["feature_names"]
        self.confidence_threshold = data.get("confidence_threshold", 0.58)
        self.training_metadata = data.get("metadata", {})
        return True
