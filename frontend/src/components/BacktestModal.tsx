import React, { useState } from 'react';
import { api } from '../api';
import type { BacktestResult } from '../types';
import { Play, BarChart3 } from 'lucide-react';

interface BacktestModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPair: string;
  currentTimeframe: string;
}

export const BacktestModal: React.FC<BacktestModalProps> = ({
  isOpen,
  onClose,
  currentPair,
  currentTimeframe,
}) => {
  const [balance, setBalance] = useState(10000);
  const [riskPct, setRiskPct] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);

  if (!isOpen) return null;

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await api.runBacktest({
        pair: currentPair,
        timeframe: currentTimeframe,
        initial_balance: balance,
        risk_pct: riskPct,
      });
      setResult(res);
    } catch (err) {
      console.error(err);
      alert('Gagal menjalankan backtest.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '540px',
          padding: '28px',
          background: '#0d1322',
          border: '1px solid rgba(255,255,255,0.12)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 color="var(--color-accent)" size={22} />
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              ML Backtest Simulation ({currentPair} • {currentTimeframe})
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '20px',
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              Initial Balance ($)
            </label>
            <input
              type="number"
              value={balance}
              onChange={(e) => setBalance(parseFloat(e.target.value) || 1000)}
              style={{
                width: '100%',
                padding: '10px',
                background: '#161f33',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontFamily: 'JetBrains Mono',
              }}
            />
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              Risk Per Trade (%)
            </label>
            <input
              type="number"
              step="0.5"
              value={riskPct}
              onChange={(e) => setRiskPct(parseFloat(e.target.value) || 1.0)}
              style={{
                width: '100%',
                padding: '10px',
                background: '#161f33',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontFamily: 'JetBrains Mono',
              }}
            />
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            background: 'var(--color-accent)',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            fontWeight: 700,
            fontSize: '14px',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            marginBottom: '20px',
          }}
        >
          <Play size={16} /> {loading ? 'Menjalankan Simulasi...' : 'Jalankan Backtest'}
        </button>

        {result && (
          <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', padding: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Hasil Backtest:
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              <div style={{ background: '#121826', padding: '10px 14px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Win Rate</div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--color-buy)' }}>
                  {result.win_rate ? `${(result.win_rate * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>

              <div style={{ background: '#121826', padding: '10px 14px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Total Trades</div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: '#fff' }}>
                  {result.total_trades || 0}
                </div>
              </div>

              <div style={{ background: '#121826', padding: '10px 14px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Total Net PnL</div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: (result.total_pnl || 0) >= 0 ? 'var(--color-buy)' : 'var(--color-sell)' }}>
                  ${(result.total_pnl || 0).toLocaleString()}
                </div>
              </div>

              <div style={{ background: '#121826', padding: '10px 14px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Max Drawdown</div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--color-sell)' }}>
                  {result.max_drawdown_pct ? `${result.max_drawdown_pct.toFixed(2)}%` : '0.00%'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
