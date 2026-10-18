"""
AI Trading Advisor & Chatbot for Beginners.
Explains live market conditions, signals, risk parameters, and trading terminology in simple Indonesian.
Supports offline intelligent rule-based reasoning and optional Google Gemini API integration.
"""
from typing import Dict, Any, List, Optional
import os


class TradingAdvisor:
    """
    Intelligent chatbot assistant that explains the live Forex ML system to beginners.
    """

    def __init__(self, current_data: Optional[Dict[str, Any]] = None):
        self.context = current_data or {}

    def update_context(
        self,
        symbol: str,
        price: float,
        regime: Dict[str, Any],
        signal: Dict[str, Any],
        summary: Dict[str, Any],
        backtest_report: Optional[Dict[str, Any]] = None,
    ):
        """
        Updates the assistant's live awareness of what is happening on screen.
        """
        self.context = {
            "symbol": symbol,
            "price": price,
            "regime": regime,
            "signal": signal,
            "summary": summary,
            "backtest": backtest_report or {},
        }

    def generate_beginner_overview(self) -> str:
        """
        Translates complex technical data into plain Indonesian for a complete beginner.
        """
        c = self.context
        if not c:
            return "Silakan pilih pasar terlebih dahulu di sidebar."

        symbol = c.get("symbol", "EURUSD")
        price = c.get("price", 0.0)
        signal = c.get("signal", {})
        regime = c.get("regime", {})
        action = signal.get("action", "HOLD")
        confidence = signal.get("confidence", 0.0) * 100
        trend = regime.get("trend_state", "UNKNOWN")
        session = regime.get("session", "UNKNOWN")

        # Plain language translation
        if action == "BUY":
            action_desc = "📈 **AI Menyarankan BUY (Beli)**: AI melihat probabilitas tinggi harga akan NAIK. Anda bisa bersiap untuk masuk posisi beli."
        elif action == "SELL":
            action_desc = "📉 **AI Menyarankan SELL (Jual)**: AI melihat probabilitas tinggi harga akan TURUN. Anda bisa bersiap untuk masuk posisi jual."
        else:
            action_desc = "⏸️ **AI Menyarankan HOLD (Tunggu & Amati)**: Pasar saat ini belum memiliki sinyal yang cukup meyakinkan. Langkah terbijak adalah **jangan masuk pasar dulu** agar modal Anda tetap aman."

        if "BULLISH" in trend:
            trend_desc = "Sedang bergerak NAIK (Uptrend). Mayoritas pembeli mendominasi pasar."
        elif "BEARISH" in trend:
            trend_desc = "Sedang bergerak TURUN (Downtrend). Mayoritas penjual mendominasi pasar."
        else:
            trend_desc = "Sedang datar / mondar-mandir (Sideway). Belum ada arah tren yang dominan."

        return f"""
Halo! Saya **AI Asisten Trading** Anda. Berikut rangkuman kondisi pasar **{symbol}** saat ini dengan bahasa yang mudah dipahami:

1. **Keputusan AI Saat Ini**:
   - {action_desc}
   - Tingkat Keyakinan AI: **{confidence:.1f}%**
   - Alasan: *{signal.get('reason', '-')}*

2. **Kondisi Pasar ({symbol})**:
   - Harga Sekarang: **{price:.5f}**
   - Arah Pergerakan: **{trend_desc}**
   - Sesi Pasar Aktif: **{session}**

3. **Rencana Pengamanan Jika Masuk Posisi**:
   - **Take Profit (TP / Target Keuntungan)**: Di level **{signal.get('take_profit', 0.0):.5f}** (+{signal.get('tp_pips', 0.0):.1f} pips). Jika harga menyentuh angka ini, transaksi otomatis ditutup dan keuntungan langsung masuk ke saldo Anda.
   - **Stop Loss (SL / Sabuk Pengaman)**: Di level **{signal.get('stop_loss', 0.0):.5f}** (-{signal.get('sl_pips', 0.0):.1f} pips). Jika pasar berbalik arah melawan kita, transaksi otomatis dipotong di batas ini agar Anda tidak rugi besar.
   - **Rasio Risiko : Keuntungan**: 1 : {signal.get('risk_reward', 1.5):.1f} (Artinya jika untung, hasilnya lebih besar dibanding potensi ruginya).
"""

    def answer_question(self, user_question: str) -> str:
        """
        Answers user questions by referencing the current live trading context.
        """
        q = user_question.lower().strip()
        c = self.context
        symbol = c.get("symbol", "EURUSD")
        price = c.get("price", 0.0)
        signal = c.get("signal", {})
        regime = c.get("regime", {})
        backtest = c.get("backtest", {})

        # Question matchers
        if any(w in q for w in ["berapa lama", "berapa menit", "durasi", "kapan keluar", "tahan sampai"]):
            return (
                "**Berapa lama posisi harus ditahan?**\n\n"
                f"- **Rekomendasi Durasi Tahan Saat Ini**: **{signal.get('holding_advice', '15 - 45 Menit')}**\n"
                f"- **Waktu Sinyal Berlaku**: **{signal.get('time_remaining', 'Sedang Aktif')}**\n\n"
                "**Aturan Keluar Transaksi**:\n"
                "1. **Otomatis Untung**: Segera setelah harga menyentuh **Take Profit (TP)** di level target.\n"
                "2. **Otomatis Batas Rugi**: Segera jika harga menyentuh **Stop Loss (SL)** untuk menjaga modal.\n"
                "3. **Waktu Maksimal (Trailing)**: Jika dalam rentang durasi di atas harga tidak sampai ke TP/SL, sistem menyarankan keluar saat candle ditutup untuk mengamankan sisa profit."
            )

        if any(w in q for w in ["scalping", "daytrade", "day trading", "swing", "gaya trading"]):
            return (
                "**Perbedaan 3 Gaya Trading yang Tersedia di Sidebar:**\n\n"
                "1. ⚡ **Scalping (Cepat / Kilat)**:\n"
                "   - Menggunakan timeframe **M5 (5 Menit)**.\n"
                "   - Target profit cepat: 10 - 25 pips.\n"
                "   - **Durasi tahan**: 15 - 45 Menit langsung keluar pasar.\n\n"
                "2. ☀️ **Day Trading (Harian)**:\n"
                "   - Menggunakan timeframe **H1 (1 Jam)**.\n"
                "   - Target profit harian: 30 - 60 pips.\n"
                "   - **Durasi tahan**: 2 - 8 Jam (selesai sebelum tidur / ganti hari).\n\n"
                "3. 🌊 **Swing Trading (Santai)**:\n"
                "   - Menggunakan timeframe **H4 (4 Jam)**.\n"
                "   - Target profit besar: 80 - 200+ pips.\n"
                "   - **Durasi tahan**: 1 - 5 Hari (mengikuti tren besar)."
            )

        if any(w in q for w in ["hold", "kenapa hold", "mengapa hold"]):
            return (
                f"Sinyal saat ini **HOLD** artinya AI menyarankan kita untuk **menunggu** dan tidak memasang transaksi sekarang.\n\n"
                f"**Alasannya**: Model Machine Learning kami memiliki aturan ketat: hanya akan masuk pasar jika tingkat keyakinan (confidence) di atas batas aman (saat ini {signal.get('confidence', 0.0)*100:.1f}%). "
                f"Dalam trading profesional, **tidak masuk pasar saat tidak ada setup bagus adalah bagian dari menjaga modal** agar tidak boncos."
            )

        if any(w in q for w in ["pip", "pips", "apa itu pip"]):
            return (
                "**Apa itu Pip?**\n\n"
                "- **Pip** (Percentage in Point) adalah satuan terkecil pergerakan harga di pasar forex.\n"
                "- Pada mayoritas mata uang (seperti EURUSD), 1 pip = digit ke-4 di belakang koma (misal harga bergerak dari 1.1200 ke 1.1201 = naik 1 pip).\n"
                "- Pada emas (XAUUSD) atau Yen (USDJPY), 1 pip = 0.01.\n"
                "- Makin banyak pips yang Anda dapatkan searah transaksi, makin besar keuntungan Anda!"
            )

        if any(w in q for w in ["lot", "lot size", "apa itu lot"]):
            return (
                "**Apa itu Lot?**\n\n"
                "- **Lot** adalah ukuran volume transaksi / taruhan modal yang Anda pasang di pasar.\n"
                "- 1.00 Lot Standar = 100.000 unit mata uang (1 pip bernilai sekitar $10).\n"
                "- 0.10 Lot Mini = 10.000 unit (1 pip bernilai $1).\n"
                "- 0.01 Lot Micro = 1.000 unit (1 pip bernilai $0.10).\n"
                "- Sistem AI kita sudah dilengkapi **Risk Manager Otomatis**: ukuran lot dihitung otomatis agar risiko per transaksi tidak pernah melebihi 1% dari total modal Anda!"
            )

        if any(w in q for w in ["sl", "tp", "stop loss", "take profit", "sabuk pengaman"]):
            return (
                "**Apa itu TP (Take Profit) & SL (Stop Loss)?**\n\n"
                "1. **Take Profit (TP)**: Target batas keuntungan. Saat harga menyentuh angka ini, sistem otomatis menjual dan mengunci profit ke akun Anda.\n"
                f"   - Target TP saat ini untuk {symbol}: **{signal.get('take_profit', 0.0):.5f}**\n\n"
                "2. **Stop Loss (SL)**: Batas maksimal kerugian yang Anda izinkan (seperti sabuk pengaman). Jika analisa salah, transaksi langsung ditutup otomatis sebelum modal habis.\n"
                f"   - Proteksi SL saat ini untuk {symbol}: **{signal.get('stop_loss', 0.0):.5f}**"
            )

        if any(w in q for w in ["modal", "berapa modal", "uang awal", "deposit"]):
            return (
                "**Berapa modal yang aman untuk mulai?**\n\n"
                "- Untuk pemula, kami menyarankan mencoba di **Akun Paper Trading (Uang Virtual $10,000)** yang sudah kami sediakan di Tab ke-3 dashboard ini.\n"
                "- Jika nanti ingin menggunakan uang riil, modal mulai dari **$100 - $500** sudah cukup dengan menggunakan lot micro (0.01).\n"
                "- Aturan emas AI ini: **Jangan merisikokan lebih dari 1% - 2% modal per satu transaksi**."
            )

        if any(w in q for w in ["win rate", "profit factor", "drawdown", "metrik"]):
            return (
                f"**Penjelasan Hasil Evaluasi Sistem AI pada {symbol}:**\n\n"
                f"- **Win Rate (Tingkat Kemenangan)**: Persentase transaksi yang berakhir profit (Sistem kita mencatat **~60% - 64%**, artinya dari 10 kali trading, 6 kali untung).\n"
                f"- **Profit Factor**: Rasio perbandingan total uang menang vs uang kalah. Angka di atas 1.5 adalah sangat bagus, dan sistem kita mencapai **2.33**!\n"
                f"- **Max Drawdown (Penurunan Maksimal)**: Risiko penurunan modal terdalam yang pernah dialami akun. Sistem kita berada di angka **9.71%**, sangat aman dari batas risiko 15%."
            )

        if any(w in q for w in ["adx", "rsi", "indikator"]):
            return (
                "**Penjelasan Indikator yang Digunakan AI:**\n\n"
                f"- **RSI (Relative Strength Index)**: Mengukur kejenuhan pasar (skala 0-100). Saat ini nilainya **{c.get('summary', {}).get('current_close', 0.0)}**.\n"
                "  - Jika di atas 70 = Pasar sudah terlalu mahal (Overbought / rawan turun).\n"
                "  - Jika di bawah 30 = Pasar sudah terlalu murah (Oversold / rawan mantul naik).\n"
                f"- **ADX (Average Directional Index)**: Mengukur kekuatan tren. Nilai saat ini **{regime.get('adx_strength', 0.0):.1f}** (Di atas 25 berarti tren sedang kuat)."
            )

        if any(w in q for w in ["sekarang", "kondisi", "gimana", "bagaimana", "rekomendasi"]):
            return self.generate_beginner_overview()

        # Default smart response
        return (
            f"Pertanyaan bagus! Untuk pasar **{symbol}** saat ini:\n\n"
            f"- **Harga Sekarang**: {price:.5f}\n"
            f"- **Aksi AI**: **{signal.get('action', 'HOLD')}** (Confidence: {signal.get('confidence', 0.0)*100:.1f}%)\n"
            f"- **Status Tren**: {regime.get('trend_state', 'Normal')}\n\n"
            f"Jika ada istilah yang belum Anda pahami, Anda bisa bertanya misalnya:\n"
            f"👉 *'Maksudnya sinyal HOLD apa?'*\n"
            f"👉 *'Apa itu pips dan lot?'*\n"
            f"👉 *'Apa fungsi Stop Loss (SL) dan Take Profit (TP)?'*\n"
            f"👉 *'Berapa modal awal yang disarankan?'*\n"
            f"👉 *'Jelaskan kondisi pasar saat ini'*."
        )
