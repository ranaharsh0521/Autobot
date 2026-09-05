export interface MarketQuote {
  symbol: string;
  exchange: 'NSE' | 'BSE';
  last_price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
  bid?: number;
  ask?: number;
  upper_circuit?: number;
  lower_circuit?: number;
  metadata: {
    provider: string;
    retrieved_at: string;
    market_timestamp: string;
    timezone: string;
    data_status: 'FRESH' | 'STALE_DATA' | 'DATA_ERROR' | 'DATA_UNAVAILABLE';
    is_mock: boolean;
  };
}

export interface CandidateItem {
  symbol: string;
  mode: 'INTRADAY' | 'SWING';
  setup_name: string;
  scanner_score: number;
  last_price: number;
  rsi: number;
  vwap?: number;
  rvol?: number;
  data_quality_score: number;
  indicators: any;
}

export interface EvidenceItem {
  evidence_id: string;
  claim: string;
  evidence_type: string;
  metric_name: string;
  metric_value: string;
  source: string;
}

export interface DebateRound {
  round: number;
  bull_claim?: string;
  bull_evidence_ids?: string[];
  bear_challenge?: string;
  bear_evidence_ids?: string[];
  bull_rebuttal?: string;
  bear_rebuttal?: string;
  bull_self_critique?: string;
  bear_self_critique?: string;
}

export interface DebateResult {
  symbol: string;
  rounds: DebateRound[];
  strongest_bull_evidence: EvidenceItem[];
  strongest_bear_evidence: EvidenceItem[];
  unresolved_risks: string[];
  key_disagreement: string;
  invalidation_condition: string;
  debate_score: number;
}

export interface AnalysisDecision {
  decision: 'TAKE_TRADE' | 'NO_TRADE' | 'WATCH';
  symbol: string;
  exchange: string;
  direction: 'BUY' | 'SELL';
  mode: 'INTRADAY' | 'SWING';
  setup_type: string;
  entry_zone: { min: number; max: number };
  stop_loss: number;
  targets: number[];
  risk_reward: number;
  position_size: number;
  confidence: number;
  market_regime: string;
  bull_case: string;
  bear_case: string;
  invalidation: string;
  evidence_ids: string[];
  failed_conditions: string[];
  data_quality_score: number;
  timestamp: string;
  execution_id?: string;
  debate?: DebateResult;
  consensus?: any;
  reason?: string;
}

export interface PaperTradeItem {
  id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  mode: 'INTRADAY' | 'SWING';
  entry_price: number;
  quantity: number;
  remaining_quantity?: number;
  stop_loss: number;
  target_1: number;
  target_2?: number;
  target_3?: number;
  trailing_stop?: number;
  status: string;
  exit_price?: number;
  exit_reason?: string;
  realized_pnl?: number;
  unrealized_pnl?: number;
  r_multiple?: number;
  holding_time_mins?: number;
  opened_at: string;
  closed_at?: string;
}
