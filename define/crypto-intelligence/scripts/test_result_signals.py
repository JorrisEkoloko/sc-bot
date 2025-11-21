"""Test result signal detection (take-profit, stop-loss hits)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

test_cases = [
    {
        "message": "#ZEN/USDT Take-Profit target 4 ✅ Profit: 53.7302%",
        "symbols": ["ZEN", "USDT"],
        "expected_skip": True,
        "reason": "Take-profit result (closed trade)"
    },
    {
        "message": "#SOL/USDT Take-Profit target 6 ✅",
        "symbols": ["SOL", "USDT"],
        "expected_skip": True,
        "reason": "Take-profit result (closed trade)"
    },
    {
        "message": "BTC/USDT Entry: $50,000 Target: $55,000",
        "symbols": ["BTC", "USDT"],
        "expected_skip": False,
        "reason": "Entry signal (new trade)"
    },
    {
        "message": "Buy SMOON at 0xd4AE83eA...",
        "symbols": ["SMOON"],
        "expected_skip": False,
        "reason": "Buy call (new trade)"
    },
    {
        "message": "ETH stop-loss hit at $3,000",
        "symbols": ["ETH"],
        "expected_skip": True,
        "reason": "Stop-loss result (closed trade)"
    }
]

def main():
    filter = TokenFilter()
    
    print("\n" + "="*70)
    print("Result Signal Detection (Skip Take-Profit/Stop-Loss Hits)")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        message = test["message"]
        symbols = test["symbols"]
        expected_skip = test["expected_skip"]
        reason = test["reason"]
        
        should_skip, skip_reason = filter.should_skip_processing(message, symbols)
        
        status = "✅ PASS" if should_skip == expected_skip else "❌ FAIL"
        if should_skip == expected_skip:
            passed += 1
        else:
            failed += 1
        
        print(f"\nTest {i}: {status}")
        print(f"  Message: {message[:60]}...")
        print(f"  Expected: {'Skip' if expected_skip else 'Process'}")
        print(f"  Got: {'Skip' if should_skip else 'Process'}")
        print(f"  Reason: {reason}")
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
