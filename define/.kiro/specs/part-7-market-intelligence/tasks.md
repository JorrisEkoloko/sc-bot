# Implementation Plan - Part 7: Market Intelligence & Tier Classification

## Task Overview

This implementation plan adds market intelligence capabilities in 4 focused tasks. Each task delivers working functionality that integrates into the pipeline, transforming price data into risk-assessed market intelligence with tier classification.

## Validation Approach

Use the existing `scripts/historical_scraper.py` as the **primary validation method**. After implementing each component, run the scraper with historical messages to validate market intelligence appears in output.

---

## - [ ] 1. Create intelligence directory and market analyzer

Create the market intelligence analyzer that classifies tokens into tiers and assesses risk using multiple factors.

**Implementation Details**:

- Create `intelligence/` directory
- Create `intelligence/__init__.py`
- Create `intelligence/market_analyzer.py` with MarketAnalyzer class
- Implement MarketIntelligence dataclass with all fields
- Implement \_classify_tier() with crypto-adjusted thresholds ($1B/$100M/$10M)
- Implement \_calculate_liquidity_ratio() (liquidity_usd / market_cap)
- Implement \_calculate_volume_ratio() (volume_24h / market_cap)
- Implement \_assess_risk() with 4-factor weighted scoring (40%/30%/20%/10%)
- Implement \_calculate_tier_risk(), \_calculate_liquidity_risk(), \_calculate_volume_risk(), \_calculate_volatility_risk()
- Implement \_get_risk_level() to convert score to categorical level
- Implement graceful degradation (works with partial data)
- Add comprehensive logging for transparency

**External Verification with fetch MCP**:

- Verify market cap classification standards: https://www.investopedia.com/terms/m/marketcapitalization.asp
- Verify crypto market adjustments (10x lower thresholds for crypto vs traditional)
- Verify risk assessment methodologies (multi-factor approach)
- Verify liquidity ratio analysis best practices

**Files to Create**:

- `intelligence/__init__.py` (~10 lines)
- `intelligence/market_analyzer.py` (~250 lines)

**Validation**:

- Tier classification works with market cap values
- Large-cap: $1B+ classified correctly
- Mid-cap: $100M-$1B classified correctly
- Small-cap: $10M-$100M classified correctly
- Micro-cap: <$10M classified correctly
- Risk assessment combines available factors
- Graceful degradation handles missing data
- Test with market_cap only → tier classification works, risk score uses 1 factor
- Test with all data → full risk assessment works, risk score uses 4 factors
- Test with no data → returns "unknown" gracefully
- Logging shows which factors were used
- Data completeness calculated correctly (0.25, 0.5, 0.75, 1.0)

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Update historical scraper to integrate MarketAnalyzer (if needed for testing)
2. Run `python scripts/historical_scraper.py --limit 10`
3. Verify logs show: "Market analyzer initialized"
4. Verify logs show: "Analyzing market intelligence for address: 0x..."
5. Verify logs show: "Classified as [tier] tier: $X.XM market cap"
6. Verify logs show: "Liquidity ratio: X.XXX"
7. Verify logs show: "Volume ratio: X.XXX"
8. Verify logs show: "Risk assessment: X factors used (X% data)"
9. Verify logs show: "Risk level: [level] (score: XX.X)"
10. Verify tier classifications match market cap values
11. Verify risk levels match risk scores
12. Verify graceful degradation with partial data
13. Review verification report for market intelligence statistics
14. Verify data completeness varies by available factors

**Status**: ⏳ Ready for implementation

**Requirements**: 1, 2, 3, 4, 5, 6, 10

---

## - [ ] 2. Extend PriceData with market intelligence fields

Update the PriceData dataclass to include market intelligence fields.

**Implementation Details**:

- Modify `core/api_clients/base_client.py`
- Add market_tier field (Optional[str])
- Add tier_description field (Optional[str])
- Add risk_level field (Optional[str])
- Add risk_score field (Optional[float])
- Add liquidity_ratio field (Optional[float])
- Add volume_ratio field (Optional[float])
- Add data_completeness field (Optional[float])
- All new fields default to None
- Maintain backward compatibility

