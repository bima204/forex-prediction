import React, { useEffect, useState } from 'react';
import { api } from './api';
import type { Candle, AnalysisResponse, PaperAccountResponse, PairItem } from './types';
import { CandlestickChart } from './components/CandlestickChart';
import { SignalCard } from './components/SignalCard';
import { PaperTraderPanel } from './components/PaperTraderPanel';
import { BacktestModal } from './components/BacktestModal';
import {
  Activity,
  Layers,
  Clock,
  RefreshCw,
  BarChart2,
  Cpu,
} from 'lucide-react';

export const App: React.FC = () => {
  const [pairs, setPairs] = useState<PairItem[]>([]);
  const [timeframes, setTimeframes] = useState<string[]>(['5m', '15m', '1h', '4h', '1d']);
  const [selectedPair, setSelectedPair] = useState<string>('EURUSD');
  const [selectedTf, setSelectedTf] = useState<string>('1h');
  const [selectedStyle, setSelectedStyle] = useState<string>('daytrading');

  const [candles, setCandles] = useState<Candle[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [paperAccount, setPaperAccount] = useState<PaperAccountResponse | null>(null);

  const [loadingMarket, setLoadingMarket] = useState<boolean>(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState<boolean>(true);
  const [isBacktestOpen, setIsBacktestOpen] = useState<boolean>(false);

  // Initial Load: Pairs metadata & Paper account
  useEffect(() => {
    async function init() {
      try {
        const pData = await api.getPairs();
        setPairs(pData.pairs);
        if (pData.timeframes) setTimeframes(pData.timeframes);

        const accData = await api.getPaperAccount();
        setPaperAccount(accData);
      } catch (err) {
        console.error('Initialization error:', err);
      }
    }
    init();
  }, []);

  // Fetch Market Data & Technical Analysis
  const fetchData = async () => {
    try {
      setLoadingMarket(true);
      const mData = await api.getMarketData(selectedPair, selectedTf);
      setCandles(mData.candles);
    } catch (err) {
      console.error('Error fetching market candles:', err);
    } finally {
      setLoadingMarket(false);
    }

    try {
      setLoadingAnalysis(true);
      const aData = await api.getAnalysis(selectedPair, selectedTf, selectedStyle);
      setAnalysis(aData);
    } catch (err) {
      console.error('Error fetching ML analysis:', err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000); // 15s refresh
    return () => clearInterval(interval);
  }, [selectedPair, selectedTf, selectedStyle]);

  // Order Handlers
  const handleExecuteOrder = async (
    action: 'BUY' | 'SELL',
    lots: number,
    sl?: number,
    tp?: number
  ) => {
    try {
      await api.executePaperOrder({
        pair: selectedPair,
        action,
        lots,
        stop_loss: sl,
        take_profit: tp,
        strategy: `AI ML (${selectedStyle})`,
      });
      const updatedAcc = await api.getPaperAccount();
      setPaperAccount(updatedAcc);
    } catch (err) {
      console.error('Order execution failed:', err);
      alert('Order gagal dieksekusi.');
    }
  };

  const handleCloseOrder = async (ticket: number) => {
    try {
      await api.closePaperOrder(ticket);
      const updatedAcc = await api.getPaperAccount();
      setPaperAccount(updatedAcc);
    } catch (err) {
      console.error('Close order failed:', err);
      alert('Gagal menutup order.');
    }
  };

  const currentPrice = analysis?.current_price || (candles.length ? candles[candles.length - 1].close : 0);

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1680px', margin: '0 auto' }}>
      {/* Top Navbar */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
            }}
          >
            <Cpu size={24} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
              Forex AI Trading Terminal
            </h1>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Machine Learning Autonomous Signal & Simulation Engine
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => setIsBacktestOpen(true)}
            className="glass-panel"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            <BarChart2 size={16} color="var(--color-accent)" />
            Run Backtest
          </button>

          <button
            onClick={fetchData}
            className="glass-panel"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            <RefreshCw size={15} className={loadingMarket ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </header>

      {/* Control Bar: Pair Selector, Timeframe, Trading Style */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '14px 20px',
          marginBottom: '20px',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {/* Pair Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={16} color="var(--text-muted)" />
            <select
              value={selectedPair}
              onChange={(e) => setSelectedPair(e.target.value)}
              style={{
                background: '#121826',
                border: '1px solid rgba(255,255,255,0.12)',
                color: '#fff',
                padding: '6px 14px',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer',
              }}
            >
              {pairs.length > 0 ? (
                pairs.map((p) => (
                  <option key={p.symbol} value={p.symbol}>
                    {p.symbol} - {p.name}
                  </option>
                ))
              ) : (
                <option value="EURUSD">EURUSD</option>
              )}
            </select>
          </div>

          {/* Timeframe Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={16} color="var(--text-muted)" />
            <div style={{ display: 'flex', background: '#121826', padding: '3px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => setSelectedTf(tf)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    fontSize: '12px',
                    fontWeight: selectedTf === tf ? 700 : 500,
                    backgroundColor: selectedTf === tf ? 'var(--color-accent)' : 'transparent',
                    color: selectedTf === tf ? '#fff' : 'var(--text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  {tf.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Style Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Style:</span>
            <select
              value={selectedStyle}
              onChange={(e) => setSelectedStyle(e.target.value)}
              style={{
                background: '#121826',
                border: '1px solid rgba(255,255,255,0.12)',
                color: '#fff',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <option value="scalping">⚡ Scalping (5m)</option>
              <option value="daytrading">☀️ Day Trading (1h)</option>
              <option value="swing">🌊 Swing Trading (4h)</option>
            </select>
          </div>
        </div>

        {/* Live Price Tag */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>LIVE PRICE</span>
          <span className="font-mono" style={{ fontSize: '22px', fontWeight: 800, color: '#fff' }}>
            {currentPrice ? currentPrice.toFixed(5) : '---'}
          </span>
        </div>
      </div>

      {/* Main Grid: Left Chart + Left Indicators, Right AI Signals & Paper Trading */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
        {/* Left Column: Interactive Candlestick Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            className="glass-panel"
            style={{
              padding: '20px',
              height: '520px',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={18} color="var(--color-accent)" />
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#fff' }}>
                  {selectedPair} Candlestick Overview ({selectedTf.toUpperCase()})
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Powered by TradingView Lightweight Charts
              </div>
            </div>

            <div style={{ flex: 1, width: '100%' }}>
              <CandlestickChart candles={candles} pair={selectedPair} />
            </div>
          </div>

          {/* Technical Indicators Strip */}
          {analysis && analysis.indicators && (
            <div
              className="glass-panel"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: '14px',
                padding: '16px 20px',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>RSI (14)</div>
                <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                  {analysis.indicators.rsi ?? '-'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MACD</div>
                <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                  {analysis.indicators.macd ?? '-'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MACD Signal</div>
                <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                  {analysis.indicators.macd_signal ?? '-'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ADX (Trend Strength)</div>
                <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                  {analysis.indicators.adx ?? '-'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ATR Volatility</div>
                <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                  {analysis.indicators.atr ? analysis.indicators.atr.toFixed(5) : '-'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: AI Signal Card + Paper Trading Desk */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <SignalCard analysis={analysis} loading={loadingAnalysis} />

          <PaperTraderPanel
            account={paperAccount}
            currentPair={selectedPair}
            currentPrice={currentPrice}
            onExecuteOrder={handleExecuteOrder}
            onCloseOrder={handleCloseOrder}
            suggestedSL={analysis?.stop_loss}
            suggestedTP={analysis?.take_profit}
          />
        </div>
      </div>

      {/* Backtest Modal */}
      <BacktestModal
        isOpen={isBacktestOpen}
        onClose={() => setIsBacktestOpen(false)}
        currentPair={selectedPair}
        currentTimeframe={selectedTf}
      />
    </div>
  );
};

export default App;
