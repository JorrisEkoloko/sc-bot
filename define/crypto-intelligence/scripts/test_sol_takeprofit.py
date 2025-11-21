"""Test SOL take-profit message."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

message = "#SOL/USDT Take-Profit target 6 ✅ Profit: 53.7302%"
symbols = ["SOL", "USDT"]  # Both are major tokens

filter = TokenFilter()

should_skip, reason = filter.should_skip_processing(message, symbols)

print(f"\nMessage: {message}")
print(f"Symbols: {symbols}")
print(f"Should skip: {should_skip}")
print(f"Reason: {reason}")
print(f"\nExpected: Should NOT skip (this is a take-profit signal)")
print(f"Result: {'✅ PASS' if not should_skip else '❌ FAIL'}")
