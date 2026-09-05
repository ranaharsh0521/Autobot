import pytest
from app.risk.engine import RiskEngine, RiskAssessmentInput

def test_risk_engine_valid_buy_trade():
    engine = RiskEngine()
    input_data = RiskAssessmentInput(
        symbol="RELIANCE",
        mode="INTRADAY",
        direction="BUY",
        current_price=2950.0,
        atr_14=30.0,
        support_levels=[2800.0, 2920.0, 3100.0], # Multiple supports
        resistance_levels=[3000.0, 3050.0],
        user_capital=100000.0,
        risk_per_trade_pct=1.0, # ₹1,000 max risk
        data_quality_score=98.0
    )

    res = engine.evaluate_trade_risk(input_data)
    assert res.passed is True
    assert res.decision == "TAKE_TRADE"
    assert res.stop_loss == 2920.0 # Selected nearest support below 2950 (2920, not 2800 or 3100)
    assert res.target_1 > res.entry_max
    assert res.risk_reward_ratio >= 2.0
    assert res.position_size_shares > 0
    assert res.total_position_value_inr <= 15000.0 # 15% max position limit

def test_risk_engine_valid_sell_trade():
    engine = RiskEngine()
    input_data = RiskAssessmentInput(
        symbol="INFY",
        mode="INTRADAY",
        direction="SELL",
        current_price=1600.0,
        atr_14=20.0,
        support_levels=[1500.0],
        resistance_levels=[1400.0, 1630.0, 1750.0], # Multiple resistances
        user_capital=100000.0,
        risk_per_trade_pct=1.0,
        data_quality_score=98.0
    )

    res = engine.evaluate_trade_risk(input_data)
    assert res.passed is True
    assert res.decision == "TAKE_TRADE"
    assert res.stop_loss == 1630.0 # Selected nearest resistance above 1600 (1630, not 1750 or 1400)
    assert res.target_1 < res.entry_min
    assert res.risk_reward_ratio >= 2.0

def test_risk_engine_upper_circuit_rejection():
    engine = RiskEngine()
    input_data = RiskAssessmentInput(
        symbol="TATAMOTORS",
        mode="INTRADAY",
        direction="BUY",
        current_price=1000.0,
        atr_14=25.0,
        support_levels=[970.0],
        upper_circuit=1030.0, # Target 1 would be 1000 + 2*30 = 1060 >= upper_circuit 1030
        user_capital=100000.0,
        risk_per_trade_pct=1.0,
        data_quality_score=95.0
    )
    
    res = engine.evaluate_trade_risk(input_data)
    assert res.passed is False
    assert res.decision == "NO_TRADE"
    assert any("Upper Circuit" in cond for cond in res.failed_conditions)
