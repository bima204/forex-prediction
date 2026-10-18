import React from 'react';
import type { AnalysisResponse } from '../types';
import { TrendingUp, TrendingDown, MinusCircle, ShieldCheck, Target, Zap } from 'lucide-react';

interface SignalCardProps {
  analysis: AnalysisResponse | null;
  loading: boolean;
}

export const SignalCard: React.FC<SignalCardProps> = ({ analysis, loading }) => {
  if (loading && !analysis) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', minHeight: '260px' }}>
        <div style={{ color: 'var(--text-secondary)' }}>Menganalisis pola pasar dengan Machine Learning...</div>
      </div>
    );
  }

  if (!analysis) return null;

  const isBuy = analysis.signal === 'BUY';
  const isSell = analysis.signal === 'SELL';
  const color = isBuy ? 'var(--color-buy)' : isSell ? 'var(--color-sell)' : 'var(--color-warning)';
  const glow = isBuy ? 'var(--color-buy-glow)' : isSell ? 'var(--color-sell-glow)' : 'rgba(245, 158, 11, 0.2)';

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        borderLeft: `4px solid ${color}`,
        boxShadow: `0 10px 30px ${glow}`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={20} color={color} />
          <span style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
            AI ML Signal Detection
          </span>
        </div>
        <span
          style={{
            fontSize: '12px',
            padding: '4px 10px',
            borderRadius: '20px',
            backgroundColor: 'rgba(255,255,255,0.06)',
            color: 'var(--text-secondary)',
          }}
        >
          {analysis.style.toUpperCase()}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '16px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {isBuy && <TrendingUp size={36} color={color} />}
          {isSell && <TrendingDown size={36} color={color} />}
          {!isBuy && !isSell && <MinusCircle size={36} color={color} />}
          <span style={{ fontSize: '36px', fontWeight: 800, color: color, letterSpacing: '1px' }}>
            {analysis.signal}
          </span>
        </div>
        <div style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>
          Confidence: <strong style={{ color: '#fff' }}>{analysis.confidence}%</strong>
        </div>
      </div>

      {/* Probability Gauge Bar */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px', color: 'var(--text-muted)' }}>
          <span>BUY: {analysis.prob_buy}%</span>
          <span>SELL: {analysis.prob_sell}%</span>
        </div>
        <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
          <div style={{ width: `${analysis.prob_buy}%`, background: 'var(--color-buy)', transition: 'width 0.4s ease' }} />
          <div style={{ width: `${analysis.prob_sell}%`, background: 'var(--color-sell)', transition: 'width 0.4s ease' }} />
        </div>
      </div>

      {/* Target TP / SL Info */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--color-buy)', marginBottom: '4px' }}>
            <Target size={14} /> TAKE PROFIT
          </div>
          <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
            {analysis.take_profit ? analysis.take_profit.toFixed(5) : '-'}
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--color-sell)', marginBottom: '4px' }}>
            <ShieldCheck size={14} /> STOP LOSS
          </div>
          <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
            {analysis.stop_loss ? analysis.stop_loss.toFixed(5) : '-'}
          </div>
        </div>
      </div>

      {/* Market Regime badge & AI Advisor brief */}
      <div style={{ fontSize: '13px', background: 'rgba(59, 130, 246, 0.08)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-glow)' }}>
        <div style={{ fontWeight: 600, color: 'var(--color-accent)', marginBottom: '4px' }}>
          Regime: {analysis.regime.trend_name} • {analysis.regime.volatility_name}
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.5 }}>
          {analysis.advisor_insight}
        </div>
      </div>
    </div>
  );
};
