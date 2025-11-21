"""Test commentary detection with real messages."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

# Test messages
test_cases = [
    {
        "message": "**JUST IN:** $ETH falls under $3,000.",
        "symbols": ["ETH"],
        "expected": True,
        "reason": "Price commentary"
    },
    {
        "message": "ETH rally coming! Bullish trend ahead.",
        "symbols": ["ETH"],
        "expected": True,
        "reason": "Market commentary"
    },
    {
        "message": "Buy SMOON at 0xd4AE83eA...",
        "symbols": ["SMOON"],
        "expected": False,
        "reason": "Token call with address"
    },
    {
        "message": "BTC hits $100k milestone",
        "symbols": ["BTC"],
        "expected": True,
        "reason": "Price milestone commentary"
    },
    {
        "message": "SOL gem call - buy now!",
        "symbols": ["SOL"],
        "expected": False,
        "reason": "Call to action present"
    }
]

def main():
    filter = TokenFilter()
    
    print("\n" + "="*70)
    print("Market Commentary Detection Tests")
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
        print(f"  Symbols: {', '.join(symbols)}")
        print(f"  Expected: {'Commentary' if expected else 'Not Commentary'}")
        print(f"  Got: {'Commentary' if is_commentary else 'Not Commentary'}")
        print(f"  Reason: {reason}")
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
