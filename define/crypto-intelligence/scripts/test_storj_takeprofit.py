"""Test STORJ take-profit message."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

message = "#STORJ/USDT Take-Profit target 1 ✅ Profit: 9.6685%"
symbols = ["STORJ", "USDT"]

filter = TokenFilter()

# Test is_market_commentary
is_commentary = filter.is_market_commentary(message, symbols)
print(f"\nMessage: {message}")
print(f"Symbols: {symbols}")
print(f"Is market commentary: {is_commentary}")

# Test should_skip_processing
should_skip, reason = filter.should_skip_processing(message, symbols)
print(f"Should skip: {should_skip}")
print(f"Reason: {reason}")

print(f"\nExpected: Should skip (take-profit result)")
print(f"Result: {'✅ PASS' if should_skip else '❌ FAIL'}")

# Debug: Check if keyword is in message
message_lower = message.lower()
print(f"\nDebug:")
print(f"  Message lower: {message_lower}")
print(f"  'take-profit target' in message: {'take-profit target' in message_lower}")
print(f"  'take profit target' in message: {'take profit target' in message_lower}")
