# Token Filtering Logic Analysis

## Current Flow in `process_addresses()`

```
1. Check if crypto relevant → return empty if not
2. Extract addresses from crypto mentions
3. ✅ NEW: Check market commentary → skip if detected
4. Validate and link symbols with addresses (SymbolResolver)
5. If no addresses, try symbol resolution
6. ✅ NEW: Filter addresses by price/market cap → skip if all filtered
7. Loop through filtered addresses:
   - Check if valid
   - Check if dead token (but DON'T skip - track for 30 days)
   - Process address
```

## Potential Conflicts & Issues

### ✅ Issue 1: Duplicate Price Fetching (PERFORMANCE)
**Location:** `_filter_addresses()` → `_process_single_address()`

**Problem:**
- `_filter_addresses()` fetches price data for filtering (line ~220-230)
- `_process_single_address()` fetches price data again immediately after (line ~280)
- This doubles API calls for every token

**Impact:** 
- 2x API calls per token
- Slower processing
- Potential rate limiting

**Solution Options:**
1. **Cache price data** in Address object during filtering
2. **Skip filtering price fetch** and filter after first fetch
3. **Accept duplication** as filtering needs quick check, processing needs fresh data

**Recommendation:** Accept for now (filtering is fast check, processing needs accurate data). Document as optimization opportunity.

---

### ✅ Issue 2: Dead Token Detection After Filtering
**Location:** Lines 125-145

**Current Behavior:**
- Filtering happens first (removes scam tokens)
- Dead token detection happens second (but doesn't skip)
- Dead tokens are tracked for 30 days

**Question:** Should dead tokens be filtered out during the filtering phase?

**Analysis:**
- **Current approach is CORRECT** ✅
- Dead tokens should be tracked for 30 days to count as failed signals
- This gives fair channel ROI calculation
- Filtering removes scams, dead token detection marks them but tracks them

**No change needed.**

---

### ✅ Issue 3: Symbol Resolution After Market Commentary Check
**Location:** Lines 95-110

**Current Behavior:**
- Market commentary check happens BEFORE symbol resolution
- If message is "ETH rally", it skips before trying to resolve ETH symbol

**Potential Issue:**
- If addresses are found but message is commentary, we skip
- If NO addresses found, we try symbol resolution
- But we already checked for commentary, so symbol resolution might resolve ETH

**Scenario:**
```
Message: "ETH rally coming!"
Addresses: [] (none found)
Commentary check: SKIPPED (only runs if addresses exist)
Symbol resolution: Tries to resolve "ETH"
Result: Might create signal for ETH rally ❌
```

**This is a BUG!** 🐛

**Fix:** Move commentary check to AFTER symbol resolution OR check before symbol resolution too.

---

### ✅ Issue 4: Market Commentary Check Only Runs If Addresses Exist
**Location:** Line 64

```python
if addresses and processed.crypto_mentions:
    should_skip, skip_reason = self.token_filter.should_skip_processing(...)
```

**Problem:**
- Commentary check only runs if addresses were found
- If no addresses found, symbol resolution runs
- Symbol resolution might resolve "ETH" from "ETH rally"
- Then filtering runs, but commentary check was skipped

**This is a BUG!** 🐛

**Fix:** Check for market commentary BEFORE address extraction, or check again after symbol resolution.

---

### ✅ Issue 5: Filtering Runs After Symbol Resolution
**Location:** Lines 115-122

**Current Behavior:**
- Symbol resolution adds addresses to the list
- Then filtering runs on ALL addresses (original + resolved)

**This is CORRECT** ✅ - Filtering should run on all addresses regardless of source.

---

## Summary of Issues

| Issue | Severity | Status | Action Needed |
|-------|----------|--------|---------------|
| Duplicate price fetching | Low | Known | Document as optimization |
| Dead token after filtering | None | Correct | No change |
| Commentary check timing | **HIGH** | **BUG** | **Fix required** |
| Commentary check condition | **HIGH** | **BUG** | **Fix required** |
| Filtering after resolution | None | Correct | No change |

## Recommended Fixes

### Fix 1: Move Market Commentary Check Earlier

**Current:**
```python
# Extract addresses
addresses = await self.address_extractor.extract_addresses_async(...)

# Check if message should be skipped (only if addresses exist)
if addresses and processed.crypto_mentions:
    should_skip, skip_reason = self.token_filter.should_skip_processing(...)
```

**Fixed:**
```python
# Check if message should be skipped (BEFORE extraction)
if processed.crypto_mentions:
    symbols = [m for m in processed.crypto_mentions if not m.startswith('0x') and len(m) < 20]
    should_skip, skip_reason = self.token_filter.should_skip_processing(
        event.message_text or "", symbols
    )
    if should_skip:
        self.logger.info(f"⏭️ Skipping message processing: {skip_reason}")
        return addresses_data

# Extract addresses
addresses = await self.address_extractor.extract_addresses_async(...)
```

**Benefits:**
- Skips processing before any API calls
- Prevents "ETH rally" from being resolved via symbol resolution
- More efficient (no wasted address extraction)

---

### Fix 2: Alternative - Check After Symbol Resolution Too

**If we want to keep current structure:**
```python
# After symbol resolution
if resolved_addresses:
    addresses.extend(resolved_addresses)
    
    # Re-check for market commentary with resolved addresses
    symbols = [addr.ticker for addr in addresses if addr.ticker]
    should_skip, skip_reason = self.token_filter.should_skip_processing(
        event.message_text or "", symbols
    )
    if should_skip:
        self.logger.info(f"⏭️ Skipping after symbol resolution: {skip_reason}")
        return addresses_data
```

**Benefits:**
- Catches commentary even if symbols were resolved
- More defensive approach

---

## Recommended Implementation

**Use Fix 1** - Move commentary check to the very beginning, before any processing.

This is:
- ✅ More efficient (no wasted API calls)
- ✅ Simpler logic
- ✅ Catches all commentary cases
- ✅ Prevents false signals from symbol resolution
