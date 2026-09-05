import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend folder is in Python Path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_indicators import test_indicator_calculations, test_rsi_edge_cases, test_vwap_session_reset
from tests.test_data_quality import test_data_quality_stale_rejection, test_invalid_ohlc_relationship
from tests.test_risk_engine import test_risk_engine_valid_buy_trade, test_risk_engine_valid_sell_trade, test_risk_engine_upper_circuit_rejection
from tests.test_live_provider import test_live_provider_symbol_formatting, test_mock_provider_fallback_contract, test_live_provider_quote_fetch
from tests.test_scheduler import test_scheduler_market_hours_check, test_scheduler_deduplication_tracking
from tests.test_whatsapp import test_whatsapp_message_formatting, test_whatsapp_idempotency_deduplication
from tests.test_p0_orchestrator import test_p0_orchestrator_signal_dispatch_and_persistence
from tests.test_backtesting import test_backtest_stateful_multi_candle_simulation
from tests.test_paper_trading import test_paper_trading_lifecycle
from tests.test_market_data_factory import test_market_data_factory_resolution
from tests.test_market_data_cache import test_market_data_cache_freshness_and_ttl
from tests.test_scrapers import test_scraper_defensive_number_parsing, test_scraper_html_parsing_contract
from tests.test_live_collector import test_live_collector_batch_polling_and_caching

def run_suite():
    print("=" * 60)
    print("HARSH TRADER AI -- EXECUTING SYSTEM TEST SUITE")
    print("=" * 60)

    passed = 0
    failed = 0
    errors = []

    test_cases = [
        ("1", "Technical Indicator Calculations", test_indicator_calculations),
        ("2", "RSI Edge Cases (Monotonic/Flat)", test_rsi_edge_cases),
        ("3", "VWAP Session Reset", test_vwap_session_reset),
        ("4", "Data Quality: Stale Data Rejection", test_data_quality_stale_rejection),
        ("5", "Data Quality: Invalid OHLC Relationship", test_invalid_ohlc_relationship),
        ("6", "Risk Engine: Valid BUY Trade", test_risk_engine_valid_buy_trade),
        ("7", "Risk Engine: Valid SELL Trade", test_risk_engine_valid_sell_trade),
        ("8", "Risk Engine: Upper Circuit Rejection", test_risk_engine_upper_circuit_rejection),
        ("9", "Live Provider: Symbol Formatting", test_live_provider_symbol_formatting),
        ("10", "Live Provider: Mock Fallback Contract", test_mock_provider_fallback_contract),
        ("11", "Live Provider: Quote Fetch", test_live_provider_quote_fetch),
        ("12", "Scanner: Market Hours Check", test_scheduler_market_hours_check),
        ("13", "Scanner: Deduplication Tracking", test_scheduler_deduplication_tracking),
        ("14", "WhatsApp: Message Formatting", test_whatsapp_message_formatting),
        ("15", "WhatsApp: Idempotency Deduplication", test_whatsapp_idempotency_deduplication),
        ("16", "P0 Orchestrator: Signal Dispatch & Persistence", test_p0_orchestrator_signal_dispatch_and_persistence),
        ("17", "Backtesting: Stateful Multi-Candle Simulation", test_backtest_stateful_multi_candle_simulation),
        ("18", "Paper Trading: Lifecycle", test_paper_trading_lifecycle),
        ("19", "Market Data Factory: Resolution", test_market_data_factory_resolution),
        ("20", "Market Data Cache: TTL & Freshness", test_market_data_cache_freshness_and_ttl),
        ("21", "Scraper: Defensive Float/Int Parsing", test_scraper_defensive_number_parsing),
        ("22", "Scraper: Google Finance HTML Contract", test_scraper_html_parsing_contract),
        ("23", "Live Collector: Batch Polling & Cache", test_live_collector_batch_polling_and_caching),
    ]

    total = len(test_cases)

    for num, name, test_fn in test_cases:
        try:
            print(f"[{num}/{total}] Testing {name}...")
            test_fn()
            print(f"  [OK] {name} passed.")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name} FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
            errors.append((name, str(e)))

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {total} tests.")
    if errors:
        print("FAILURES:")
        for name, err in errors:
            print(f"  - {name}: {err}")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_suite()
