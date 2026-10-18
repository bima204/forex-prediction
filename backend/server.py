"""
FastAPI Backend Server for Forex Machine Learning Trading System.
Provides REST and WebSocket endpoints for market data, AI predictions,
backtest simulations, and paper trading portfolio management.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure root dir is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import DEFAULT_PAIRS, SUPPORTED_TIMEFRAMES
from src.data_loader.data_manager import DataManager
from src.features.feature_pipeline import FeaturePipeline
from src.features.market_regime import MarketRegimeDetector
from src.models.model_trainer import ForexMLModel
from src.simulation.backtester import Backtester
from src.simulation.paper_trader import PaperTrader
from src.simulation.signal_manager import SignalLockManager, TRADING_STYLES
from src.ui.ai_advisor import TradingAdvisor

app = FastAPI(
    title="Forex AI Trade Engine API",
    description="Backend API powering AI Forex Prediction & Paper Trading Dashboard",
    version="1.0.0"
)

# Enable CORS for React Frontend (typically localhost:5173 for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_manager = DataManager()
paper_trader = PaperTrader()
signal_manager = SignalLockManager()
ai_advisor = TradingAdvisor()

# --- Pydantic Request Models ---
class OrderRequest(BaseModel):
    pair: str
    action: str  # BUY or SELL
    lots: float = 0.1
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: Optional[str] = "Manual Entry"

class BacktestRequest(BaseModel):
    pair: str = "EURUSD"
    timeframe: str = "1h"
    initial_balance: float = 10000.0
    risk_pct: float = 1.0


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/pairs")
def get_pairs():
    """Returns available currency pairs, timeframes, and trading styles."""
    pairs_list = []
    for code, info in DEFAULT_PAIRS.items():
        pairs_list.append({
            "symbol": code,
            "name": info["name"],
            "pip_decimal": info["pip_decimal"],
            "pip_value": info["pip_value"]
        })
    return {
        "pairs": pairs_list,
        "timeframes": SUPPORTED_TIMEFRAMES,
        "trading_styles": TRADING_STYLES
    }


@app.get("/api/market/{pair}")
def get_market_data(
    pair: str,
    timeframe: str = Query("1h", pattern="^(5m|15m|1h|4h|1d)$"),
    limit: int = 300
):
    """
    Returns OHLCV candle data formatted for Lightweight Charts / TradingView.
    """
    pair = pair.upper().strip()
    if pair not in DEFAULT_PAIRS:
        raise HTTPException(status_code=404, detail=f"Pair {pair} is not supported.")

    df = data_manager.get_data(pair=pair, timeframe=timeframe, use_cache=True)
    if df is None or df.empty:
        raise HTTPException(status_code=500, detail=f"Unable to fetch data for {pair}")

    # Format for charting libraries (time, open, high, low, close, volume)
    recent_df = df.tail(limit).copy()
    candles = []
    
    for idx, row in recent_df.iterrows():
        # idx is pd.Timestamp
        timestamp = int(idx.timestamp())
        candles.append({
            "time": timestamp,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0))
        })

    latest_price = float(df["close"].iloc[-1])
    prev_price = float(df["close"].iloc[-2]) if len(df) > 1 else latest_price
    change = latest_price - prev_price
    change_pct = (change / prev_price) * 100 if prev_price > 0 else 0

    return {
        "pair": pair,
        "timeframe": timeframe,
        "latest_price": latest_price,
        "price_change": round(change, 5),
        "price_change_pct": round(change_pct, 3),
        "candles": candles
    }


@app.get("/api/analysis/{pair}")
def get_market_analysis(
    pair: str,
    timeframe: str = Query("1h", pattern="^(5m|15m|1h|4h|1d)$"),
    style: str = Query("daytrading")
):
    """
    Computes technical features, Market Regime, ML Predictions, and Trading Signals.
    """
    pair = pair.upper().strip()
    if pair not in DEFAULT_PAIRS:
        raise HTTPException(status_code=404, detail=f"Pair {pair} is not supported.")

    df = data_manager.get_data(pair=pair, timeframe=timeframe, use_cache=True)
    if df is None or df.empty or len(df) < 50:
        raise HTTPException(status_code=500, detail="Insufficient data for ML pipeline")

    # 1. Feature Extraction
    pipeline = FeaturePipeline()
    feat_df = pipeline.extract_features(df, include_labels=False)

    # 2. Market Regime Detection
    regime_detector = MarketRegimeDetector()
    regime_summary = regime_detector.get_current_regime_summary(feat_df)

    # 3. Model Inference
    model = ForexMLModel()
    model_loaded = model.load_model(pair, timeframe)
    
    if not model_loaded:
        # Auto-train lightweight model if not yet cached
        train_df = pipeline.extract_features(df, include_labels=True)
        model.train(train_df, pair=pair, timeframe=timeframe)

    pred_res = model.predict(feat_df.tail(1))

    # Format Prediction Result
    signal = pred_res.get("signal", "HOLD")
    prob_buy = float(pred_res.get("prob_buy", 0.5))
    prob_sell = float(pred_res.get("prob_sell", 0.5))
    confidence = float(pred_res.get("confidence", 0.5))

    # Style lock-in & SL/TP Calculations
    curr_price = float(df["close"].iloc[-1])
    atr = float(feat_df["atr_14"].iloc[-1]) if "atr_14" in feat_df.columns else curr_price * 0.002
    
    style_cfg = TRADING_STYLES.get(style, TRADING_STYLES["daytrading"])
    sl_distance = atr * style_cfg["sl_mult"]
    tp_distance = atr * style_cfg["tp_mult"]

    if signal == "BUY":
        stop_loss = curr_price - sl_distance
        take_profit = curr_price + tp_distance
    elif signal == "SELL":
        stop_loss = curr_price + sl_distance
        take_profit = curr_price - tp_distance
    else:
        stop_loss = None
        take_profit = None

    # Locked Signal Check
    active_locked = signal_manager.get_active_signal(pair, timeframe, style)
    if active_locked:
        # Update current price in locked signal
        signal_manager.update_price_and_check(pair, timeframe, style, curr_price)

    # AI Advisory insight
    advisor_insight = ai_advisor.generate_recommendation(
        pair=pair,
        regime=regime_summary,
        ml_signal=signal,
        confidence=confidence,
        current_price=curr_price,
        timeframe=timeframe
    )

    # Key Technical Indicator Values for Dashboard
    indicators = {
        "rsi": round(float(feat_df["rsi_14"].iloc[-1]), 2) if "rsi_14" in feat_df.columns else None,
        "macd": round(float(feat_df["macd"].iloc[-1]), 5) if "macd" in feat_df.columns else None,
        "macd_signal": round(float(feat_df["macd_signal"].iloc[-1]), 5) if "macd_signal" in feat_df.columns else None,
        "adx": round(float(feat_df["adx_14"].iloc[-1]), 2) if "adx_14" in feat_df.columns else None,
        "atr": round(atr, 5)
    }

    return {
        "pair": pair,
        "timeframe": timeframe,
        "style": style,
        "current_price": curr_price,
        "signal": signal,
        "confidence": round(confidence * 100, 1),
        "prob_buy": round(prob_buy * 100, 1),
        "prob_sell": round(prob_sell * 100, 1),
        "stop_loss": round(stop_loss, 5) if stop_loss else None,
        "take_profit": round(take_profit, 5) if take_profit else None,
        "risk_reward_ratio": round(tp_distance / sl_distance, 2) if sl_distance > 0 else 2.0,
        "regime": regime_summary,
        "indicators": indicators,
        "advisor_insight": advisor_insight,
        "locked_signal": active_locked
    }


@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    """Executes backtesting simulation and returns performance statistics."""
    df = data_manager.get_data(pair=req.pair, timeframe=req.timeframe, use_cache=True)
    if df is None or len(df) < 100:
        raise HTTPException(status_code=400, detail="Data insufficient for backtest")

    pipeline = FeaturePipeline()
    feat_df = pipeline.extract_features(df, include_labels=True)
    
    model = ForexMLModel()
    if not model.load_model(req.pair, req.timeframe):
        model.train(feat_df, pair=req.pair, timeframe=req.timeframe)

    backtester = Backtester(initial_balance=req.initial_balance, risk_pct=req.risk_pct)
    results = backtester.run_simulation(df=feat_df, model=model, pair=req.pair)

    return results


@app.get("/api/papertrade/account")
def get_paper_account():
    """Returns the paper trading account state (balance, equity, positions)."""
    paper_trader.load_state()
    return {
        "balance": paper_trader.balance,
        "open_positions": paper_trader.open_positions,
        "closed_positions": paper_trader.closed_positions[-50:],
        "total_trades": len(paper_trader.closed_positions)
    }


@app.post("/api/papertrade/order")
def execute_paper_order(order: OrderRequest):
    """Executes a simulated buy or sell order in paper trading."""
    pair = order.pair.upper()
    df = data_manager.get_data(pair=pair, timeframe="1h", use_cache=True)
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Cannot fetch live price for order execution.")

    curr_price = float(df["close"].iloc[-1])
    pos = paper_trader.open_order(
        pair=pair,
        order_type=order.action.upper(),
        entry_price=curr_price,
        lots=order.lots,
        stop_loss=order.stop_loss,
        take_profit=order.take_profit,
        strategy=order.strategy
    )
    return {"status": "success", "position": pos}


@app.post("/api/papertrade/close/{ticket}")
def close_paper_order(ticket: int):
    """Closes an active paper trade position."""
    paper_trader.load_state()
    target_pos = None
    for p in paper_trader.open_positions:
        if p.get("ticket_id") == ticket or p.get("ticket") == ticket:
            target_pos = p
            break

    if not target_pos:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket} not found in open positions.")

    pair = target_pos["symbol"]
    df = data_manager.get_data(pair=pair, timeframe="1h", use_cache=True)
    curr_price = float(df["close"].iloc[-1]) if df is not None and not df.empty else target_pos["entry_price"]

    closed_pos = paper_trader.close_order(ticket_id=ticket, exit_price=curr_price, reason="Manual User Close")
    return {"status": "closed", "trade": closed_pos}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
