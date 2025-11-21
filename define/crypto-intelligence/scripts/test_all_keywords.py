"""Comprehensive test of all keyword types."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

test_cases = [
    # Trading signals (should NOT be commentary)
    {"msg": "Take-Profit target hit", "symbols": ["BTC"], "expected_commentary": False, "type": "Trading Signal"},
    {"msg": "Stop-loss triggered", "symbols": ["ETH"], "expected_commentary": False, "type": "Trading Signal"},
    {"msg": "Entry at $50k", "symbols": ["BTC"], "expected_commentary": False, "type": "Trading Signal"},
    
    # Action keywords (should NOT be commentary)
    {"msg": "Buy now!", "symbols": ["SOL"], "expected_commentary": False, "type": "Action"},
    {"msg": "Gem alert", "symbols": ["DOGE"], "expected_commentary": False, "type": "Action"},
    {"msg": "Accumulate here", "symbols": ["ETH"], "expected_commentary": False, "type": "Action"},
    {"msg": "FOMO incoming", "symbols": ["BTC"], "expected_commentary": False, "type": "Action"},
    {"msg": "Diamond hands", "symbols": ["SOL"], "expected_commentary": False, "type": "Action"},
    
    # Commentary keywords (should BE commentary)
    {"msg": "ETH rally coming", "symbols": ["ETH"], "expected_commentary": True, "type": "Commentary"},
    {"msg": "Bullish prediction", "symbols": ["BTC"], "expected_commentary": True, "type": "Commentary"},
    {"msg": "Market analysis shows", "symbols": ["SOL"], "expected_commentary": True, "type": "Commentary"},
    {"msg": "Breaking news", "symbols": ["ETH"], "expected_commentary": True, "type": "Commentary"},
    {"msg": "Overbought conditions", "symbols": ["BTC"], "expected_commentary": True, "type": "Commentary"},
    
    # Price commentary (should BE commentary)
    {"msg": "BTC hits $100k", "symbols": ["BTC"], "expected_commentary": True, "type": "Price Commentary"},
    {"msg": "ETH falls under $3,000", "symbols": ["ETH"], "expected_commentary": True, "type": "Price Commentary"},
]

def main():
    filter = TokenFilter()
    
    print("\n" + "="*80)
    print("Comprehensive Keyword Test")
    print("="*80)
    print(f"\nLoaded Keywords:")
    print(f"  Trading Signals: {len(filter.trading_signal_keywords)}")
    print(f"  Action Keywords: {len(filter.action_keywords)}")
    print(f"  Commentary Keywords: {len(filter.commentary_keywords)}")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        msg = test["msg"]
        symbols = test["symbols"]
        expected = test["expected_commentary"]
        test_type = test["type"]
        
        is_commentary = filter.is_market_commentary(msg, symbols)
        
        status = "✅" if is_commentary == expected else "❌"
        if is_commentary == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} Test {i}: {test_type}")
        print(f"   Message: {msg}")
        print(f"   Expected: {'Commentary' if expected else 'Not Commentary'}")
        print(f"   Got: {'Commentary' if is_commentary else 'Not Commentary'}")
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print("="*80 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
