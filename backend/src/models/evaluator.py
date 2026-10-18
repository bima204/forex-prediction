"""
Model Evaluation and Trading Metric Diagnostics.
Computes Precision, Recall, ROC-AUC, Expected Value (EV), and Brier Score.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
)


class ModelEvaluator:
    """
    Evaluates probabilistic model accuracy and financial expectancy.
    """

    @staticmethod
    def evaluate_predictions(
        y_true: pd.Series,
        y_prob: np.ndarray,
        threshold: float = 0.58,
        tp_pips: float = 40.0,
        sl_pips: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Calculates machine learning and financial performance indicators.
        """
        y_pred = (y_prob >= threshold).astype(int)

        # Standard ML Metrics
        auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
        brier = float(brier_score_loss(y_true, y_prob))

        # Precision on high-confidence signals
        total_signals = int(y_pred.sum())
        if total_signals > 0:
            precision = float(precision_score(y_true, y_pred, zero_division=0))
            recall = float(recall_score(y_true, y_pred, zero_division=0))
            f1 = float(f1_score(y_true, y_pred, zero_division=0))
            
            # Financial Expected Value per high-confidence trade
            # EV = (WinRate * TP) - ((1 - WinRate) * SL)
            expected_value_pips = (precision * tp_pips) - ((1 - precision) * sl_pips)
            profit_factor = (precision * tp_pips) / (((1 - precision) * sl_pips) + 1e-8)
        else:
            precision = 0.0
            recall = 0.0
            f1 = 0.0
            expected_value_pips = 0.0
            profit_factor = 0.0

        return {
            "roc_auc": round(auc, 4),
            "brier_score": round(brier, 4),
            "confidence_threshold": threshold,
            "total_trades_triggered": total_signals,
            "win_rate_precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1, 4),
            "expected_value_pips_per_trade": round(expected_value_pips, 2),
            "profit_factor": round(profit_factor, 2),
        }
