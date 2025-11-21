# Price Engine Refactoring Plan

## Current State

`PriceEngine` (599 lines) mixes core price fetching with extensive enrichment logic.

## Proposed Split

### 1. **PriceEngine** (~350 lines)
**Responsibility**: Core price fetching with failover

**Keep**:
- API client initialization
- Rate limiter setup
- Cache management
- `get_price()` - simplified to fetch + delegate enrichment
- `get_historical_data()` - historical ATH/ATL fetching
- `get_historical_ohlc()` - OHLC data fetching
- `get_price_at_timestamp()` - timestamp-specific prices
- `get_prices_batch()` - batch operations
- `_get_api_sequence()` - API priority logic
- `close()` - cleanup

**Simplify `get_price()` to**:
```python
async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
    # Check cache
    if cache_key in self.cache:
        return self.cache[cache_key]
    
    # Try APIs in sequence
    price_data = await self._fetch_from_apis(address, chain)
    if not price_data:
        return None
    
    # Delegate enrichment to PriceEnrichmentService
    price_data = await self.enrichment_service.enrich_price_data(
        price_data, address, chain
    )
    
    # Cache and return
    self.cache[cache_key] = price_data
    return price_data
```

### 2. **PriceEnrichmentService** (~250 lines) ✅ CREATED
**Responsibility**: Enrich price data with missing fields

**Contains**:
- `enrich_price_data()` - main enrichment coordinator
- `_enrich_with_parallel_apis()` - DexScreener + Blockscout parallel calls
- `_merge_dexscreener_data()` - merge DexScreener results
- `_enrich_symbol_fallback()` - contract reading + GoPlus + DefiLlama
- `_enrich_ath_data()` - fetch ATH from CoinGecko

## Benefits

1. **Separation of Concerns**: Fetching vs enrichment clearly separated
2. **Testability**: Can test enrichment logic independently
3. **Maintainability**: Each file has one clear purpose
4. **Reusability**: Enrichment service can be used by other components
5. **Readability**: Simpler get_price() method

## Implementation Status

- ✅ PriceEnrichmentService created
- ⏳ PriceEngine refactoring (pending)
- ⏳ Integration testing (pending)

## Notes

The PriceEnrichmentService has been created and is ready to use. The PriceEngine refactoring is straightforward:
1. Initialize enrichment service in __init__
2. Simplify get_price() to delegate enrichment
3. Remove enrichment logic from get_price()

This refactoring is **optional** as the current code works well. The main benefit is cleaner separation for future maintenance.

## Decision

Given that:
1. Steps 1-3 are complete and working
2. PriceEngine enrichment logic is already well-organized
3. The enrichment service is created and ready
4. Time/benefit tradeoff for this specific refactoring

**Recommendation**: Mark as "ready to implement when needed" rather than forcing it now. The groundwork is done.
