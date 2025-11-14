# Part 7: Market Intelligence - Quick Start

## Overview

Part 7 adds market intelligence to price data with tier classification and multi-factor risk assessment.

## What You Get

- **Tier Classification**: Large/Mid/Small/Micro-cap based on market cap
- **Risk Assessment**: 4-factor risk scoring (tier, liquidity, volume, volatility)
- **Graceful Degradation**: Works with partial data
- **6 New Columns**: market_tier, risk_level, risk_score, liquidity_ratio, volume_ratio, data_completeness

## Implementation Order

1. **Task 1**: Create `intelligence/market_analyzer.py` (~250 lines)
2. **Task 2**: Add 7 fields to `PriceData` (~7 lines)
3. **Task 3**: Integrate with `price_engine.py` (~20 lines)
4. **Task 4**: Update `data_output.py` columns (~10 lines)

**Total**: ~287 lines of new code

## Key Thresholds

### Market Cap Tiers (Crypto-Adjusted)

- Large: $1B+
- Mid: $100M-$1B
- Small: $10M-$100M
- Micro: <$10M

### Risk Factors & Weights

- Tier Risk: 40%
- Liquidity Risk: 30%
- Volume Risk: 20%
- Volatility Risk: 10%

## Validation

```bash
# Run historical scraper
python scripts/historical_scraper.py --limit 10

# Check logs for:
# "Market intelligence: mid tier, high risk (100% data)"

# Check CSV for 15 columns (was 9):
# address, chain, symbol, price_usd, market_cap, volume_24h, price_change_24h,
# liquidity_usd, pair_created_at, market_tier, risk_level, risk_score,
# liquidity_ratio, volume_ratio, data_completeness
```

## Expected Results

### With Full Data (DexScreener)

```
market_tier: "mid"
risk_level: "high"
risk_score: 62.5
liquidity_ratio: 0.036
volume_ratio: 0.047
data_completeness: 1.0
```

### With Partial Data (CoinGecko)

```
market_tier: "small"
risk_level: "moderate"
risk_score: 45.0
liquidity_ratio: None
volume_ratio: 0.023
data_completeness: 0.75
```

### With Price Only (DefiLlama)

```
market_tier: "unknown"
risk_level: "unknown"
risk_score: None
liquidity_ratio: None
volume_ratio: None
data_completeness: 0.0
```

## No Breaking Changes

- Existing price fetching works unchanged
- Market intelligence is additive only
- Analysis failures don't crash the system
- Backward compatible with existing code

## Performance

- Tier classification: <1ms
- Full risk assessment: <5ms
- Total overhead: <10ms
- No additional API calls

## Files Modified

```
NEW:
- intelligence/__init__.py
- intelligence/market_analyzer.py

MODIFIED:
- core/api_clients/base_client.py (PriceData +7 fields)
- core/price_engine.py (add intelligence enrichment)
- core/data_output.py (TOKEN_PRICES +6 columns)
```

## Ready to Implement?

Follow `tasks.md` for detailed step-by-step implementation.
