"""Test trading signal detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

test_cases = [
    {
        "message": "#STORJ/USDT Take-Profit target 3 ✅ Profit: 23.9328%",
        "symbols": ["USDT", "STORJ"],
        "expected": False,
        "reason": "Trading signal (take-profit hit)"
    },
    {
        "message": "BTC/USDT Entry: $50,000 Target: $55,000",
        "symbols": ["BTC", "USDT"],
        "expected": False,
        "reason": "Trading signal (entry/target)"
    },
    {
        "message": "ETH falls under $3,000",
        "symbols": ["ETH"],
        "expected": True,
        "reason": "Price commentary"
    },
    {
        "message": "SOL rally coming! Bullish trend",
        "symbols": ["SOL"],
        "expected": True,
        "reason": "Market commentary"
    },
    {
        "message": "DOGE stop-loss triggered at $0.10",
        "symbols": ["DOGE", "USDT"],
        "expected": False,
        "reason": "Trading signal (stop-loss)"
    }
]

def main():
    filter = TokenFilter()
    
    print("\n" + "="*70)
    print("Trading Signal vs Commentary Detection")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        message = test["message"]
        symbols = test["symbols"]
        expected = test["expected"]
        reason = test["reason"]
        
        is_commentary = filter.is_market_commentary(message, symbols)
        
        status = "✅ PASS" if is_commentary == expected else "❌ FAIL"
        if is_commentary == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\nTest {i}: {status}")
        print(f"  Message: {message[:60]}...")
        print(f"  Expected: {'Commentary' if expected else 'Trading Signal'}")
        print(f"  Got: {'Commentary' if is_commentary else 'Trading Signal'}")
        print(f"  Reason: {reason}")
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
