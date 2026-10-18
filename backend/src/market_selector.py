"""
Interactive Market Selector Module for Forex Machine Learning System.
Allows selecting trading pairs, inspecting market statistics, and caching data.
"""
from typing import Optional, List, Dict
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DEFAULT_PAIRS, SUPPORTED_TIMEFRAMES
from src.data_loader.data_manager import DataManager

console = Console()


class MarketSelector:
    """
    Market Selection controller with CLI interface and programmatic API.
    """

    def __init__(self, data_manager: Optional[DataManager] = None):
        self.dm = data_manager or DataManager()

    def list_available_markets(self) -> List[Dict[str, str]]:
        """
        Returns list of configured markets and their descriptions.
        """
        markets = []
        for code, info in DEFAULT_PAIRS.items():
            markets.append({
                "code": code,
                "name": info["name"],
                "pip_decimal": info["pip_decimal"],
            })
        return markets

    def display_market_catalog(self):
        """
        Renders a beautiful Rich table of all supported markets.
        """
        table = Table(title="[Katalog Pasar Forex & Komoditas]", header_style="bold cyan")
        table.add_column("No", justify="center", style="dim", width=4)
        table.add_column("Kode Pasar (Pair)", justify="center", style="bold yellow")
        table.add_column("Nama Deskripsi", style="white")
        table.add_column("Presisi Pip", justify="center", style="green")

        for idx, (code, info) in enumerate(DEFAULT_PAIRS.items(), 1):
            table.add_row(str(idx), code, info["name"], f"{info['pip_decimal']} desimal")

        console.print(table)

    def select_market(
        self,
        symbol: str,
        timeframe: str = "1h",
        force_refresh: bool = False,
    ):
        """
        Picks a market symbol, downloads/loads OHLCV data, and prints snapshot summary.
        """
        symbol_upper = symbol.upper().strip()
        timeframe = timeframe.lower().strip()

        with console.status(f"[bold green]Mengambil data pasar untuk {symbol_upper} ({timeframe})...", spinner="dots"):
            try:
                df = self.dm.get_ohlcv(symbol_upper, timeframe=timeframe, force_refresh=force_refresh)
            except Exception as e:
                console.print(f"[bold red][ERROR] Gagal mengambil data untuk {symbol_upper}:[/bold red] {e}")
                return None, None

        summary = self.dm.get_market_summary(df, symbol_upper)

        # Display Summary Panel
        change_color = "green" if summary["change"] >= 0 else "red"
        sign = "+" if summary["change"] >= 0 else ""

        panel_content = (
            f"[bold cyan]Pasar:[/bold cyan] {summary['name']} ([yellow]{summary['symbol']}[/yellow])\n"
            f"[bold cyan]Timeframe:[/bold cyan] {timeframe.upper()} | [bold cyan]Total Bar Lilin:[/bold cyan] {summary['bars_count']:,}\n"
            f"[bold cyan]Rentang Waktu:[/bold cyan] {summary['start_time']} s/d {summary['last_time']}\n"
            f"--------------------------------------------------\n"
            f"[bold cyan]Harga Terakhir:[/bold cyan] [bold white]{summary['current_close']:.5f}[/bold white]\n"
            f"[bold cyan]Perubahan:[/bold cyan] [{change_color}]{sign}{summary['change']:.5f} ({sign}{summary['change_pct']:.2f}%)[/{change_color}]\n"
            f"[bold cyan]Rentang 24 Jam:[/bold cyan] {summary['range_24h_pips']:.1f} pips\n"
            f"[bold cyan]Status Cache:[/bold cyan] [green]Tersimpan & Siap untuk Pelatihan AI[/green]"
        )

        console.print(Panel(panel_content, title=f"[Ringkasan Pasar: {symbol_upper}]", border_style="bright_blue"))
        return df, summary


def interactive_cli():
    """
    Interactive prompt for the user to pick a market.
    """
    selector = MarketSelector()
    selector.display_market_catalog()

    console.print("\n[bold]Pilih kode pasar yang ingin dianalisis (contoh: EURUSD, GBPUSD, XAUUSD) atau ketik 'exit':[/bold]")
    choice = input(">> ").strip()

    if choice.lower() in ["exit", "quit", "q"]:
        console.print("[dim]Keluar dari selector.[/dim]")
        return

    tf_choice = input(f"Pilih timeframe {SUPPORTED_TIMEFRAMES} [default: 1h]: ").strip() or "1h"
    df, summary = selector.select_market(choice, timeframe=tf_choice)
    if df is not None:
        console.print(f"\n[bold green]✅ Berhasil memuat {len(df)} bar data pasar {choice.upper()}![/bold green]")


if __name__ == "__main__":
    interactive_cli()