**External Verification with fetch MCP**:

- Verify Python dataclass best practices: https://docs.python.org/3/library/dataclasses.html
- Verify Optional type hints: https://docs.python.org/3/library/typing.html
- Verify backward compatibility patterns for dataclass extensions

**Files to Modify**:

- `core/api_clients/base_client.py` (~7 lines added)

**Validation**:

- PriceData can be created with new fields
- PriceData can be created without new fields (backward compatible)
- New fields serialize correctly
- Test creating PriceData with all fields populated
- Test creating PriceData with only price (new fields None)
- Test existing code still works (no breaking changes)
- Import PriceData in other modules still works

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "PriceData created with market intelligence fields"
3. Verify no errors from PriceData changes
4. Verify existing price fetching still works
5. Verify new fields can be accessed (even if None)
6. Verify backward compatibility maintained
7. Verify PriceData serialization works with new fields
8. Review verification report confirms no breaking changes

**Status**: ⏳ Ready for implementation

**Requirements**: 7

---

## - [ ] 3. Integrate market analyzer with price engine

Add market intelligence enrichment to the price engine after price fetching.

**Implementation Details**:

- Modify `core/price_engine.py`
- Import MarketAnalyzer in get_price() method
- After successful price fetch and data enrichment, call analyzer.analyze()
- Populate PriceData with MarketIntelligence results
- Add try/except to handle analysis failures gracefully
- Log market intelligence results (tier, risk level, data completeness)
- If analysis fails, continue with price data only (no crash)
- Cached PriceData includes market intelligence
- Ensure no additional API calls are made

**External Verification with fetch MCP**:

- Verify async integration patterns: https://docs.python.org/3/library/asyncio-task.html
- Verify error handling best practices: https://docs.python.org/3/tutorial/errors.html
- Verify graceful degradation patterns in distributed systems

**Files to Modify**:

- `core/price_engine.py` (~20 lines added)

**Validation**:

- Price fetching still works (no breaking changes)
- Market intelligence added when data available
- Logs show tier and risk level
- Analysis failures don't crash price fetching
- Cached data includes market intelligence
- Test with DexScreener (full data) → full intelligence (4 factors)
- Test with CoinGecko (no liquidity) → partial intelligence (3 factors)
- Test with DefiLlama (price only) → minimal intelligence (0-1 factors)
- Test with API failure → no intelligence, price fetch continues
- Performance overhead < 10ms

**Historical Scraper Verification**:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "Market intelligence: [tier] tier, [risk] risk ([X]% data)"
3. Verify price fetching still works for all addresses
4. Verify market intelligence appears for addresses with market_cap
5. Verify graceful degradation for addresses without market_cap
6. Verify no crashes or errors
7. Review verification report for market intelligence statistics
8. Verify data completeness varies by API source

**Status**: ⏳ Ready for implementation

**Requirements**: 7, 9

---

## - [ ] 4. Update data output with market intelligence columns

Extend the TOKEN_PRICES table to include 6 new market intelligence columns.

**Implementation Details**:

- Modify `core/data_output.py`
- Update TOKEN_PRICES_COLUMNS to include 6 new columns:
  - market_tier
  - risk_level
  - risk_score
  - liquidity_ratio
  - volume_ratio
  - data_completeness
- Update write_token_price() to populate new columns from PriceData
- Handle None values (write empty string or null)
- Ensure CSV and Google Sheets both get new columns
- Maintain column order and formatting

**External Verification with fetch MCP**:

- Verify CSV format best practices: https://docs.python.org/3/library/csv.html
- Verify Google Sheets API column updates: https://docs.gspread.org/en/latest/
- Verify handling None/null values in CSV and Sheets

**Files to Modify**:

- `core/data_output.py` (~10 lines modified)

**Validation**:

- CSV files have 15 columns (was 9)
- Google Sheets have 15 columns
- New columns populated when data available
- New columns empty when data unavailable
- No errors when writing None values
- Column headers correct in both CSV and Sheets
- Test with full intelligence → all columns populated
- Test with partial intelligence → some columns populated
- Test with no intelligence → columns empty
- Existing data output still works (no breaking changes)

