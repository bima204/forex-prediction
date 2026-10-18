"""
Validation test for Phase 4: Autonomous Simulation Engine & Risk Management.
"""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from src.data_loader.data_manager import DataManager
from src.features.feature_pipeline import FeaturePipeline
from src.models.model_trainer import ForexMLModel
from src.simulation.risk_manager import RiskManager
from src.simulation.backtester import Backtester
from src.simulation.paper_trader import PaperTrader


def test_phase4():
    print("=== Testing Phase 4: Simulation Engine & Risk Management ===")

    # 1. Test Risk Manager Dynamic Lot Sizing
    print("\n1. Testing Risk Manager & Lot Sizing...")
    rm = RiskManager(risk_per_trade_pct=1.0, spread_pips=1.5, slippage_pips=0.5)
    lot_size = rm.calculate_lot_size(account_balance=10000.0, sl_pips=25.0, pip_value=0.0001)
    # Risk 1% of 10,000 = $100. 25 pips * $10/pip = $250/lot. Lot = 100 / 250 = 0.40 lots.
    assert lot_size == 0.40, f"Expected 0.40 lots, got {lot_size}"
    print(f"   [PASS] Calculated Lot Size: {lot_size} lots for $10,000 capital with 25 pips SL (1% risk).")

    # Test Execution Cost
    ask_price = rm.apply_execution_costs(1.1000, "BUY")
    bid_price = rm.apply_execution_costs(1.1000, "SELL")
    assert ask_price > 1.1000 and bid_price < 1.1000
    print(f"   [PASS] Friction Applied -> Raw: 1.1000 | Ask: {ask_price:.5f} | Bid: {bid_price:.5f}")

    # 2. Run Event-Driven Backtest on Out-of-Sample Market Data
    print("\n2. Loading Model & Running Backtest Simulation on EURUSD...")
    dm = DataManager()
    df = dm.get_ohlcv("EURUSD", timeframe="1h")
    
    pipeline = FeaturePipeline()
    processed_df = pipeline.extract_features(df, include_labels=False)
    feature_cols = pipeline.get_feature_column_names(processed_df)

    # Use out-of-sample partition (last 2,500 candles)
    test_slice = processed_df.tail(2500).copy()
    raw_slice = df.loc[test_slice.index].copy()

    model = ForexMLModel(symbol="EURUSD", timeframe="1h")
    assert model.load(), "Model should be pre-trained from Phase 3!"

    # Generate signals for test slice
    print(f"   Generating AI predictions for {len(test_slice)} candles...")
    signal_records = []
    pip_val = 0.0001
    
    for _, row in test_slice.iterrows():
        c_price = float(row["close"])
        c_atr = float(row.get("atr_14", 0.0015))
        sig = model.predict_signal(row, current_price=c_price, current_atr=c_atr, pip_value=pip_val)
        signal_records.append(sig)

    signals_df = pd.DataFrame(signal_records, index=test_slice.index)

    # Run Backtest
    backtester = Backtester(initial_capital=10000.0, risk_manager=rm, use_trailing_stop=True)
    report = backtester.run_simulation(raw_slice, signals_df, symbol="EURUSD")

    print(f"\n   === HASIL SIMULASI MANDIRI EURUSD ===")
    print(f"   Modal Awal:          ${report['initial_capital']:,.2f}")
    print(f"   Ekuitas Akhir:       ${report['final_equity']:,.2f}")
    print(f"   Total Net Profit:    ${report['net_profit']:,.2f} ({report['net_profit_pct']:+.2f}%)")
    print(f"   Total Trade Eksekusi:{report['closed_trades_count']}")
    print(f"   Win Rate:            {report['win_rate']}%")
    print(f"   Profit Factor:       {report['profit_factor']}")
    print(f"   Risk:Reward Rill:    1:{report['risk_reward_realized']}")
    print(f"   Max Drawdown:        {report['max_drawdown_pct']}%")
    print(f"   Sharpe Ratio:        {report['sharpe_ratio']}")

    assert report["closed_trades_count"] > 0, "Backtest should execute trades!"
    assert report["max_drawdown_pct"] < 15.0, f"Max DD {report['max_drawdown_pct']}% exceeds 15% benchmark!"
    print(f"   [PASS] Max Drawdown ({report['max_drawdown_pct']}%) di bawah batas aman (< 15%)!")

    # 3. Test Paper Trader Forward Testing Engine
    print("\n3. Testing Paper Trader State & Order Execution...")
    paper = PaperTrader()
    paper.reset_account(10000.0)

    # Simulate candle processing with BUY signal
    sample_candle = {
        "close": 1.1250,
        "high": 1.1270,
        "low": 1.1240,
        "time": "2026-10-16T18:00:00",
    }
    sample_sig = {
        "action": "BUY",
        "stop_loss": 1.1220,
        "take_profit": 1.1310,
    }

    res1 = paper.process_candle("EURUSD", sample_candle, signal=sample_sig)
    assert res1["open_count"] == 1, "Should have 1 open position"
    print(f"   [PASS] Paper position opened: {res1['new_trade']['direction']} {res1['new_trade']['lot_size']} lots at {res1['new_trade']['entry_price']:.5f}")

    # Simulate subsequent candle that hits TP
    tp_candle = {
        "close": 1.1320,
        "high": 1.1325,
        "low": 1.1245,
        "time": "2026-10-16T19:00:00",
    }
    res2 = paper.process_candle("EURUSD", tp_candle)
    assert res2["open_count"] == 0, "Position should be closed by TP"
    assert len(res2["closed_trades"]) == 1
    print(f"   [PASS] Paper position closed by TP. Net PnL: +${res2['closed_trades'][0]['pnl_cash']:.2f} ({res2['closed_trades'][0]['pnl_pips']} pips). New Balance: ${res2['balance']:,.2f}")

    print("\n[SUCCESS] ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_phase4()
