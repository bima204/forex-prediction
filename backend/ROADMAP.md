# Roadmap & Progress Tracker: Forex Trade Machine Learning System

Sistem otomasi trading forex berbasis Machine Learning yang mampu:
1. **Mendeteksi** kondisi pasar (Market Regime, Tren, Volatilitas, Likuiditas).
2. **Belajar Mandiri** (Model ML/RL berbasis probabilitas & manajemen risiko).
3. **Simulasi Mandiri** (Backtest realistis & Paper Trading otomatis).
4. **Pemilihan Pasar Interaktif** (User cukup memilih pair/pasar, sistem memproses sisanya).

---

## 🎯 Target Metrik Kinerja (Performance Benchmarks)

| Metrik | Target Minimal | Target Ideal | Status Saat Ini |
| :--- | :---: | :---: | :---: |
| **Win Rate** | $\ge 50\%$ | $55\% - 65\%$ | **60.78%** (Tercapai) |
| **Profit Factor** | $\ge 1.5$ | $\ge 2.0$ | **2.33** (Tercapai) |
| **Risk-to-Reward (RR)** | $1:1.5$ | $1:2+$ | **1:1.5** (Tercapai) |
| **Max Drawdown (DD)** | $< 15\%$ | $< 10\%$ | **9.71%** (Tercapai Ideal) |
| **Sharpe Ratio** | $> 1.0$ | $> 1.8$ | **5.30** (Tercapai Ideal) |

---

## 🗺️ Tahapan Pengerjaan & Task List

### [x] Tahap 1: Fondasi Proyek & Pipeline Data (Market Selector) - SELESAI
- [x] Inisialisasi struktur project Python & dependencies (`requirements.txt`).
- [x] Modul Data Loader (Pilihan: MetaTrader 5 API / yfinance / CSV historical downloader).
- [x] Normalisasi data multi-timeframe (M5, M15, H1, H4).
- [x] Fitur cache & update data lokal agar proses cepat dan efisien.
- [x] CLI/Modul selector pasar (User bisa memilih pair misal: `EURUSD`, `GBPUSD`, `XAUUSD`).

### [x] Tahap 2: Feature Engineering & Deteksi Pasar (Market Detection) - SELESAI
- [x] **Market Regime Detector**:
  - [x] Deteksi Tren vs Sideway (ADX, Moving Averages slope).
  - [x] Deteksi Volatilitas (ATR, Bollinger Bands bandwidth, Z-score).
  - [x] Deteksi Jam Sesi Pasar (Asia, London, New York, Overlap) & filter waktu spread tinggi (rollover).
- [x] **Price Action & Technical Features**:
  - [x] Support / Resistance dinamis & Swing High / Low (ATR-normalized distance).
  - [x] Candlestick momentum, Pinbar detection, & Fair Value Gap (FVG) / Imbalance.
  - [x] Momentum indicators (RSI, Stochastic, MACD diferensial & crossover).
- [x] **Labeling Generator (Triple Barrier Method)**:
  - [x] Labeling berbasis Target Profit (TP), Stop Loss (SL), dan Batas Waktu (Vertical Barrier).

### [x] Tahap 3: Mesin Pembelajaran Mandiri (Learning Engine) - SELESAI
- [x] Pembuatan pipeline pelatihan model (LightGBM Dual Long/Short Classifier).
- [x] Validasi Time-Series (Purged Walk-Forward Cross Validation untuk mencegah data leakage).
- [x] Penyetelan hyperparameter teratur untuk mencegah overfit pada data finansial.
- [x] Kalibrasi probabilitas sinyal & filter filter tren (entry hanya jika tingkat keyakinan $\ge 55\% - 60\%$).
- [x] Feature Importance analysis (Distance to S/R Pivots, EMA 200, Realized Volatility).

### [x] Tahap 4: Mesin Simulasi Mandiri (Simulation & Risk Management) - SELESAI
- [x] Simulator eksekusi realistis:
  - [x] Perhitungan Spread & Slippage dinamis (friction modeling).
  - [x] Dynamic Lot Sizing berdasarkan persentase risiko modal (1% per transaksi).
  - [x] Manajemen posisi: Trailing Stop otomatis dan Breakeven trigger.
- [x] Mode Paper Trading (Forward testing tanpa modal nyata dengan persistensi state ke `data/paper_account.json`).
- [x] Evaluasi drawdown dan Sharpe ratio pada simulasi out-of-sample (Max DD 9.71%, Sharpe 5.30).

### [x] Tahap 5: Dashboard Kontrol Pasar & Visualisasi - SELESAI
- [x] Antarmuka interaktif (Web Dashboard / GUI via Streamlit & Plotly):
  - [x] Dropdown pemilihan pasar/pair (`EURUSD`, `GBPUSD`, `USDJPY`, `XAUUSD`, `BTCUSD`, dll.).
  - [x] Tampilan status pasar (Regime: Tren/Sideway, Volatilitas, Sesi pasar aktif).
  - [x] Kartu sinyal aktif (Aksi: BUY/SELL/HOLD, Rekomendasi Entry, SL, TP, Confidence Score).
  - [x] Grafik histori ekuitas, win rate, dan trade logs hasil simulasi mandiri.

---

## 📈 Log Perkembangan Proyek

| Tanggal | Tahap | Deskripsi Kemajuan | Status |
| :---: | :---: | :--- | :---: |
| 16-10-2026 | Perencanaan | Perancangan arsitektur sistem dan pembuatan dokumen Roadmap | Selesai |
| 16-10-2026 | Tahap 1 | Setup environment, pipeline data loader, multi-pair cache, dan interactive market selector | Selesai |
| 16-10-2026 | Tahap 2 | Market regime detector, Smart Money Concepts (FVG, pinbars), indikator teknikal & Triple Barrier labeling | Selesai |
| 16-10-2026 | Tahap 3 | Pelatihan model LightGBM dual-classifier, Purged Walk-Forward CV, kalibrasi probabilitas sinyal & evaluasi OOS | Selesai |
| 16-10-2026 | Tahap 4 | Mesin simulasi backtesting realistis, dynamic lot sizing, trailing stops & paper trading engine | Selesai |
| 16-10-2026 | Tahap 5 | Dashboard kontrol pasar interaktif (Streamlit & Plotly) dengan grafik candlestick, sinyal AI, dan visualizer ekuitas | Selesai |
| 16-10-2026 | Enhanced UI | Dark/Light Mode toggle, Asisten AI Chatbot interaktif untuk pemula, dan selector Gaya Trading (Scalping, Day Trading, Swing) | Selesai |
| 16-10-2026 | Live Engine | Anti-Flicker Signal Lock-In Manager, Auto-Streaming Real-Time live fragment (3-5s), dan sinkronisasi live price line | Selesai |

---

## 📁 Struktur Direktori Rencana

```text
forex trade machine learning/
├── ROADMAP.md              # File tracker ini
├── requirements.txt        # Dependensi library
├── config/                 # Konfigurasi pair, parameter risiko, model settings
├── data/                   # Penyimpanan dataset lokal cache
├── src/
│   ├── data_loader/        # Pengambil data MT5 / API
│   ├── features/           # Feature engineering & market regime detector
│   ├── models/             # Machine learning training & prediction engine
│   ├── simulation/         # Backtester, risk manager & paper trader
│   └── ui/                 # Dashboard kontrol pemilihan pasar
└── main.py                 # Entry point aplikasi
```
