import React, { useState, useEffect } from 'react';
import { CandidateItem } from '../types';
import { api } from '../services/api';
import { Search, TrendingUp, BarChart2, ShieldCheck, Zap, RefreshCw, ArrowUpRight } from 'lucide-react';

interface ScannerPanelProps {
  onSelectSymbol: (symbol: string, mode: 'INTRADAY' | 'SWING') => void;
}

export const ScannerPanel: React.FC<ScannerPanelProps> = ({ onSelectSymbol }) => {
  const [mode, setMode] = useState<'INTRADAY' | 'SWING'>('INTRADAY');
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchFilter, setSearchFilter] = useState<string>('');

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      if (mode === 'INTRADAY') {
        const data = await api.getIntradayCandidates();
        setCandidates(data);
      } else {
        const data = await api.getSwingCandidates();
        setCandidates(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [mode]);

  const filteredCandidates = candidates.filter((c) =>
    c.symbol.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Scanner Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-4 rounded-xl">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 tracking-wide font-mono">
              REAL-TIME CANDIDATE SCANNER
            </h2>
            <p className="text-xs text-slate-400">
              Filtered against volume, volatility, VWAP & quality gates
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Mode Switcher */}
          <div className="flex bg-[#070A0F] p-1 rounded-lg border border-slate-800 font-mono text-xs">
            <button
              onClick={() => setMode('INTRADAY')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                mode === 'INTRADAY'
                  ? 'bg-cyan-500 text-black font-bold shadow-md shadow-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              INTRADAY (5m / 15m)
            </button>
            <button
              onClick={() => setMode('SWING')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                mode === 'SWING'
                  ? 'bg-cyan-500 text-black font-bold shadow-md shadow-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              SWING (Daily / 4H)
            </button>
          </div>

          <button
            onClick={fetchCandidates}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-cyan-400 hover:bg-slate-700 transition-all border border-slate-700"
            title="Refresh candidates"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
        <input
          type="text"
          placeholder="Search symbol (e.g., RELIANCE, TCS, INFY)..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="w-full bg-[#0D111A] border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-mono"
        />
      </div>

      {/* Candidates Grid */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-sm font-mono text-slate-400">Scanning NSE market universe...</p>
        </div>
      ) : filteredCandidates.length === 0 ? (
        <div className="py-16 text-center glass-panel rounded-xl">
          <p className="text-sm font-mono text-slate-400">No candidates matched the scanner thresholds.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCandidates.map((candidate) => (
            <div
              key={candidate.symbol}
              className="glass-card rounded-xl p-5 flex flex-col justify-between space-y-4 relative group border border-slate-800 hover:border-cyan-500/40"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-bold font-mono text-lg text-slate-100 tracking-wider">
                      {candidate.symbol}
                    </span>
                    <span className="ml-2 px-2 py-0.5 text-[10px] font-mono rounded bg-slate-800 text-slate-400 border border-slate-700">
                      NSE
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-base font-bold font-mono text-cyan-400">
                      ₹{candidate.last_price.toLocaleString('en-IN')}
                    </div>
                    <div className="text-[10px] font-mono text-slate-400">Score: {candidate.scanner_score}/100</div>
                  </div>
                </div>

                <div className="mt-3 inline-block px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-xs font-mono font-medium">
                  {candidate.setup_name}
                </div>

                {/* Metrics */}
                <div className="mt-4 grid grid-cols-3 gap-2 text-center font-mono text-xs bg-[#070A0F]/60 p-2.5 rounded-lg border border-slate-800/80">
                  <div>
                    <div className="text-[10px] text-slate-500">RSI (14)</div>
                    <div className="font-semibold text-slate-200">{candidate.rsi}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">VWAP</div>
                    <div className="font-semibold text-slate-200">
                      {candidate.vwap ? `₹${candidate.vwap}` : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">RVOL</div>
                    <div className="font-semibold text-emerald-400">
                      {candidate.rvol ? `${candidate.rvol}x` : '1.0x'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Data Quality Pill & Action */}
              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                <div className="flex items-center space-x-1 text-[11px] font-mono text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>DQ Score: {candidate.data_quality_score}%</span>
                </div>

                <button
                  onClick={() => onSelectSymbol(candidate.symbol, mode)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500 text-cyan-300 hover:text-black font-mono font-bold text-xs flex items-center space-x-1 transition-all"
                >
                  <span>RUN AGENT DEBATE</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
