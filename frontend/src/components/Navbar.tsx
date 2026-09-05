import React from 'react';
import { ShieldCheck, Activity, Cpu, AlertTriangle, Clock, Play } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  marketSession: any;
  planningMode: boolean;
  setPlanningMode: (val: boolean) => void;
  systemHealth: any;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  marketSession,
  planningMode,
  setPlanningMode,
  systemHealth,
}) => {
  const isMarketOpen = marketSession?.status === 'OPEN';

  return (
    <header className="border-b border-slate-800 bg-[#0A0E17]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 via-emerald-500 to-indigo-600 p-[1.5px] flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <div className="w-full h-full bg-[#0D111A] rounded-[7px] flex items-center justify-center">
                <Cpu className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-slate-100 via-cyan-200 to-cyan-400 bg-clip-text text-transparent">
                  HARSH TRADER AI
                </span>
                <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  v1.0 PROD
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                NSE/BSE Multi-Agent Trading Intelligence
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex space-x-1 font-medium text-xs font-mono">
            {[
              { id: 'scanner', label: 'CANDIDATE SCANNER' },
              { id: 'swing_finder', label: '⚡ SWING 30%+ HUNTER' },
              { id: 'analysis', label: 'STOCK ANALYSIS' },
              { id: 'journal', label: 'PAPER JOURNAL' },
              { id: 'backtest', label: 'BACKTESTING' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-2 rounded-md transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Right Status Controls */}
          <div className="flex items-center space-x-3">
            {/* Provider Badge */}
            {systemHealth?.provider && systemHealth.provider !== 'MOCK_NSE_PROVIDER' ? (
              <div className="px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center space-x-1.5 animate-pulse">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-[11px] font-mono font-semibold text-emerald-400">
                  {systemHealth.provider} DATA
                </span>
              </div>
            ) : (
              <div className="px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-[11px] font-mono font-semibold text-amber-400">
                  MOCK DATA MODE
                </span>
              </div>
            )}

            {/* Session Indicator */}
            <div className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 flex items-center space-x-2 text-xs font-mono">
              <div className={`w-2 h-2 rounded-full ${isMarketOpen ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300">{marketSession?.status || 'OPEN'}</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400 text-[10px]">IST</span>
            </div>

            {/* Planning Mode Toggle */}
            <button
              onClick={() => setPlanningMode(!planningMode)}
              className={`px-2.5 py-1 rounded-md text-xs font-mono flex items-center space-x-1 transition-all ${
                planningMode
                  ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
              title="Toggle explicit next-session planning mode when market is closed"
            >
              <Clock className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">PLANNING MODE</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
