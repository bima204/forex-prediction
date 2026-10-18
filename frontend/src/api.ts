import axios from 'axios';
import type {
  MarketDataResponse,
  AnalysisResponse,
  PaperAccountResponse,
  BacktestResult,
  PairItem,
} from './types';

// Relative path automatically proxied by Vite dev server
const API_BASE_URL = '/api';

export const api = {
  async getPairs(): Promise<{ pairs: PairItem[]; timeframes: string[]; trading_styles: Record<string, any> }> {
    const res = await axios.get(`${API_BASE_URL}/pairs`);
    return res.data;
  },

  async getMarketData(pair: string, timeframe: string, limit = 250): Promise<MarketDataResponse> {
    const res = await axios.get(`${API_BASE_URL}/market/${pair}`, {
      params: { timeframe, limit },
    });
    return res.data;
  },

  async getAnalysis(pair: string, timeframe: string, style = 'daytrading'): Promise<AnalysisResponse> {
    const res = await axios.get(`${API_BASE_URL}/analysis/${pair}`, {
      params: { timeframe, style },
    });
    return res.data;
  },

  async getPaperAccount(): Promise<PaperAccountResponse> {
    const res = await axios.get(`${API_BASE_URL}/papertrade/account`);
    return res.data;
  },

  async executePaperOrder(data: {
    pair: string;
    action: 'BUY' | 'SELL';
    lots: number;
    stop_loss?: number | null;
    take_profit?: number | null;
    strategy?: string;
  }): Promise<{ status: string; position: any }> {
    const res = await axios.post(`${API_BASE_URL}/papertrade/order`, data);
    return res.data;
  },

  async closePaperOrder(ticket: number): Promise<{ status: string; trade: any }> {
    const res = await axios.post(`${API_BASE_URL}/papertrade/close/${ticket}`);
    return res.data;
  },

  async runBacktest(data: {
    pair: string;
    timeframe: string;
    initial_balance?: number;
    risk_pct?: number;
  }): Promise<BacktestResult> {
    const res = await axios.post(`${API_BASE_URL}/backtest`, data);
    return res.data;
  },
};
