import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ScannerPanel } from './components/ScannerPanel';
import { StockAnalysisView } from './components/StockAnalysisView';
import { PaperJournal } from './components/PaperJournal';
import { BacktestView } from './components/BacktestView';
import { SwingTradeFinder } from './components/SwingTradeFinder';
import { api } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('scanner');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('RELIANCE');
  const [selectedMode, setSelectedMode] = useState<'INTRADAY' | 'SWING'>('INTRADAY');
  const [marketSession, setMarketSession] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [planningMode, setPlanningMode] = useState<boolean>(false);
  const [liveSignalAlert, setLiveSignalAlert] = useState<any>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      const data = await api.getMarketStatus(planningMode);
      setMarketSession(data);
      
      const health = await api.getSystemHealth();
      setSystemHealth(health);
    };
    fetchStatus();

    // Subscribe to real-time WebSocket signals
    const disconnectWs = api.connectSignalWebSocket((signalData) => {
      console.log('🚨 Live Signal Alert Received:', signalData);
      setLiveSignalAlert(signalData);
      setTimeout(() => setLiveSignalAlert(null), 10000); // Auto hide after 10s
    });

    return () => disconnectWs();
  }, [planningMode]);

  const handleSelectSymbol = (symbol: string, mode: 'INTRADAY' | 'SWING') => {
    setSelectedSymbol(symbol);
    setSelectedMode(mode);
    setActiveTab('analysis');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#070A0F] text-slate-100 font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        marketSession={marketSession}
        planningMode={planningMode}
        setPlanningMode={setPlanningMode}
        systemHealth={systemHealth}
      />

      {liveSignalAlert && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/30 text-emerald-400 px-4 py-3 text-center text-sm font-semibold flex items-center justify-center space-x-3 animate-pulse">
          <span>🚨 LIVE SIGNAL ALERT:</span>
          <span>{liveSignalAlert.symbol} ({liveSignalAlert.direction}) - {liveSignalAlert.setup_type} | Confidence: {liveSignalAlert.confidence}%</span>
          <button
            onClick={() => handleSelectSymbol(liveSignalAlert.symbol, liveSignalAlert.mode || 'INTRADAY')}
            className="ml-4 px-3 py-1 bg-emerald-500 text-slate-950 font-bold rounded text-xs hover:bg-emerald-400"
          >
            Inspect Analysis
          </button>
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'scanner' && <ScannerPanel onSelectSymbol={handleSelectSymbol} />}
        {activeTab === 'swing_finder' && <SwingTradeFinder onSelectSymbol={handleSelectSymbol} />}
        {activeTab === 'analysis' && <StockAnalysisView symbol={selectedSymbol} mode={selectedMode} />}
        {activeTab === 'journal' && <PaperJournal />}
        {activeTab === 'backtest' && <BacktestView />}
      </main>

      <footer className="border-t border-slate-800/80 bg-[#0A0E17]/60 py-4 text-center text-xs font-mono text-slate-500">
        HARSH TRADER AI — Production-Grade Multi-Agent Indian Stock Market Intelligence Platform (NSE/BSE)
      </footer>
    </div>
  );
};

export default App;
