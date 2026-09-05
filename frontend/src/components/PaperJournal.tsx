import React, { useState, useEffect } from 'react';
import { PaperTradeItem } from '../types';
import { api } from '../services/api';
import { BookOpen, TrendingUp, TrendingDown, DollarSign, Clock, RefreshCw, XCircle, Shield, CheckCircle } from 'lucide-react';

export const PaperJournal: React.FC = () => {
  const [journal, setJournal] = useState<{
    total_trades: number;
    total_realized_pnl_inr: number;
    win_rate_pct: number;
    trades: PaperTradeItem[];
  }>({ total_trades: 0, total_realized_pnl_inr: 0, win_rate_pct: 0, trades: [] });
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchJournal = async () => {
    setLoading(true);
    try {
      const data = await api.getJournal();
      setJournal(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJournal();
  }, []);

  const handleCloseTrade = async (tradeId: string) => {
    try {
      const res = await api.closePaperTrade(tradeId, undefined, 'MANUAL_CLOSE');
      setActionMessage(`Trade closed at ₹${res.exit_price} | P&L: ₹${res.realized_pnl}`);
      setTimeout(() => setActionMessage(null), 5000);
      await fetchJournal();
    } catch (e: any) {
      alert(`Failed to close trade: ${e?.response?.data?.detail || e.message}`);
    }
  };

  const handleMoveBreakeven = async (tradeId: string, entryPrice: number) => {
    try {
      await api.updateStopLoss(tradeId, entryPrice);
      setActionMessage(`Stop Loss moved to Breakeven (₹${entryPrice})`);
      setTimeout(() => setActionMessage(null), 5000);
      await fetchJournal();
    } catch (e: any) {
      alert(`Failed to update stop loss: ${e?.response?.data?.detail || e.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'OPEN') {
      return <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 text-[10px] font-bold font-mono">OPEN</span>;
    }
    if (status.startsWith('PARTIAL')) {
      return <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] font-bold font-mono">{status}</span>;
    }
    if (status === 'CLOSED_TP') {
      return <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold font-mono">CLOSED (TP)</span>;
    }
    if (status === 'CLOSED_SL') {
      return <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30 text-[10px] font-bold font-mono">CLOSED (SL)</span>;
    }
    return <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-bold font-mono">{status}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Top Header Summary */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-mono text-slate-100">PAPER TRADING JOURNAL & POSITION MONITOR</h2>
            <p className="text-xs text-slate-400">Real-time fill execution, multi-target scale outs (TP1/TP2/TP3), and automated risk trailing</p>
          </div>
        </div>

        <button
          onClick={fetchJournal}
          className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-cyan-400 border border-slate-700 transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {actionMessage && (
        <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-cyan-400" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-xl border border-slate-800 font-mono">
          <div className="text-xs text-slate-400">TOTAL PAPER TRADES</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{journal.total_trades}</div>
        </div>
        <div className="glass-card p-5 rounded-xl border border-slate-800 font-mono">
          <div className="text-xs text-slate-400">WIN RATE</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{journal.win_rate_pct}%</div>
        </div>
        <div className="glass-card p-5 rounded-xl border border-slate-800 font-mono">
          <div className="text-xs text-slate-400">REALIZED NET P&L</div>
          <div
            className={`text-2xl font-bold mt-1 ${
              journal.total_realized_pnl_inr >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            ₹{journal.total_realized_pnl_inr.toLocaleString('en-IN')}
          </div>
        </div>
      </div>

      {/* Trade Log Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        {journal.trades.length === 0 ? (
          <div className="py-16 text-center text-sm font-mono text-slate-400">
            No paper trades logged yet. Run analysis and click "PAPER TRADE NOW".
          </div>
        ) : (
          <div className="overflow-x-auto font-mono text-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/80 border-b border-slate-800 text-slate-400 text-[11px]">
                  <th className="p-3.5">SYMBOL</th>
                  <th className="p-3.5">DIR / MODE</th>
                  <th className="p-3.5">ENTRY</th>
                  <th className="p-3.5">QTY (REM)</th>
                  <th className="p-3.5">STOP LOSS</th>
                  <th className="p-3.5">TARGETS</th>
                  <th className="p-3.5">STATUS</th>
                  <th className="p-3.5">REALIZED P&L</th>
                  <th className="p-3.5">R MULT</th>
                  <th className="p-3.5 text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {journal.trades.map((t) => {
                  const isOpen = !t.status.startsWith('CLOSED') && t.status !== 'CANCELLED';
                  return (
                    <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3.5 font-bold text-slate-100">{t.symbol}</td>
                      <td className="p-3.5">
                        <span className={`font-semibold ${t.direction === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {t.direction}
                        </span>
                        <span className="text-slate-500 ml-1.5 text-[10px]">({t.mode})</span>
                      </td>
                      <td className="p-3.5 text-slate-200 font-semibold">₹{t.entry_price}</td>
                      <td className="p-3.5 text-slate-200">
                        {t.remaining_quantity !== undefined && t.remaining_quantity !== null ? t.remaining_quantity : t.quantity} / {t.quantity}
                      </td>
                      <td className="p-3.5 text-rose-400 font-semibold">
                        ₹{t.trailing_stop || t.stop_loss}
                      </td>
                      <td className="p-3.5 text-emerald-400 text-[11px]">
                        <div>T1: ₹{t.target_1}</div>
                        {t.target_2 && <div className="text-slate-400 text-[10px]">T2: ₹{t.target_2}</div>}
                      </td>
                      <td className="p-3.5">
                        {getStatusBadge(t.status)}
                      </td>
                      <td className={`p-3.5 font-bold ${(t.realized_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        ₹{t.realized_pnl !== undefined && t.realized_pnl !== null ? t.realized_pnl : 0.0}
                      </td>
                      <td className="p-3.5 font-semibold text-cyan-400">{t.r_multiple ? `${t.r_multiple}R` : '0R'}</td>
                      <td className="p-3.5 text-right space-x-1.5">
                        {isOpen ? (
                          <>
                            <button
                              onClick={() => handleMoveBreakeven(t.id, t.entry_price)}
                              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px] font-semibold border border-slate-700 transition-all"
                              title="Move Stop Loss to Breakeven"
                            >
                              SET BE
                            </button>
                            <button
                              onClick={() => handleCloseTrade(t.id)}
                              className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500 text-rose-300 hover:text-black rounded text-[10px] font-bold border border-rose-500/30 transition-all"
                            >
                              CLOSE
                            </button>
                          </>
                        ) : (
                          <span className="text-slate-500 text-[10px]">
                            {t.exit_reason || 'CLOSED'} @ ₹{t.exit_price || '-'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
