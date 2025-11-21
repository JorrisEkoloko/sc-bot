"""Test if BUY message is correctly detected."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filtering.token_filter import TokenFilter

message = """🆕 | **3 BUY!**
__by ____@MajorBuyBot__
🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩 🎩  🎩
🔷 **SOL** 22.7810 ($4460.52)
🪙 **3** 8799091.56 [__(Tx)__](https://solscan.io/tx/48dFZpzRzHKR7WKUx2GknN3fsoTCjMMR46G4Md9GmdQWoNfJkFJFzFxNZb5FLb4pcuNarC7qx4PPrJ7wHJnDF1gsQ)
🔎 **Position:** New Holder [__(Wallet)__](https://solscan.io/account/FCx2JrnLprveVhoJnzp4eaPoeqYCsWPsZTxKvr4p18i1)
📈 **MCap:** $506,929
**📊**** **[**Dex**](https://majorbots.io/buybot/3hW6i9h7tJKHdmCRNH3pzVLLtAPFmhbHgBaf5WVdDRRJ?utm=MevX)** ****💲**** **[**Thor**](https://t.me/ThorSolana_bot?start=r-major-buy-GfCSfsnVE1jnS6NnSMoYqXWJV1ZgPug93J79byxYpump)** ****💲**** **[**MevX**](https://t.me/MevxTradingBot?start=GfCSfsnVE1jnS6NnSMoYqXWJV1ZgPug93J79byxYpump-MajorBuyBot)******🗳**** **[**Vote**](https://t.me/MajorBuyBot?start=vote_-1003145003968)"""

symbols = ["SOL"]  # Only short symbols passed (addresses filtered out by len < 20)

filter = TokenFilter()

should_skip, reason = filter.should_skip_processing(message, symbols)

print(f"\nMessage: {message[:100]}...")
print(f"Symbols: {symbols}")
print(f"Should skip: {should_skip}")
print(f"Reason: {reason}")
print(f"\nExpected: Should NOT skip (this is a BUY call)")
print(f"Result: {'✅ PASS' if not should_skip else '❌ FAIL'}")
