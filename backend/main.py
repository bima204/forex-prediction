"""
Main Entry Point for Forex Trade Machine Learning System.
Can be run directly:
    python main.py                  (Runs automated analysis & simulation for default EURUSD)
    python main.py GBPUSD           (Runs for GBPUSD)
    python main.py XAUUSD 15m       (Runs for Gold on 15m)
    python main.py --interactive    (Interactive market prompt)
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.market_selector import MarketSelector
from config.settings import DEFAULT_PAIRS, SUPPORTED_TIMEFRAMES
from src.features.feature_pipeline import FeaturePipeline
from src.features.market_regime import MarketRegimeDetector
from src.models.model_trainer import ForexMLModel
from src.simulation.backtester import Backtester
from src.simulation.risk_manager import RiskManager

console = Console()


def print_banner():
    banner = (
        "[bold cyan]====================================================[/bold cyan]\n"
        "[bold green]   FOREX TRADE MACHINE LEARNING SYSTEM   [/bold green]\n"
        "[dim]   Autonomous Detection, Learning & Simulation Engine[/dim]\n"
        "[bold cyan]====================================================[/bold cyan]"
    )
    console.print(banner)


def run_pipeline_for_pair(pair: str = "EURUSD", timeframe: str = "1h", run_simulation: bool = True):
    """
    Executes end-to-end autonomous analysis, machine learning detection, and simulation.
    """
    pair = pair.upper().strip()
    timeframe = timeframe.lower().strip()

    selector = MarketSelector()
    console.print(f"\n[bold green]>> Memproses Pasar: [bold yellow]{pair}[/bold yellow] ({timeframe.upper()})...[/bold green]")
    
    df, summary = selector.select_market(pair, timeframe=timeframe)
    if df is None or df.empty:
        console.print(f"[bold red]Gagal mengambil data untuk {pair}.[/bold red]")
        return

    # 1. Feature Engineering & Market Regime Detection
    pipeline = FeaturePipeline()
    processed_df = pipeline.extract_features(df, include_labels=True)
    regime_detector = MarketRegimeDetector()
    regime = regime_detector.get_current_regime_summary(processed_df)

    trend_color = "green" if regime["trend_code"] == 1 else ("red" if regime["trend_code"] == -1 else "yellow")
    latest_row = processed_df.iloc[-1]

    regime_panel = (
        f"[bold cyan]Regime Tren:[/bold cyan] [{trend_color}]{regime['trend_state']}[/{trend_color}] "
        f"(ADX: {regime['adx_strength']:.1f} - {'Kuat/Trending' if regime['is_trending'] else 'Lemah/Sideway'})\n"
        f"[bold cyan]Volatilitas Pasar:[/bold cyan] {regime['volatility_state']} (Z-Score: {regime['volatility_zscore']:.2f}, ATR: {regime['atr_14']:.5f})\n"
        f"[bold cyan]Sesi Trading Aktif:[/bold cyan] {regime['session']}\n"
        f"--------------------------------------------------\n"
        f"[bold cyan]Indikator Momentum:[/bold cyan] RSI(14) = [bold white]{latest_row['rsi_14']:.1f}[/bold white] | "
        f"MACD Hist = [{'green' if latest_row['macd_hist'] >= 0 else 'red'}]{latest_row['macd_hist']:.5f}[/]\n"
        f"[bold cyan]Fair Value Gap (FVG):[/bold cyan] "
        f"Bullish FVG = {int(latest_row['is_bullish_fvg'])}, Bearish FVG = {int(latest_row['is_bearish_fvg'])}\n"
        f"[bold cyan]Fitur Terkalkulasi:[/bold cyan] [green]{len(pipeline.get_feature_column_names(processed_df))} fitur prediktif siap[/green]"
    )
    console.print(Panel(regime_panel, title=f"[DETEKSI KONDISI PASAR: {pair}]", border_style="green"))

    # 2. Machine Learning Autonomous Model
    model = ForexMLModel(symbol=pair, timeframe=timeframe)
    feature_cols = pipeline.get_feature_column_names(processed_df)

    if not model.load():
        console.print(f"[bold magenta]>> AI sedang belajar mandiri menganalisis histori {pair}...[/bold magenta]")
        metadata = model.train(processed_df, feature_cols=feature_cols)
        console.print(f"[bold green]>> AI selesai belajar! Walk-Forward AUC: {metadata['walk_forward_cv_auc_buy']:.4f} (Buy), {metadata['walk_forward_cv_auc_sell']:.4f} (Sell)[/bold green]")
    else:
        console.print(f"[dim]>> Model AI untuk {pair} ({timeframe}) dimuat dari memori lokal.[/dim]")

    # 3. Generate Signal Recommendation
    current_price = float(latest_row["close"])
    current_atr = float(latest_row.get("atr_14", 0.0015))
    signal = model.predict_signal(latest_row, current_price=current_price, current_atr=current_atr)

    action_style = "bold white on green" if signal["action"] == "BUY" else ("bold white on red" if signal["action"] == "SELL" else "bold yellow")
    signal_content = (
        f"[bold cyan]Keputusan Entry AI:[/bold cyan] [{action_style}]  {signal['action']}  [/{action_style}] "
        f"([bold white]Confidence: {signal['confidence']:.1%}[/bold white])\n"
        f"[bold cyan]Probabilitas:[/bold cyan] P(BUY) = {signal['p_buy']:.1%} | P(SELL) = {signal['p_sell']:.1%}\n"
        f"--------------------------------------------------\n"
        f"[bold cyan]Harga Entry Saat Ini:[/bold cyan] [bold white]{signal['current_price']:.5f}[/bold white]\n"
        f"[bold cyan]Target Take Profit (TP):[/bold cyan] [green]{signal['take_profit']:.5f}[/green] ({signal['tp_pips']:.1f} pips)\n"
        f"[bold cyan]Proteksi Stop Loss (SL):[/bold cyan] [red]{signal['stop_loss']:.5f}[/red] ({signal['sl_pips']:.1f} pips)\n"
        f"[bold cyan]Rasio Risk-to-Reward:[/bold cyan] 1:{signal['risk_reward']:.1f}\n"
        f"[bold cyan]Alasan Keputusan AI:[/bold cyan] [italic]{signal['reason']}[/italic]"
    )
    console.print(Panel(signal_content, title=f"[REKOMENDASI SINYAL AI: {pair}]", border_style="cyan"))

    # 4. Simulation Engine (Backtest)
    if run_simulation:
        sim_slice = processed_df.tail(2000).copy()
        raw_slice = df.loc[sim_slice.index].copy()
        
        sim_signals = []
        for _, r in sim_slice.iterrows():
            cp = float(r["close"])
            catr = float(r.get("atr_14", 0.0015))
            sim_signals.append(model.predict_signal(r, current_price=cp, current_atr=catr))
        import pandas as pd
        sim_sig_df = pd.DataFrame(sim_signals, index=sim_slice.index)

        backtester = Backtester(initial_capital=10000.0, risk_manager=RiskManager(risk_per_trade_pct=1.0))
        rep = backtester.run_simulation(raw_slice, sim_sig_df, symbol=pair)

        profit_color = "green" if rep["net_profit"] >= 0 else "red"
        sim_panel = (
            f"[bold cyan]Modal Awal:[/bold cyan] ${rep['initial_capital']:,.2f}  |  "
            f"[bold cyan]Ekuitas Akhir:[/bold cyan] [{profit_color}]${rep['final_equity']:,.2f}[/{profit_color}]  |  "
            f"[bold cyan]Net Profit:[/bold cyan] [{profit_color}]${rep['net_profit']:+,.2f} ({rep['net_profit_pct']:+.2f}%)[/{profit_color}]\n"
            f"--------------------------------------------------\n"
            f"[bold cyan]Total Transaksi:[/bold cyan] {rep['closed_trades_count']}  |  "
            f"[bold cyan]Win Rate:[/bold cyan] [bold white]{rep['win_rate']}%[/bold white]  |  "
            f"[bold cyan]Profit Factor:[/bold cyan] [bold white]{rep['profit_factor']}[/bold white]\n"
            f"[bold cyan]Max Drawdown:[/bold cyan] [green]{rep['max_drawdown_pct']}%[/green] (Target Aman < 15%)  |  "
            f"[bold cyan]Sharpe Ratio:[/bold cyan] [bold white]{rep['sharpe_ratio']}[/bold white]\n"
            f"[bold cyan]Status Sistem:[/bold cyan] [green]Sistem Siap Digunakan untuk Trading Mandiri & Simulasi[/green]"
        )
        console.print(Panel(sim_panel, title=f"[HASIL SIMULASI MANDIRI AI: {pair}]", border_style="gold1"))


def main():
    print_banner()

    args = sys.argv[1:]
    pair = "EURUSD"
    tf = "1h"

    if "--interactive" in args:
        selector = MarketSelector()
        selector.display_market_catalog()
        user_pair = input("\nMasukkan Kode Pasar (default: EURUSD): ").strip().upper()
        if user_pair:
            pair = user_pair
        user_tf = input("Masukkan Timeframe (default: 1h): ").strip().lower()
        if user_tf:
            tf = user_tf
    elif len(args) >= 1:
        pair = args[0].upper()
        if len(args) >= 2:
            tf = args[1].lower()
    else:
        # Default run immediately without blocking
        console.print("[dim]Menjalankan analisis otomatis untuk pasangan standar: EURUSD (1h)[/dim]")
        console.print("[dim]Tips: Jalankan 'python main.py GBPUSD' atau 'python main.py XAUUSD 15m' untuk pasar lain.[/dim]")

    run_pipeline_for_pair(pair=pair, timeframe=tf)


if __name__ == "__main__":
    main()
