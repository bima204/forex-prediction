import React, { useState } from 'react';
import type { PaperAccountResponse } from '../types';
import { Wallet, ArrowUpRight, ArrowDownRight, XCircle } from 'lucide-react';

interface PaperTraderPanelProps {
  account: PaperAccountResponse | null;
  currentPair: string;
  currentPrice?: number;
  onExecuteOrder: (action: 'BUY' | 'SELL', lots: number, sl?: number, tp?: number) => void;
  onCloseOrder: (ticket: number) => void;
  suggestedSL?: number | null;
  suggestedTP?: number | null;
}

export const PaperTraderPanel: React.FC<PaperTraderPanelProps> = ({
  account,
  currentPair,
  onExecuteOrder,
  onCloseOrder,
  suggestedSL,
  suggestedTP,
}) => {
  const [lots, setLots] = useState(0.1);
  const [customSL, setCustomSL] = useState<string>('');
  const [customTP, setCustomTP] = useState<string>('');

  const handleBuy = () => {
    const sl = customSL ? parseFloat(customSL) : suggestedSL || undefined;
    const tp = customTP ? parseFloat(customTP) : suggestedTP || undefined;
    onExecuteOrder('BUY', lots, sl, tp);
  };

  const handleSell = () => {
    const sl = customSL ? parseFloat(customSL) : suggestedSL || undefined;
    const tp = customTP ? parseFloat(customTP) : suggestedTP || undefined;
    onExecuteOrder('SELL', lots, sl, tp);
  };

  const balance = account ? account.balance : 10000;
  const openPositions = account ? account.open_positions : [];

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Wallet size={20} color="var(--color-accent)" />
          <span style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Paper Trading Simulator</span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>ACCOUNT BALANCE</div>
          <div className="font-mono" style={{ fontSize: '18px', fontWeight: 800, color: 'var(--color-buy)' }}>
            ${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Execution Form */}
      <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Lot Size</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={lots}
              onChange={(e) => setLots(parseFloat(e.target.value) || 0.01)}
              style={{
                width: '100%',
                padding: '8px 10px',
                background: '#121826',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                color: '#fff',
                fontFamily: 'JetBrains Mono',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Stop Loss</label>
            <input
              type="number"
              step="0.0001"
              placeholder={suggestedSL ? suggestedSL.toFixed(4) : 'Auto'}
              value={customSL}
              onChange={(e) => setCustomSL(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                background: '#121826',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                color: '#fff',
                fontFamily: 'JetBrains Mono',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Take Profit</label>
            <input
              type="number"
              step="0.0001"
              placeholder={suggestedTP ? suggestedTP.toFixed(4) : 'Auto'}
              value={customTP}
              onChange={(e) => setCustomTP(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                background: '#121826',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                color: '#fff',
                fontFamily: 'JetBrains Mono',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <button
            onClick={handleBuy}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '12px',
              background: 'linear-gradient(135deg, #059669, #10b981)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'transform 0.15s ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseOut={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <ArrowUpRight size={18} /> BUY {currentPair}
          </button>

          <button
            onClick={handleSell}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '12px',
              background: 'linear-gradient(135deg, #dc2626, #ef4444)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'transform 0.15s ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseOut={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <ArrowDownRight size={18} /> SELL {currentPair}
          </button>
        </div>
      </div>

      {/* Open Positions List */}
      <div>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px' }}>
          Active Positions ({openPositions.length})
        </div>

        {openPositions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)', fontSize: '13px' }}>
            Tidak ada posisi terbuka saat ini.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
            {openPositions.map((pos) => {
              const isLong = pos.direction === 'BUY';
              return (
                <div
                  key={pos.ticket_id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(255,255,255,0.03)',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: isLong ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                          color: isLong ? 'var(--color-buy)' : 'var(--color-sell)',
                        }}
                      >
                        {pos.direction}
                      </span>
                      <span style={{ fontWeight: 700, fontSize: '13px' }}>{pos.symbol}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{pos.lot_size} lots</span>
                    </div>
                    <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Entry: {pos.entry_price} | SL: {pos.stop_loss} | TP: {pos.take_profit}
                    </div>
                  </div>

                  <button
                    onClick={() => onCloseOrder(pos.ticket_id)}
                    style={{
                      background: 'rgba(239,68,68,0.15)',
                      border: '1px solid rgba(239,68,68,0.3)',
                      color: 'var(--color-sell)',
                      borderRadius: '6px',
                      padding: '6px 10px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <XCircle size={14} /> Close
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
