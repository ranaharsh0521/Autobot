import axios from 'axios';
import { MarketQuote, CandidateItem, AnalysisDecision, PaperTradeItem } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = {
  getSystemHealth: async () => {
    try {
      const res = await axios.get(`${API_BASE}/system/health`);
      return res.data;
    } catch (e) {
      return { status: 'HEALTHY', environment: 'development', provider: 'MOCK_NSE_PROVIDER' };
    }
  },

  getMarketStatus: async (planningMode = false) => {
    try {
      const res = await axios.get(`${API_BASE}/market/status?planning_mode=${planningMode}`);
      return res.data;
    } catch (e) {
      return { status: 'OPEN', timestamp: new Date().toISOString(), timezone: 'Asia/Kolkata', can_execute_intraday: true };
    }
  },

  getQuote: async (symbol: string): Promise<MarketQuote> => {
    const res = await axios.get(`${API_BASE}/market/quote/${symbol}`);
    return res.data;
  },

  getIntradayCandidates: async (symbols?: string): Promise<CandidateItem[]> => {
    const url = symbols ? `${API_BASE}/scanner/intraday?symbols=${symbols}` : `${API_BASE}/scanner/intraday`;
    const res = await axios.get(url);
    return res.data;
  },

  getSwingCandidates: async (symbols?: string): Promise<CandidateItem[]> => {
    const url = symbols ? `${API_BASE}/scanner/swing?symbols=${symbols}` : `${API_BASE}/scanner/swing`;
    const res = await axios.get(url);
    return res.data;
  },

  scanAiSwingSetups: async (apiKey?: string): Promise<any[]> => {
    const res = await axios.post(`${API_BASE}/scanner/ai-swing`, { api_key: apiKey });
    return res.data;
  },

  analyzeSymbol: async (symbol: string, mode: 'INTRADAY' | 'SWING', capital = 100000, riskPct = 1.0): Promise<AnalysisDecision> => {
    const res = await axios.post(`${API_BASE}/analyze/${symbol}?mode=${mode}&capital=${capital}&risk_pct=${riskPct}`);
    return res.data;
  },

  getJournal: async () => {
    try {
      const res = await axios.get(`${API_BASE}/journal`);
      return res.data;
    } catch (e) {
      return { total_trades: 0, total_realized_pnl_inr: 0, win_rate_pct: 0, trades: [] };
    }
  },

  executePaperTrade: async (trade: {
    symbol: string;
    direction: 'BUY' | 'SELL';
    mode: 'INTRADAY' | 'SWING';
    entry_price: number;
    quantity: number;
    stop_loss: number;
    target_1: number;
    target_2?: number;
    target_3?: number;
  }) => {
    const res = await axios.post(`${API_BASE}/paper-trade`, null, { params: trade });
    return res.data;
  },

  closePaperTrade: async (tradeId: string, exitPrice?: number, exitReason = 'MANUAL_CLOSE') => {
    const res = await axios.post(`${API_BASE}/paper-trade/${tradeId}/close`, {
      exit_price: exitPrice,
      exit_reason: exitReason
    });
    return res.data;
  },

  updateStopLoss: async (tradeId: string, newStopLoss: number) => {
    const res = await axios.post(`${API_BASE}/paper-trade/${tradeId}/stop-loss`, {
      new_stop_loss: newStopLoss,
      reason: 'MANUAL_ADJUSTMENT'
    });
    return res.data;
  },

  runBacktest: async (symbol: string, mode: 'INTRADAY' | 'SWING', capital = 100000) => {
    const res = await axios.post(`${API_BASE}/backtests?symbol=${symbol}&mode=${mode}&capital=${capital}`);
    return res.data;
  },

  sendTestNotification: async (symbol: string) => {
    const res = await axios.post(`${API_BASE}/notifications/test?symbol=${symbol}`);
    return res.data;
  },

  connectSignalWebSocket: (onSignalReceived: (signal: any) => void) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Explicit environment variable or fallback
    let wsUrl: string;
    if (import.meta.env.VITE_WS_BASE_URL) {
      wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/signals`;
    } else if (window.location.port === '5173' || window.location.port === '3000') {
      wsUrl = `${protocol}//${window.location.hostname}:8000/ws/signals`;
    } else {
      wsUrl = `${protocol}//${window.location.host}/ws/signals`;
    }
    
    let ws: WebSocket | null = null;
    let reconnectTimer: any = null;
    let isUnmounted = false;

    const connect = () => {
      if (isUnmounted) return;
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('🟢 [WebSocket] Connected to real-time signals feed');
        };

        ws.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload.type === 'NEW_SIGNAL' || payload.type === 'SYSTEM_STATUS') {
              onSignalReceived(payload.data || payload);
            }
          } catch (e) {
            console.error('[WebSocket] Error parsing message payload:', e);
          }
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            console.warn('🔴 [WebSocket] Connection closed. Reconnecting in 5s...');
            reconnectTimer = setTimeout(connect, 5000);
          }
        };

        ws.onerror = () => {
          console.warn('[WebSocket] Transport issue encountered. Will retry automatically.');
        };
      } catch (e) {
        if (!isUnmounted) {
          reconnectTimer = setTimeout(connect, 5000);
        }
      }
    };

    connect();

    return () => {
      isUnmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.onerror = null;
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            try {
              ws?.close();
            } catch (e) {
              // Ignore clean close exceptions
            }
          };
        } else if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.close();
          } catch (e) {
            // Ignore clean close exceptions
          }
        }
      }
    };
  }
};
