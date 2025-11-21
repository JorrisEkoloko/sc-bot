"""Test duplicate symbol filtering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter, TokenCandidate

# Simulate two ZEN tokens
candidates = [
    TokenCandidate(
        address="3pH7FnM3yR2Jy2c6vyXmsCiNi1rjQ7gerCq2pEUHpump",
        chain="solana",
        symbol="ZEN",
        price_usd=0.011256,
        market_cap=50000  # Lower market cap
    ),
    TokenCandidate(
        address="0x3bbbb6a231d0a1a12c6b79ba5bc2ed6358db5160",
        chain="ethereum",
        symbol="ZEN",
        price_usd=0.340025,
        market_cap=500000  # Higher market cap
    )
]

filter = TokenFilter()

filtered = filter.filter_symbol_candidates("ZEN", candidates, "Buy ZEN")

print(f"\nOriginal candidates: {len(candidates)}")
for c in candidates:
    print(f"  - {c.chain}: {c.address[:10]}... (${c.market_cap:,})")

print(f"\nFiltered candidates: {len(filtered)}")
for c in filtered:
    print(f"  - {c.chain}: {c.address[:10]}... (${c.market_cap:,})")

print(f"\nExpected: 1 candidate (highest market cap)")
print(f"Result: {'✅ PASS' if len(filtered) == 1 else '❌ FAIL'}")

if len(filtered) == 1:
    print(f"Selected: {filtered[0].chain} with ${filtered[0].market_cap:,} market cap")
