import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class RiskAssessmentInput(BaseModel):
    symbol: str
    mode: str # INTRADAY | SWING
    direction: str # BUY | SELL
    current_price: float
    atr_14: float
    support_levels: List[float] = []
    resistance_levels: List[float] = []
    upper_circuit: Optional[float] = None
    lower_circuit: Optional[float] = None
    bid_ask_spread_pct: float = 0.05
    data_quality_score: float = 100.0
    user_capital: float = 100000.0
    risk_per_trade_pct: float = 1.0 # 1% risk per trade
    max_position_size_pct: float = 15.0 # Max 15% of portfolio in single trade
    is_market_session_valid: bool = True
    model_config = ConfigDict(extra="ignore")

class RiskAssessmentResult(BaseModel):
    passed: bool
    decision: str # TAKE_TRADE | NO_TRADE
    rejection_reason_code: Optional[str] = None
    entry_min: float
    entry_max: float
    stop_loss: float
    target_1: float
    target_2: float
    target_3: float
    risk_reward_ratio: float
    position_size_shares: int
    max_trade_risk_inr: float
    total_position_value_inr: float
    failed_conditions: List[str] = []
    model_config = ConfigDict(extra="ignore")

class RiskEngine:
    """
    100% Deterministic Risk & Position Sizing Engine.
    Enforces non-negotiable hard rejections across 7 mandatory gates.
    """

    def evaluate_trade_risk(self, input_data: RiskAssessmentInput) -> RiskAssessmentResult:
        failed_conditions = []
        rejection_code = None

        # Gate 1 — Data Quality Gate
        if input_data.data_quality_score < 85.0:
            failed_conditions.append(f"GATE_1_DATA_QUALITY_BELOW_THRESHOLD: Score ({input_data.data_quality_score}) below minimum (85.0)")
            if not rejection_code:
                rejection_code = "GATE_1_DATA_QUALITY_BELOW_THRESHOLD"

        # Gate 2 — Market Session Gate
        if not input_data.is_market_session_valid:
            failed_conditions.append("GATE_2_MARKET_SESSION_INVALID: Session closed or execution restricted for Asia/Kolkata timezone")
            if not rejection_code:
                rejection_code = "GATE_2_MARKET_SESSION_INVALID"

        # Gate 4 — Valid Entry Price Gate
        curr = input_data.current_price
        if curr <= 0:
            failed_conditions.append("GATE_4_INVALID_ENTRY_PRICE: Current price must be greater than zero")
            if not rejection_code:
                rejection_code = "GATE_4_INVALID_ENTRY_PRICE"

        # Gate 7 — Liquidity & Spread Gate
        if input_data.bid_ask_spread_pct > 0.3:
            failed_conditions.append(f"GATE_7_LIQUIDITY_SPREAD_EXCEEDED: Spread ({round(input_data.bid_ask_spread_pct, 2)}%) exceeds limit (0.3%)")
            if not rejection_code:
                rejection_code = "GATE_7_LIQUIDITY_SPREAD_EXCEEDED"

        atr = max(input_data.atr_14, curr * 0.005) # Minimum ATR floor

        # Gate 5 & Gate 6 — Deterministic Entry, Stop Loss, and Targets
        if input_data.direction == "BUY":
            entry_min = round(curr * 0.999, 2)
            entry_max = round(curr * 1.001, 2)
            entry_mid = round(curr, 2)

            valid_supports = [s for s in input_data.support_levels if s < entry_mid]
            pivot_sl = max(valid_supports) if valid_supports else (entry_mid - 1.5 * atr)
            stop_loss = round(max(pivot_sl, entry_mid - 2.5 * atr), 2)
            sl_distance = entry_mid - stop_loss

            if sl_distance <= 0 or sl_distance / entry_mid < 0.003:
                failed_conditions.append(f"GATE_5_INVALID_STOP_LOSS: Invalid or tight Stop Loss distance (₹{round(sl_distance, 2)})")
                if not rejection_code:
                    rejection_code = "GATE_5_INVALID_STOP_LOSS"

            target_1 = round(entry_mid + (2.0 * sl_distance), 2)
            target_2 = round(entry_mid + (3.0 * sl_distance), 2)
            target_3 = round(entry_mid + (4.5 * sl_distance), 2)

        else: # SELL / SHORT
            entry_min = round(curr * 0.999, 2)
            entry_max = round(curr * 1.001, 2)
            entry_mid = round(curr, 2)

            valid_resistances = [r for r in input_data.resistance_levels if r > entry_mid]
            pivot_sl = min(valid_resistances) if valid_resistances else (entry_mid + 1.5 * atr)
            stop_loss = round(min(pivot_sl, entry_mid + 2.5 * atr), 2)
            sl_distance = stop_loss - entry_mid

            if sl_distance <= 0 or sl_distance / entry_mid < 0.003:
                failed_conditions.append(f"GATE_5_INVALID_STOP_LOSS: Invalid or tight Stop Loss distance (₹{round(sl_distance, 2)})")
                if not rejection_code:
                    rejection_code = "GATE_5_INVALID_STOP_LOSS"

            target_1 = round(entry_mid - (2.0 * sl_distance), 2)
            target_2 = round(entry_mid - (3.0 * sl_distance), 2)
            target_3 = round(entry_mid - (4.5 * sl_distance), 2)

        reward_distance = abs(target_1 - entry_mid)
        rr_ratio = round(reward_distance / sl_distance, 2) if sl_distance > 0 else 0.0

        # Gate 3 — Risk/Reward Minimum Gate (1:2.0)
        min_rr = 2.0
        if rr_ratio < min_rr:
            failed_conditions.append(f"GATE_3_RISK_REWARD_BELOW_MINIMUM: R/R ratio ({rr_ratio}) below minimum requirement ({min_rr})")
            if not rejection_code:
                rejection_code = "GATE_3_RISK_REWARD_BELOW_MINIMUM"

        # Position Sizing
        max_trade_risk_inr = input_data.user_capital * (input_data.risk_per_trade_pct / 100.0)
        shares = math.floor(max_trade_risk_inr / sl_distance) if sl_distance > 0 else 0
        position_value_inr = round(shares * entry_mid, 2)
        max_allowed_position_value = input_data.user_capital * (input_data.max_position_size_pct / 100.0)

        if position_value_inr > max_allowed_position_value:
            shares = math.floor(max_allowed_position_value / entry_mid)
            position_value_inr = round(shares * entry_mid, 2)

        if shares <= 0:
            failed_conditions.append("GATE_7_LIQUIDITY_INSUFFICIENT: Calculated position size is 0 shares")
            if not rejection_code:
                rejection_code = "GATE_7_LIQUIDITY_INSUFFICIENT"

        # Circuit Band Safety Checks
        if input_data.upper_circuit:
            if input_data.direction == "BUY" and target_1 >= input_data.upper_circuit:
                failed_conditions.append(f"GATE_6_INVALID_TARGET: Target 1 (₹{target_1}) exceeds Upper Circuit price band (₹{input_data.upper_circuit})")
                if not rejection_code:
                    rejection_code = "GATE_6_INVALID_TARGET"
            if input_data.direction == "SELL" and stop_loss >= input_data.upper_circuit:
                failed_conditions.append("GATE_5_INVALID_STOP_LOSS: Stop loss exceeds Upper Circuit price band")
                if not rejection_code:
                    rejection_code = "GATE_5_INVALID_STOP_LOSS"
        
        if input_data.lower_circuit:
            if input_data.direction == "SELL" and target_1 <= input_data.lower_circuit:
                failed_conditions.append(f"GATE_6_INVALID_TARGET: Target 1 (₹{target_1}) below Lower Circuit price band (₹{input_data.lower_circuit})")
                if not rejection_code:
                    rejection_code = "GATE_6_INVALID_TARGET"
            if input_data.direction == "BUY" and stop_loss <= input_data.lower_circuit:
                failed_conditions.append("GATE_5_INVALID_STOP_LOSS: Stop loss below Lower Circuit price band")
                if not rejection_code:
                    rejection_code = "GATE_5_INVALID_STOP_LOSS"

        passed = len(failed_conditions) == 0
        decision = "TAKE_TRADE" if passed else "NO_TRADE"

        return RiskAssessmentResult(
            passed=passed,
            decision=decision,
            rejection_reason_code=rejection_code,
            entry_min=entry_min,
            entry_max=entry_max,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            risk_reward_ratio=rr_ratio,
            position_size_shares=shares,
            max_trade_risk_inr=round(max_trade_risk_inr, 2),
            total_position_value_inr=position_value_inr,
            failed_conditions=failed_conditions
        )

risk_engine = RiskEngine()
