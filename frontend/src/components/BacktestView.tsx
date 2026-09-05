import React, { useState } from 'react';
import { api } from '../services/api';
import { Play, LineChart, ShieldCheck, Award, AlertOctagon } from 'lucide-react';

export const BacktestView: React.FC = () => {
  const [symbol, setSymbol] = useState<string>('RELIANCE');
  const [mode, setMode] = useState<'INTRADAY' | 'SWING'>('INTRADAY');
  const [capital, setCapital] = useState<number>(100000);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      const data = await api.runBacktest(symbol, mode, capital);
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <LineChart className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-mono text-slate-100">EVENT-DRIVEN BACKTESTING ENGINE</h2>
            <p className="text-xs text-slate-400">Enforces zero look-ahead bias, slippage, STT, and exchange fee math</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 font-mono text-xs">
          <div>
            <label className="text-slate-400 block mb-1">Target Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full bg-[#070A0F] border border-slate-800 rounded-lg p-2 text-slate-100 font-bold"
            />
          </div>
          <div>
            <label className="text-slate-400 block mb-1">Timeframe Mode</label>
            <select
              value={mode}
              onChange={(e: any) => setMode(e.target.value)}
              className="w-full bg-[#070A0F] border border-slate-800 rounded-lg p-2 text-slate-100"
            >
              <option value="INTRADAY">INTRADAY (15m)</option>
              <option value="SWING">SWING (1D)</option>
            </select>
          </div>
          <div>
            <label className="text-slate-400 block mb-1">Initial Capital (INR)</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              className="w-full bg-[#070A0F] border border-slate-800 rounded-lg p-2 text-slate-100"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleRunBacktest}
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-bold flex items-center justify-center space-x-2 transition-all shadow-md shadow-cyan-500/20"
            >
              <Play className="w-4 h-4 fill-black" />
              <span>{loading ? 'RUNNING...' : 'RUN BACKTEST'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
            <div className="glass-card p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">WIN RATE</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">{result.win_rate_pct}%</div>
              <div className="text-[10px] text-slate-500 mt-1">{result.winning_trades} / {result.total_trades} wins</div>
            </div>
            <div className="glass-card p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">PROFIT FACTOR</div>
              <div className="text-2xl font-bold text-cyan-400 mt-1">{result.profit_factor}</div>
              <div className="text-[10px] text-slate-500 mt-1">Gross Win / Gross Loss</div>
            </div>
            <div className="glass-card p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">NET P&L (INR)</div>
              <div className={`text-2xl font-bold mt-1 ${result.net_pnl_inr >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                ₹{result.net_pnl_inr.toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">After charges: ₹{result.total_charges_inr}</div>
            </div>
            <div className="glass-card p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">MAX DRAWDOWN</div>
              <div className="text-2xl font-bold text-rose-400 mt-1">{result.max_drawdown_pct}%</div>
              <div className="text-[10px] text-slate-500 mt-1">Peak-to-trough risk</div>
            </div>
          </div>

          {/* Secondary Ratios */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-4 text-center font-mono text-xs">
            <div>
              <div className="text-slate-400">AVG R MULTIPLE</div>
              <div className="font-bold text-slate-100 text-sm mt-0.5">{result.average_r_multiple}R</div>
            </div>
            <div>
              <div className="text-slate-400">EXPECTANCY / TRADE</div>
              <div className="font-bold text-emerald-400 text-sm mt-0.5">₹{result.expectancy_inr}</div>
            </div>
            <div>
              <div className="text-slate-400">SHARPE RATIO</div>
              <div className="font-bold text-cyan-400 text-sm mt-0.5">{result.sharpe_ratio}</div>
            </div>
            <div>
              <div className="text-slate-400">SORTINO RATIO</div>
              <div className="font-bold text-cyan-400 text-sm mt-0.5">{result.sortino_ratio}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
