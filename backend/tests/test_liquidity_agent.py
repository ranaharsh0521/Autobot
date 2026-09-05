from app.agents.liquidity_agent import LiquidityAgent


def test_liquidity_agent_handles_missing_bid_ask():
    agent = LiquidityAgent()

    result = agent.analyze(
        "RELIANCE",
        "EXEC-TEST",
        {
            "last_price": 1300.0,
            "bid": None,
            "ask": None,
            "volume": 500000,
            "upper_circuit": None,
            "lower_circuit": None,
        },
    )

    assert result.score >= 50.0
    assert "Bid/ask spread unavailable" in result.bearish_factors[0]