**Historical Scraper Verification**:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify CSV has 15 columns in token_prices.csv
3. Verify column headers include: market_tier, risk_level, risk_score, liquidity_ratio, volume_ratio, data_completeness
4. Verify market_tier column has values like "mid", "small", "micro"
5. Verify risk_level column has values like "moderate", "high", "extreme"
6. Verify risk_score column has numerical values 0-100
7. Verify liquidity_ratio and volume_ratio have decimal values
8. Verify data_completeness shows 0.25, 0.5, 0.75, or 1.0
9. Verify Google Sheets shows new columns with data
10. Verify tokens with full data have complete intelligence
11. Verify tokens with partial data have partial intelligence
12. Review verification report for complete statistics

**Status**: ⏳ Ready for implementation

**Requirements**: 8

---

## Final Validation Checklist

After completing all tasks, verify:

### Component Verification

- [ ] MarketAnalyzer classifies tiers correctly
- [ ] MarketAnalyzer calculates liquidity ratio
- [ ] MarketAnalyzer calculates volume ratio
- [ ] MarketAnalyzer assesses volatility
- [ ] MarketAnalyzer combines factors into risk score
- [ ] MarketAnalyzer handles missing data gracefully
- [ ] PriceData has new intelligence fields
- [ ] Price Engine enriches with market intelligence
- [ ] Price Engine handles analysis failures
- [ ] Data Output writes 15 columns
- [ ] CSV files contain market intelligence
- [ ] Google Sheets contain market intelligence

### Data Verification

- [ ] Large-cap tokens (>$1B) classified correctly
- [ ] Mid-cap tokens ($100M-$1B) classified correctly
- [ ] Small-cap tokens ($10M-$100M) classified correctly
- [ ] Micro-cap tokens (<$10M) classified correctly
- [ ] Risk levels match risk scores (low/moderate/high/extreme)
- [ ] Liquidity ratios calculated correctly
- [ ] Volume ratios calculated correctly
- [ ] Data completeness reflects available factors

### Integration Verification

- [ ] Price fetching still works (no breaking changes)
- [ ] Market intelligence appears in logs
- [ ] Market intelligence appears in CSV
- [ ] Market intelligence appears in Google Sheets
- [ ] Caching works with intelligence data
- [ ] Graceful degradation works with partial data
- [ ] System doesn't crash on analysis failures

### Performance Verification

- [ ] Tier classification < 1ms
- [ ] Risk assessment < 5ms
- [ ] Price Engine overhead < 10ms
- [ ] No additional API calls made

---

## Example Output

### Console Log

```
[2025-11-10 23:00:00] [INFO] [PriceEngine] Price fetched from dexscreener: $3.920000
[2025-11-10 23:00:00] [INFO] [MarketAnalyzer] Classified as mid tier: $50.6M market cap
[2025-11-10 23:00:00] [INFO] [MarketAnalyzer] Risk assessment: 4 factors used (100% data)
[2025-11-10 23:00:00] [INFO] [PriceEngine] Market intelligence: mid tier, high risk (100% data)
```

### CSV Output (token_prices.csv)

```csv
address,chain,symbol,price_usd,market_cap,volume_24h,price_change_24h,liquidity_usd,pair_created_at,market_tier,risk_level,risk_score,liquidity_ratio,volume_ratio,data_completeness
5gb4npgfb3...,solana,AVICI,3.92,50587715.0,2361161.26,38.38,1804744.18,1760806818000,mid,high,62.5,0.036,0.047,1.0
0x9f277e...,evm,WOOLLY,0.00014424,144338.19,67.62,-0.56,,,micro,extreme,80.0,,,0.5
```

---

## Success Criteria

- ✅ All 4 tasks completed
- ✅ Market intelligence appears in output
- ✅ Graceful degradation works
- ✅ No breaking changes to existing functionality
- ✅ Performance targets met
- ✅ Historical scraper shows intelligence in verification report
