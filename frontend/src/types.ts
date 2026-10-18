export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketDataResponse {
  pair: string;
  timeframe: string;
  latest_price: number;
  price_change: number;
  price_change_pct: number;
  candles: Candle[];
}

export interface PairItem {
  symbol: string;
  name: string;
  pip_decimal: number;
  pip_value: number;
}

export interface MarketRegime {
  trend_name: string;
  trend_code: number;
  trend_desc: string;
  volatility_name: string;
  volatility_desc: string;
  recommendation: string;
}

export interface TechnicalIndicators {
  rsi: number | null;
  macd: number | null;
  macd_signal: number | null;
  adx: number | null;
  atr: number;
}

export interface AnalysisResponse {
  pair: string;
  timeframe: string;
  style: string;
  current_price: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  prob_buy: number;
  prob_sell: number;
  stop_loss: number | null;
  take_profit: number | null;
  risk_reward_ratio: number;
  regime: MarketRegime;
  indicators: TechnicalIndicators;
  advisor_insight: string;
  locked_signal?: any;
}

export interface PaperTrade {
  ticket_id: number;
  symbol: string;
  direction: 'BUY' | 'SELL';
  lot_size: number;
  entry_price: number;
  entry_time: string;
  stop_loss: number;
  take_profit: number;
  strategy?: string;
  status: string;
  exit_price?: number;
  exit_time?: string;
  pnl_cash?: number;
  pnl_pips?: number;
}

export interface PaperAccountResponse {
  balance: number;
  open_positions: PaperTrade[];
  closed_positions: PaperTrade[];
  total_trades: number;
}

export interface BacktestResult {
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  total_pnl: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
}
