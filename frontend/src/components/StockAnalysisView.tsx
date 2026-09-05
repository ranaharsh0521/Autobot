import React, { useState, useEffect } from 'react';
import { AnalysisDecision } from '../types';
import { api } from '../services/api';
import {
  ShieldCheck,
  AlertTriangle,
  Play,
  Cpu,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  Send,
  MessageSquare
} from 'lucide-react';

interface StockAnalysisViewProps {
  symbol: string;
  mode: 'INTRADAY' | 'SWING';
}

export const StockAnalysisView: React.FC<StockAnalysisViewProps> = ({ symbol, mode }) => {
  const [decision, setDecision] = useState<AnalysisDecision | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [executingTrade, setExecutingTrade] = useState<boolean>(false);
  const [tradeSuccess, setTradeSuccess] = useState<string | null>(null);
  const [whatsappSent, setWhatsappSent] = useState<boolean>(false);

  const runFullAnalysis = async () => {
    setLoading(true);
    setTradeSuccess(null);
    try {
      const data = await api.analyzeSymbol(symbol, mode);
      setDecision(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      runFullAnalysis();
    }
  }, [symbol, mode]);

  const handlePaperTrade = async () => {
    if (!decision || decision.decision !== 'TAKE_TRADE') return;
    setExecutingTrade(true);
    try {
      const res = await api.executePaperTrade({
        symbol: decision.symbol,
        direction: decision.direction,
        mode: decision.mode,
        entry_price: decision.entry_zone.min,
        quantity: decision.position_size,
        stop_loss: decision.stop_loss,
        target_1: decision.targets[0],
        target_2: decision.targets[1],
        target_3: decision.targets[2],
      });
      setTradeSuccess(`Paper order filled! Trade ID: ${res.trade_id || 'OPEN'}`);
    } catch (e) {
      console.error(e);
    } finally {
      setExecutingTrade(false);
    }
  };

  const handleWhatsAppAlert = async () => {
    if (!decision) return;
    try {
      await api.sendTestNotification(decision.symbol);
      setWhatsappSent(true);
      setTimeout(() => setWhatsappSent(false), 4000);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="py-28 text-center space-y-4">
        <Cpu className="w-10 h-10 text-cyan-400 animate-bounce mx-auto" />
        <div className="text-base font-mono text-slate-200">
          Running Multi-Agent Intelligence Engine for <span className="text-cyan-400 font-bold">{symbol}</span>...
        </div>
        <p className="text-xs font-mono text-slate-500 max-w-md mx-auto">
          Executing Technical, Price Action, Volume, Regime, News, Bull/Bear Evidence Debate & Risk Gates.
        </p>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="py-16 text-center glass-panel rounded-xl">
        <p className="text-sm font-mono text-slate-400">Analysis failed to complete. Please try again.</p>
      </div>
    );
  }

  const isTakeTrade = decision.decision === 'TAKE_TRADE';

  return (
    <div className="space-y-6">
      {/* Top Banner Decision Card */}
      <div
        className={`p-6 rounded-2xl border glass-panel flex flex-col md:flex-row items-start md:items-center justify-between gap-6 ${
          isTakeTrade
            ? 'border-emerald-500/40 bg-gradient-to-r from-emerald-950/30 via-slate-900/80 to-slate-900/80'
            : 'border-rose-500/40 bg-gradient-to-r from-rose-950/30 via-slate-900/80 to-slate-900/80'
        }`}
      >
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <span className="text-2xl font-bold font-mono text-slate-100">{decision.symbol}</span>
            <span className="px-2.5 py-0.5 text-xs font-mono font-bold rounded bg-slate-800 text-slate-300 border border-slate-700">
              NSE ({decision.mode})
            </span>

            {/* Decision Badge */}
            <div
              className={`px-3 py-1 rounded-md text-xs font-mono font-extrabold flex items-center space-x-1.5 ${
                isTakeTrade
                  ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
              }`}
            >
              {isTakeTrade ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              <span>{decision.decision}</span>
            </div>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Setup: <span className="text-cyan-400 font-semibold">{decision.setup_type}</span> | Direction:{' '}
            <span className={decision.direction === 'BUY' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
              {decision.direction}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleWhatsAppAlert}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold flex items-center space-x-2 border border-slate-700 transition-all"
          >
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            <span>{whatsappSent ? 'ALERT SENT!' : 'WHATSAPP ALERT'}</span>
          </button>

          {isTakeTrade && (
            <button
              onClick={handlePaperTrade}
              disabled={executingTrade}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-mono font-bold text-xs flex items-center space-x-2 shadow-lg shadow-emerald-500/20 transition-all"
            >
              <Play className="w-4 h-4 fill-black" />
              <span>{executingTrade ? 'EXECUTING...' : 'PAPER TRADE NOW'}</span>
            </button>
          )}
        </div>
      </div>

      {tradeSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-mono text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{tradeSuccess}</span>
        </div>
      )}

      {/* Reason Banner if NO_TRADE or Session Closed */}
      {decision.reason && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono text-xs flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
          <div>
            <div className="font-bold text-amber-200">ANALYSIS STATUS / SESSION REASON:</div>
            <div>{decision.reason}</div>
          </div>
        </div>
      )}

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Risk & Execution Parameters */}
        <div className="space-y-6">
          {/* Risk Gate Parameters */}
          <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold font-mono text-slate-200 tracking-wider flex items-center space-x-2 border-b border-slate-800 pb-3">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>DETERMINISTIC RISK GATE</span>
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Entry Zone</span>
                <span className="font-semibold text-slate-100">
                  {decision.entry_zone ? `₹${decision.entry_zone.min} - ₹${decision.entry_zone.max}` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Stop Loss</span>
                <span className="font-semibold text-rose-400">
                  {decision.stop_loss !== undefined ? `₹${decision.stop_loss}` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Target 1</span>
                <span className="font-semibold text-emerald-400">
                  {decision.targets?.[0] !== undefined ? `₹${decision.targets[0]}` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Target 2</span>
                <span className="font-semibold text-emerald-400">
                  {decision.targets?.[1] !== undefined ? `₹${decision.targets[1]}` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Target 3</span>
                <span className="font-semibold text-emerald-400">
                  {decision.targets?.[2] !== undefined ? `₹${decision.targets[2]}` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Risk/Reward Ratio</span>
                <span className="font-bold text-cyan-400">
                  {decision.risk_reward !== undefined ? `1:${decision.risk_reward}` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Recommended Size</span>
                <span className="font-bold text-slate-100">
                  {decision.position_size !== undefined ? `${decision.position_size} shares` : '0 shares'}
                </span>
              </div>
            </div>

            {(decision.failed_conditions?.length ?? 0) > 0 && (
              <div className="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px] font-mono space-y-1">
                <div className="font-bold flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>HARD REJECTION REASONS:</span>
                </div>
                {decision.failed_conditions.map((fc, idx) => (
                  <div key={idx} className="pl-4">• {fc}</div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Middle & Right Column: Bull vs Bear Debate & Evidence Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Bull vs Bear Case Synthesis */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Bull Case */}
            {decision.bull_case && (
              <div className="glass-panel p-4 rounded-xl border border-emerald-500/30 space-y-2">
                <div className="text-xs font-bold font-mono text-emerald-400 tracking-wider flex items-center space-x-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>BULL CASE THESIS</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">{decision.bull_case}</p>
              </div>
            )}

            {/* Bear Case */}
            {decision.bear_case && (
              <div className="glass-panel p-4 rounded-xl border border-rose-500/30 space-y-2">
                <div className="text-xs font-bold font-mono text-rose-400 tracking-wider flex items-center space-x-1">
                  <AlertTriangle className="w-4 h-4" />
                  <span>BEAR CASE CHALLENGE</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">{decision.bear_case}</p>
              </div>
            )}
          </div>

          {/* 3-Round Debate Log */}
          {decision.debate && (
            <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold font-mono text-slate-200 tracking-wider border-b border-slate-800 pb-3 flex items-center justify-between">
                <span>EVIDENCE-BASED DEBATE LOG (3 ROUNDS)</span>
                <span className="text-xs font-normal text-cyan-400">Score: {decision.debate.debate_score}/100</span>
              </h3>

              <div className="space-y-4">
                {decision.debate.rounds.map((rnd) => (
                  <div key={rnd.round} className="p-3.5 rounded-lg bg-[#070A0F]/70 border border-slate-800/80 space-y-2 text-xs">
                    <div className="font-mono font-bold text-cyan-400 text-[11px]">ROUND {rnd.round}</div>
                    {rnd.bull_claim && (
                      <div className="text-slate-300">
                        <strong className="text-emerald-400 font-mono">Bull:</strong> {rnd.bull_claim}
                      </div>
                    )}
                    {rnd.bear_challenge && (
                      <div className="text-slate-300">
                        <strong className="text-rose-400 font-mono">Bear:</strong> {rnd.bear_challenge}
                      </div>
                    )}
                    {rnd.bull_rebuttal && (
                      <div className="text-slate-300">
                        <strong className="text-emerald-400 font-mono">Bull Rebuttal:</strong> {rnd.bull_rebuttal}
                      </div>
                    )}
                    {rnd.bear_rebuttal && (
                      <div className="text-slate-300">
                        <strong className="text-rose-400 font-mono">Bear Rebuttal:</strong> {rnd.bear_rebuttal}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* WHY? Evidence Tracing Panel */}
          {(decision.evidence_ids?.length ?? 0) > 0 && (
            <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold font-mono text-slate-200 tracking-wider border-b border-slate-800 pb-3 flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-amber-400" />
                <span>WHY? (GROUNDED EVIDENCE TRACE)</span>
              </h3>

              <div className="space-y-2">
                {decision.evidence_ids.map((id, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-[#070A0F]/60 border border-slate-800 flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300">Evidence Reference `{id}`</span>
                    <span className="text-[10px] text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">VERIFIED DATA</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
