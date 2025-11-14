# Implementation Plan - Part 3: Address Extraction & Price Tracking

## Task Overview

This implementation plan builds price intelligence in 5 focused tasks. Each task delivers a working component that integrates into the pipeline, transforming crypto mentions into actionable price and performance data with CSV and Google Sheets output.

## Validation Approach

**Critical**: Since real-time crypto messages are slow, we use the existing `scripts/historical_scraper.py` as the **primary validation method** throughout implementation. After implementing each component, update the historical scraper to integrate it, then run the scraper with 100 historical messages to validate. This provides instant feedback with real crypto data instead of waiting for live messages.

---

## - [ ] 1. Create address extractor with validation

Create the address extraction and validation system that identifies blockchain addresses from crypto mentions and validates their format.

**Implementation Details**:

- ✅ Create `core/address_extractor.py` with AddressExtractor class
- ✅ Implement Address dataclass with address, chain, is_valid, ticker, chain_specific fields
- ✅ Implement extract_addresses() to filter addresses from crypto_mentions list
- ✅ Implement identify_chain() to determine blockchain from address format
- ✅ Implement validate_evm_address() with regex pattern (0x + 40 hex chars) - supports Ethereum, BSC, Polygon, Arbitrum, Avalanche, Optimism
- ✅ Implement validate_solana_address() with base58 validation and 32-byte decoding
- ✅ Add \_looks_like_address() helper for quick filtering
- ✅ Return list of Address objects with validation status
- ✅ Add base58>=2.1.1 to requirements.txt

**External Verification with fetch MCP** (✅ COMPLETED):

- ✅ Verified Ethereum address format: https://ethereum.org/en/developers/docs/accounts/
- ✅ Verified Solana address format: https://docs.solana.com/terminology#account
- ✅ Verified BSC is EVM-compatible: https://docs.bnbchain.org/
- ✅ Verified base58 library: https://pypi.org/project/base58/

**Files to Create**:

- `core/address_extractor.py` (~150 lines)

**Validation** (✅ COMPLETED):

- ✅ EVM addresses detected (0x + 40 hex) - works for Ethereum, BSC, Polygon, Arbitrum, Avalanche, Optimism
- ✅ Solana addresses detected (base58, 32-44 chars with 32-byte decoding)
- ✅ Invalid addresses marked as is_valid=False
- ✅ Chain identified correctly (evm/solana/unknown)
- ✅ Empty list returned when no addresses found
- ✅ Test with EVM addresses: "0xdAC17F958D2ee523a2206206994597C13D831ec7" (USDT Ethereum) → valid
- ✅ Test with EVM addresses: "0x55d398326f99059fF775485246999027B3197955" (USDT BSC) → valid
- ✅ Test with Solana address: "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK" → valid
- ✅ Test with Solana address: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" (USDC Solana) → valid
- ✅ Test with invalid addresses: "0xINVALID", "0x123", "InvalidSolanaAddress" → filtered out
- ✅ Test with tickers: "BTC", "ETH", "SOL", "USDT" → not extracted (not addresses)

**Historical Scraper Verification** (⏳ NEXT STEP):

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. ⏳ Update historical scraper to integrate AddressExtractor
2. ⏳ Run `python scripts/historical_scraper.py --channel @erics_calls --limit 100`
3. ⏳ Verify logs show: "Extracting addresses from crypto mentions"
4. ⏳ Verify logs show: "Found X addresses: Y evm, Z solana"
5. ⏳ Verify logs show: "EVM address validated: 0x742d35..."
6. ⏳ Verify logs show: "Solana address validated: DYw8jCTf..."
7. ⏳ Verify logs show: "Invalid address detected: 0xINVALID" (if any)
8. ⏳ Verify logs show: "Address extraction completed in Xms"
9. ⏳ Review verification report for address extraction statistics
10. ⏳ Verify addresses extracted from real historical crypto mentions

**Status**: ✅ Component implemented and unit tested. Ready for historical scraper integration.

**Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5

---

## - [ ] 2. Create price engine with multi-API failover

Create the price fetching system with intelligent failover across multiple APIs and aggressive caching.

**Implementation Details**:

- Create `core/price_engine.py` with PriceEngine class
- Create PriceData dataclass with price_usd, market_cap, volume_24h, price_change_24h, source, timestamp
- Implement CoinGeckoAPI, BirdeyeAPI, MoralisAPI, DexScreenerAPI client classes
- Implement RateLimiter class with token bucket algorithm
- Initialize TTLCache with 5-minute TTL (300 seconds)
- Implement get_price() with cache check and API failover sequence
- Implement \_get_api_sequence() to order APIs by chain (Birdeye first for Solana)
- Add rate limiters for each API (CoinGecko: 45/min, Birdeye: 54/min, Moralis: 22/min)
- Create `config/price_config.py` with PriceConfig dataclass
- Update `config/settings.py` to load API keys from environment

**External Verification with fetch MCP**:

- Verify CoinGecko API: https://www.coingecko.com/en/api/documentation
- Verify Birdeye API: https://docs.birdeye.so/
- Verify Moralis API: https://docs.moralis.io/
- Verify DexScreener API: https://docs.dexscreener.com/
- Verify cachetools TTLCache: https://cachetools.readthedocs.io/en/stable/
- Verify aiohttp async HTTP: https://docs.aiohttp.org/en/stable/
- Verify rate limiting patterns: https://en.wikipedia.org/wiki/Token_bucket

**Files to Create**:

- `core/price_engine.py` (~300 lines)
- `config/price_config.py` (~30 lines)

**Files to Modify**:

- `config/settings.py` (add PriceConfig loading, ~50 lines added)
- `.env.example` (add API key variables)

**Validation**:

- Cache returns data within TTL (5 minutes)
- CoinGecko tried first for Ethereum addresses
- Birdeye tried first for Solana addresses
- Failover works when primary API fails
- Rate limiters enforce limits (45, 54, 22 req/min)
- PriceData includes source API name
- Returns None when all APIs fail
- Test cache hit: fetch same address twice → second fetch < 1ms
- Test failover: mock CoinGecko failure → Moralis succeeds
- Test rate limit: make 50 requests → delays after 45
- Test Solana: Birdeye tried before CoinGecko

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Update historical scraper to integrate PriceEngine
2. Run `python scripts/historical_scraper.py --channel @erics_calls --limit 100`
3. Verify logs show: "Checking cache for ethereum:0x742d35..."
4. Verify logs show: "Cache miss, fetching from APIs"
5. Verify logs show: "Trying CoinGecko API for ethereum:0x742d35..."
6. Verify logs show: "Price fetched from coingecko: $1,234.56"
7. Verify logs show: "Cached price data for ethereum:0x742d35..."
8. Run scraper again with same messages
9. Verify logs show: "Cache hit for ethereum:0x742d35..." (cache working)
10. Verify cache hit rate > 70% on second run
11. Mock API failure to test failover
12. Verify logs show: "coingecko failed: error_details"
13. Verify logs show: "Trying moralis API..." (failover working)
14. Review verification report for API usage statistics
15. Verify prices fetched for real addresses from historical messages

**Requirements**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5

---

## - [ ] 3. Create performance tracker with 7-day ATH tracking

Create the performance tracking system that monitors 7-day ATH for addresses with disk persistence and multi-table output.

**Implementation Details**:

- Create `core/performance_tracker.py` with PerformanceTracker class
- Create PerformanceData dataclass with address, chain, first_message_id, start_price, start_time, ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked
- Implement start_tracking() to create new tracking entries and write to PERFORMANCE table
- Implement update_price() to update current price, ATH, and sync to PERFORMANCE table
- Implement get_performance() to calculate performance metrics
- Implement to_table_row() to convert tracking data to PERFORMANCE table format (10 columns)
- Implement cleanup_old_entries() to remove entries older than 7 days
- Implement save_to_disk() to persist tracking data to internal JSON (fast recovery)
- Implement load_from_disk() to restore tracking data on startup
- Create `core/csv_table_writer.py` for generic CSV table operations (append/update)
- Create `config/performance_config.py` with PerformanceConfig dataclass
- Update `config/settings.py` to load performance configuration
- Create `data/performance/` directory structure

**Multi-Table Integration**:

- PerformanceTracker maintains internal JSON for fast lookups
- Writes to PERFORMANCE CSV table (10 columns) on every update
- Writes to PERFORMANCE Google Sheet on every update
- Coordinates with DataOutput for table writes

**External Verification with fetch MCP**:

- Verify JSON persistence: https://docs.python.org/3/library/json.html
- Verify pathlib usage: https://docs.python.org/3/library/pathlib.html
- Verify datetime operations: https://docs.python.org/3/library/datetime.html
- Verify dataclass usage: https://docs.python.org/3/library/dataclasses.html

**Files to Create**:

- `core/performance_tracker.py` (~300 lines) - Enhanced with multi-table output
- `core/csv_table_writer.py` (~150 lines) - Generic CSV table operations
- `config/performance_config.py` (~20 lines)
- `data/performance/` directory

**Files to Modify**:

- `config/settings.py` (add PerformanceConfig loading, ~30 lines added)
- `.env.example` (add performance variables)

**PERFORMANCE Table Format (10 columns)**:

```
address, chain, first_message_id, start_price, start_time,
ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked
```

**Validation**:

- New addresses start tracking with initial price
- ATH updates when current price exceeds previous ATH
- ATH multiplier calculated correctly (ath_since_mention / start_price)
- Current multiplier calculated correctly (current_price / start_price)
- Days tracked calculated from start_time
- Entries older than 7 days removed on cleanup
- Data persists to internal JSON file after changes
- Data loads from JSON file on startup
- Corrupted JSON handled gracefully (start fresh)
- PERFORMANCE CSV file created with 10 columns
- PERFORMANCE CSV updates existing rows (not append)
- PERFORMANCE Google Sheet updates existing rows
- Test new tracking: start_price=$1.00 → ath=$1.00, multiplier=1.0
- Test ATH update: price=$2.50 → ath=$2.50, multiplier=2.5
- Test persistence: save, restart, load → data intact
- Test cleanup: 8-day-old entry → removed from JSON and tables
- Test CSV update: same address → row updated, not duplicated
- Test Sheets update: same address → row updated, not duplicated

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Update historical scraper to integrate PerformanceTracker
2. Run `python scripts/historical_scraper.py --channel @erics_calls --limit 100`
3. Verify logs show: "Performance tracker initialized"
4. Verify logs show: "Loading tracking data from disk"
5. Verify logs show: "Started tracking X new addresses"
6. Verify logs show: "Started tracking 0x742d35... at $1.23"
7. Verify logs show: "Saved tracking data to disk"
8. Run scraper again with same messages (simulate price updates)
9. Verify logs show: "Loaded X tracking entries" (persistence working)
10. Verify logs show: "Updating price for 0x742d35...: $2.45"
11. Verify logs show: "New ATH for 0x742d35...: $2.45 (2.0x)" (if price increased)
12. Verify tracking data persists between runs
13. Review verification report for performance tracking statistics
14. Verify ATH multipliers calculated correctly

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 15.1, 15.2, 15.3, 15.4, 15.5

---

## - [ ] 4. Create multi-table data output with CSV and Google Sheets

Create the data output system that writes to 4 separate tables (MESSAGES, TOKEN_PRICES, PERFORMANCE, HISTORICAL) in both CSV and Google Sheets formats.

**Implementation Details**:

- Create `core/data_output.py` with MultiTableDataOutput class
- Create `core/csv_table_writer.py` with CSVTableWriter class for generic table operations
- Create `core/sheets_multi_table.py` with GoogleSheetsMultiTable class
- Implement write_message() to write to MESSAGES table (8 columns)
- Implement write_token_price() to update TOKEN_PRICES table (9 columns)
- Implement write_performance() to update PERFORMANCE table (10 columns)
- Implement write_historical() to update HISTORICAL table (8 columns)
- Implement daily file rotation for CSV (directory: output/YYYY-MM-DD/)
- Implement GoogleSheetsMultiTable with 4 sheets in single spreadsheet
- Implement conditional formatting rules (high confidence: green, high HDRB: bold, ATH > 2x: gold)
- Create `config/output_config.py` with OutputConfig dataclass
- Update `config/settings.py` to load output configuration
- Create `output/` and `credentials/` directories

**Multi-Table Architecture**:

- 4 separate CSV files per day (messages, token_prices, performance, historical)
- 4 separate sheets in single Google Spreadsheet
- MESSAGES table: append-only (new messages)
- TOKEN_PRICES table: update or insert (latest prices)
- PERFORMANCE table: update or insert (tracking data)
- HISTORICAL table: update or insert (CoinGecko data)

**External Verification with fetch MCP**:

- Verify CSV writing: https://docs.python.org/3/library/csv.html
- Verify gspread usage: https://docs.gspread.org/en/latest/
- Verify Google Sheets API: https://developers.google.com/sheets/api
- Verify oauth2client: https://oauth2client.readthedocs.io/
- Verify service account auth: https://cloud.google.com/iam/docs/service-accounts

**Files to Create**:

- `core/data_output.py` (~400 lines) - Multi-table coordinator
- `core/csv_table_writer.py` (~150 lines) - Generic CSV table writer
- `core/sheets_multi_table.py` (~250 lines) - Multi-sheet manager
- `config/output_config.py` (~30 lines)
- `output/` directory
- `credentials/` directory

**Files to Modify**:

- `config/settings.py` (add OutputConfig loading, ~40 lines added)
- `.env.example` (add Google Sheets variables)

**Table Formats**:

**MESSAGES Table (8 columns)**:

```
message_id, timestamp, channel_name, message_text,
hdrb_score, crypto_mentions, sentiment, confidence
```

**TOKEN_PRICES Table (9 columns)**:

```
address, chain, symbol, price_usd, market_cap,
volume_24h, price_change_24h, liquidity_usd, pair_created_at
```

**PERFORMANCE Table (10 columns)**:

```
address, chain, first_message_id, start_price, start_time,
ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked
```

**HISTORICAL Table (8 columns)**:

```
address, chain, all_time_ath, all_time_ath_date, distance_from_ath,
all_time_atl, all_time_atl_date, distance_from_atl
```

**Validation**:

- 4 CSV files created with headers (messages, token_prices, performance, historical)
- CSV files rotate daily (new directory per day: output/YYYY-MM-DD/)
- Google Sheets authenticated with service account
- 4 sheets created in single spreadsheet (Messages, Token Prices, Performance, Historical)
- MESSAGES: rows appended (no duplicates)
- TOKEN_PRICES: rows updated or inserted (by address)
- PERFORMANCE: rows updated or inserted (by address)
- HISTORICAL: rows updated or inserted (by address)
- Conditional formatting applied correctly
- High confidence messages have green background
- High HDRB messages have bold formatting
- ATH > 2x in PERFORMANCE have gold background
- Errors handled gracefully (CSV continues if Sheets fails)
- Test message write: message → row in MESSAGES table
- Test price update: same address → row updated in TOKEN_PRICES, not duplicated
- Test performance update: same address → row updated in PERFORMANCE, not duplicated
- Test file rotation: change date → new directory with 4 CSV files
- Test Sheets write: data appears in correct sheet
- Test formatting: high confidence message → green background in Messages sheet
- Test error handling: Sheets fails → CSV still works
- Test table linking: address in PERFORMANCE links to TOKEN_PRICES via VLOOKUP

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Update historical scraper to integrate MultiTableDataOutput
2. Run `python scripts/historical_scraper.py --channel @erics_calls --limit 100`
3. Verify logs show: "Multi-table data output initialized"
4. Verify logs show: "CSV output directory: output/YYYY-MM-DD/"
5. Verify logs show: "Google Sheets enabled: True"
6. Verify logs show: "Authenticating with Google Sheets"
7. Verify logs show: "Connected to spreadsheet: [spreadsheet_id]"
8. Verify logs show: "Created 4 sheets: Messages, Token Prices, Performance, Historical"
9. Verify logs show: "Writing message to MESSAGES table"
10. Verify logs show: "Updating TOKEN_PRICES table for address: 0x..."
11. Verify logs show: "Updating PERFORMANCE table for address: 0x..."
12. Verify logs show: "Updating HISTORICAL table for address: 0x..."
13. Verify 4 CSV files created in output/YYYY-MM-DD/ directory
14. Verify messages.csv contains 8 columns with data
15. Verify token_prices.csv contains 9 columns with data
16. Verify performance.csv contains 10 columns with data
17. Verify historical.csv contains 8 columns with data
18. Open Google Sheets and verify 4 sheets exist
19. Verify data in each sheet matches corresponding CSV
20. Verify conditional formatting applied (green for high confidence, etc.)
21. Test VLOOKUP: =VLOOKUP(A2,'Token Prices'!A:D,4,FALSE) returns price
22. Review verification report for multi-table output statistics

**Requirements**: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5, 12.1, 12.2, 12.3, 12.4, 12.5

---

## - [ ] 5. Integrate Part 3 pipeline with automatic historical scraping

Integrate all Part 3 components into main.py with automatic historical scraping for new channels, and verify the complete pipeline.

**Implementation Details**:

- Create `core/historical_scraper.py` with HistoricalScraper class for automatic scraping
- Implement scraped channels tracking with `data/scraped_channels.json`
- Create `config/historical_scraper_config.py` with HistoricalScraperConfig dataclass
- Update `config/settings.py` to load historical scraper configuration
- Update `main.py` to initialize AddressExtractor, PriceEngine, PerformanceTracker, DataOutput
- Update `main.py` to initialize HistoricalScraper and scrape new channels on startup
- Modify handle_message() to process through Part 3 pipeline
- Extract addresses from ProcessedMessage.crypto_mentions
- Fetch prices for each address
- Update performance tracking for each address
- Create EnrichedMessage with all data
- Write EnrichedMessage to CSV and Google Sheets
- Update console output to show addresses, prices, and performance
- Add error handling for each pipeline stage
- Update `requirements.txt` with new dependencies
- Update `README.md` with Part 3 features
- Update `.env.example` with historical scraper variables

**External Verification with fetch MCP**:

- Verify async integration: https://docs.python.org/3/library/asyncio-task.html
- Verify error handling: https://docs.python.org/3/tutorial/errors.html
- Verify requirements.txt format: https://pip.pypa.io/en/stable/reference/requirements-file-format/

**Files to Create**:

- `core/historical_scraper.py` (~200 lines)
- `config/historical_scraper_config.py` (~20 lines)

**Files to Modify**:

- `main.py` (integrate Part 3 pipeline + historical scraper, ~200 lines modified/added)
- `config/settings.py` (add HistoricalScraperConfig loading, ~30 lines added)
- `requirements.txt` (add new dependencies)
- `README.md` (document Part 3 features)
- `.env.example` (add historical scraper variables)

**New Dependencies to Add**:

```
aiohttp>=3.9.0
cachetools>=5.3.0
gspread>=5.12.0
oauth2client>=4.1.3
base58>=2.1.1
```

**Automatic Historical Scraping Verification**:

Test the automatic historical scraping feature integrated into the main pipeline:

1. Delete `data/scraped_channels.json` to simulate fresh start
2. Run `python main.py`
3. Verify logs show: "Configuration loaded successfully"
4. Verify logs show: "Historical scraper initialized"
5. Verify logs show: "Address extractor initialized"
6. Verify logs show: "Price engine initialized with 4 APIs"
7. Verify logs show: "Performance tracker initialized"
8. Verify logs show: "Data output initialized"
9. Verify logs show: "Connected to Telegram successfully"
10. Verify logs show: "Channel [name] not scraped, fetching 100 historical messages"
11. Verify logs show: "Processing historical message X/100"
12. Verify logs show: "Found Y crypto-relevant messages with addresses"
13. Verify logs show: "Extracting addresses from crypto mentions"
14. Verify logs show: "Fetching prices for Z addresses"
15. Verify logs show: "Price fetched from [api]: $X.XX"
16. Verify logs show: "Started tracking N new addresses"
17. Verify logs show: "Writing enriched messages to CSV"
18. Verify logs show: "Writing enriched messages to Google Sheets"
19. Verify logs show: "Historical scraping complete for [channel]"
20. Verify logs show: "Starting real-time monitoring"
21. Verify `data/scraped_channels.json` created with channel ID
22. Verify CSV file exists with historical messages
23. Verify Google Sheets contains historical messages
24. Stop system (Ctrl+C)
25. Run `python main.py` again
26. Verify logs show: "Channel [name] already scraped, skipping"
27. Verify logs show: "Starting real-time monitoring" (no historical scraping)
28. Verify system starts faster on second run

**Manual Historical Scraper Verification** (for testing/debugging):

Use the standalone `scripts/historical_scraper.py` for manual testing:

1. Run `python scripts/historical_scraper.py --channel @erics_calls --limit 100`
2. Verify all Part 3 components process messages correctly
3. Review generated verification report for statistics
4. Verify CSV and Google Sheets output
5. Run again to test cache effectiveness (> 70% hit rate)
6. Verify performance tracking persists between runs

**Success Criteria**:

- Automatic historical scraping runs on first startup for new channels
- Historical scraper processes 100 messages successfully before real-time monitoring
- Scraped channels tracked in `data/scraped_channels.json`
- Second startup skips historical scraping for already-scraped channels
- All Part 3 components initialize successfully
- Addresses extracted from real crypto mentions in historical data
- Prices fetched from APIs with failover working
- Cache effectiveness demonstrated (>70% hit rate on repeated scrapes)
- Performance tracking works across system restarts
- CSV files created and populated with all 23 columns
- Google Sheets updated with all enriched messages
- Conditional formatting applied correctly
- Processing completes in < 500ms per message average
- Errors handled gracefully without crashes
- Real-time monitoring starts after historical scraping completes
- System provides immediate data context before monitoring live messages

**Requirements**: 11.1, 11.2, 11.3, 11.4, 11.5, 13.1, 13.2, 13.3, 13.4, 13.5, 14.1, 14.2, 14.3, 14.4, 14.5

---

## Implementation Notes

### Using fetch MCP Server for Verification

Before implementing each task, use the fetch MCP server to:

1. Verify official documentation for APIs and libraries
2. Check API references for correct usage patterns
3. Validate best practices from authoritative sources
4. Clarify any ambiguous implementation details

**Example fetch usage**:

```
Use fetch MCP to verify CoinGecko API:
- URL: https://www.coingecko.com/en/api/documentation
- Extract: Price endpoint, rate limits, response format
```

```
Use fetch MCP to verify gspread authentication:
- URL: https://docs.gspread.org/en/latest/oauth2.html
- Extract: Service account setup, authentication flow
```

### Task Dependencies

- Task 1 (address extractor) can be implemented independently
- Task 2 (price engine) depends on Task 1 (needs Address objects)
- Task 3 (performance tracker) depends on Task 2 (needs price data)
- Task 4 (data output) depends on Tasks 1-3 (needs all data)
- Task 5 (integration) depends on Tasks 1-4 (integrates everything)

### Testing Approach

Each task should be tested immediately after implementation:

1. **Unit-level**: Test the component in isolation with mock data
2. **Integration-level**: Test with previous components
3. **Pipeline-level**: Test complete flow with real Telegram messages

### API Key Setup

Before starting Task 2, obtain API keys:

1. **CoinGecko**: Sign up at https://www.coingecko.com/en/api
2. **Birdeye**: Sign up at https://birdeye.so/
3. **Moralis**: Sign up at https://moralis.io/
4. **Google Sheets**: Create service account at https://console.cloud.google.com/

Add to `.env`:

```
COINGECKO_API_KEY=your_key_here
BIRDEYE_API_KEY=your_key_here
MORALIS_API_KEY=your_key_here
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
```

### Performance Requirements

All processing must complete within performance targets:

- Address extraction: < 10ms per message
- Price fetch (cached): < 1ms
- Price fetch (API): < 300ms per address
- Performance update: < 50ms per address
- CSV write: < 10ms
- Google Sheets write: < 100ms
- **Total pipeline**: < 500ms per message

Use `time.perf_counter()` to track processing time and log warnings if exceeded.

### Error Handling Strategy

All components must implement graceful degradation:

- **Address extraction fails**: Return empty list, continue processing
- **Price fetch fails**: Return None, continue with other addresses
- **Performance tracking fails**: Log error, continue processing
- **CSV write fails**: Log error, try Google Sheets
- **Google Sheets write fails**: Log error, continue with CSV only

Never crash on processing errors - always create an EnrichedMessage object.

### Caching Strategy

Price Engine caching is critical for performance:

- **TTL**: 5 minutes (300 seconds)
- **Cache key**: `f"{chain}:{address}"`
- **Max size**: 1000 entries
- **Expected hit rate**: >70% after warmup
- **Benefit**: Reduces API calls by ~80%

### Rate Limiting

Enforce rate limits with 90% buffer:

- **CoinGecko**: 50 req/min → enforce 45 req/min
- **Birdeye**: 60 req/min → enforce 54 req/min
- **Moralis**: 25 req/min → enforce 22 req/min
- **DexScreener**: No limit (no key required)

### File Structure After Completion

```
crypto-intelligence/
├── config/
│   ├── __init__.py
│   ├── settings.py                    # Updated with Part 3 configs
│   ├── price_config.py                # NEW
│   ├── performance_config.py          # NEW
│   ├── output_config.py               # NEW
│   ├── historical_scraper_config.py   # NEW
│   └── channels.json
├── core/
│   ├── __init__.py
│   ├── telegram_monitor.py            # Existing
│   ├── message_processor.py           # Existing
│   ├── address_extractor.py           # NEW
│   ├── price_engine.py                # NEW
│   ├── performance_tracker.py         # NEW
│   ├── data_output.py                 # NEW
│   └── historical_scraper.py          # NEW - automatic scraping
├── utils/
│   ├── __init__.py
│   ├── logger.py                      # Existing
│   └── error_handler.py               # Existing
├── data/
│   ├── performance/                   # NEW
│   │   └── tracking.json
│   └── scraped_channels.json          # NEW - tracks scraped channels
├── output/                            # NEW
│   └── crypto_intelligence_YYYY-MM-DD.csv
├── credentials/                       # NEW
│   └── google_service_account.json
├── scripts/
│   └── historical_scraper.py          # Existing - manual scraping tool
├── logs/
├── main.py                            # Updated with Part 3 + auto scraping
├── requirements.txt                   # Updated with new dependencies
├── .env
├── .env.example                       # Updated with new variables
└── README.md                          # Updated with Part 3 features
```

### Multi-Table CSV Output Format (35 Columns Total Across 4 Tables)

**TABLE 1: MESSAGES (8 columns)** - Crypto signals from channels

```
message_id, timestamp, channel_name, message_text,
hdrb_score, crypto_mentions, sentiment, confidence
```

**TABLE 2: TOKEN_PRICES (9 columns)** - Current market data

```
address, chain, symbol, price_usd, market_cap,
volume_24h, price_change_24h, liquidity_usd, pair_created_at
```

**TABLE 3: PERFORMANCE (10 columns)** - ROI since mention

```
address, chain, first_message_id, start_price, start_time,
ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked
```

**TABLE 4: HISTORICAL (8 columns)** - All-time context (optional)

```
address, chain, all_time_ath, all_time_ath_date, distance_from_ath,
all_time_atl, all_time_atl_date, distance_from_atl
```

**File Structure**:

```
output/
├── 2024-11-08/
│   ├── messages.csv
│   ├── token_prices.csv
│   ├── performance.csv
│   └── historical.csv
```

### Example Console Output

```
================================================================================
[2024-11-07 14:32:15] [Eric Cryptomans Journal] (ID: 12345)
================================================================================
📊 HDRB Score: 67.5/100 (IC: 675.0)
   Engagement: 50 forwards, 300 reactions, 25 replies

💰 Crypto Mentions: BTC, 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

💎 Addresses:
   • 0x742d35... (ethereum) - $1,234.56
     📊 Performance: 2.5x ATH (tracked 3 days)

📈 Sentiment: Positive (+0.75)

🎯 Confidence: 🟢 HIGH (0.82)

BTC and ETH looking strong! Check out this gem: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Already 2.5x from when I first mentioned it!
================================================================================
✅ Written to: crypto_intelligence_2024-11-07.csv
✅ Written to: Google Sheets
================================================================================
```

### Configuration Example

**.env additions**:

```
# Part 3: Address Extraction & Price Tracking

# API Keys
COINGECKO_API_KEY=your_coingecko_key
BIRDEYE_API_KEY=your_birdeye_key
MORALIS_API_KEY=your_moralis_key

# Price Engine
PRICE_CACHE_TTL=300
PRICE_RATE_LIMIT_BUFFER=0.9

# Performance Tracking
PERFORMANCE_UPDATE_INTERVAL=7200
PERFORMANCE_TRACKING_DAYS=7
PERFORMANCE_DATA_DIR=data/performance

# Data Output
CSV_OUTPUT_DIR=output
CSV_ROTATE_DAILY=true
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Historical Scraper (Automatic)
HISTORICAL_SCRAPER_ENABLED=true
HISTORICAL_SCRAPER_MESSAGE_LIMIT=100
HISTORICAL_SCRAPER_SCRAPED_CHANNELS_FILE=data/scraped_channels.json
```

---

## Verification Checklist

After completing all tasks, verify:

### Component Verification

- [ ] Address extractor validates Ethereum addresses
- [ ] Address extractor validates Solana addresses
- [ ] Address extractor identifies chains correctly
- [ ] Price engine checks cache before API calls
- [ ] Price engine tries APIs in correct order
- [ ] Price engine failover works when APIs fail
- [ ] Rate limiters enforce limits correctly
- [ ] Performance tracker starts tracking new addresses
- [ ] Performance tracker updates ATH correctly
- [ ] Performance tracker persists data to disk
- [ ] Performance tracker loads data on startup
- [ ] Performance tracker cleans up old entries
- [ ] CSV output creates files with headers
- [ ] CSV output rotates files daily
- [ ] Google Sheets output authenticates successfully
- [ ] Google Sheets output appends rows
- [ ] Conditional formatting applied correctly

### Logging Verification

- [ ] Startup logs show all components initialized
- [ ] Address extraction logs show found addresses
- [ ] Price fetching logs show API attempts
- [ ] Price fetching logs show cache hits/misses
- [ ] Price fetching logs show failover attempts
- [ ] Performance tracking logs show new tracking
- [ ] Performance tracking logs show ATH updates
- [ ] Data output logs show CSV writes
- [ ] Data output logs show Google Sheets writes
- [ ] Error logs show graceful error handling
- [ ] Shutdown logs show data persistence

### Pipeline Verification

- [ ] System starts without errors
- [ ] Configuration loads successfully
- [ ] All Part 3 components initialize
- [ ] Telegram connection established
- [ ] Crypto-relevant messages processed
- [ ] Addresses extracted from mentions
- [ ] Prices fetched from APIs
- [ ] Performance tracking works
- [ ] CSV files created and populated
- [ ] Google Sheets updated
- [ ] Console shows enriched data
- [ ] Cache reduces API calls
- [ ] Processing completes in < 500ms
- [ ] Errors handled gracefully
- [ ] System runs stable for 60+ seconds
- [ ] Ctrl+C triggers clean shutdown
- [ ] Data persists across restarts

### Performance Verification

- [ ] Address extraction < 10ms per message
- [ ] Price fetch (cached) < 1ms
- [ ] Price fetch (API) < 300ms per address
- [ ] Performance update < 50ms per address
- [ ] CSV write < 10ms
- [ ] Google Sheets write < 100ms
- [ ] Total pipeline < 500ms per message
- [ ] Cache hit rate > 70% after warmup
- [ ] No memory leaks during extended operation
- [ ] CPU usage < 30% during message bursts

### Data Verification

- [ ] CSV files contain all 23 columns
- [ ] CSV data matches message content
- [ ] Google Sheets contains same data as CSV
- [ ] Conditional formatting visible in Sheets
- [ ] Performance tracking data accurate
- [ ] ATH multipliers calculated correctly
- [ ] Tracking data persists across restarts
- [ ] Old entries cleaned up after 7 days

---

## Implementation Notes

### Primary Validation Method: Historical Scraper

**Critical**: Since real-time crypto messages are slow, the existing `scripts/historical_scraper.py` is the **primary validation method** for all Part 3 components.

**Workflow for Each Task**:

1. Implement the component (e.g., AddressExtractor)
2. Update `scripts/historical_scraper.py` to integrate the new component
3. Run `python scripts/historical_scraper.py --channel @erics_calls --limit 100`
4. Verify component works with 100 real historical messages
5. Review verification report for statistics
6. Fix any issues and re-run scraper
7. Move to next task once verification passes

**Benefits**:

- Instant validation with 100 test cases
- Real crypto addresses and mentions from historical data
- Fast iteration (no waiting for real-time messages)
- Comprehensive statistics in verification report
- Cache and performance tracking can be tested across multiple runs

**Historical Scraper Updates Required**:

- Task 1: Add AddressExtractor integration
- Task 2: Add PriceEngine integration with API statistics
- Task 3: Add PerformanceTracker integration with persistence testing
- Task 4: Add DataOutput integration with CSV and Google Sheets
- Task 5: Complete pipeline with all components and enhanced reporting

---

## Final Verification Checklist

Complete this checklist after finishing all tasks:

### Component Verification (via Historical Scraper)

- [ ] Address extractor validates Ethereum addresses
- [ ] Address extractor validates Solana addresses
- [ ] Address extractor identifies chains correctly
- [ ] Price engine checks cache before API calls
- [ ] Price engine tries APIs in correct order
- [ ] Price engine failover works when APIs fail
- [ ] Rate limiters enforce limits correctly
- [ ] Performance tracker starts tracking new addresses
- [ ] Performance tracker updates ATH correctly
- [ ] Performance tracker persists data to disk
- [ ] Performance tracker loads data on startup
- [ ] Performance tracker cleans up old entries
- [ ] CSV output creates files with headers
- [ ] CSV output rotates files daily
- [ ] Google Sheets output authenticates successfully
- [ ] Google Sheets output appends rows
- [ ] Conditional formatting applied correctly

### Historical Scraper Verification

- [ ] Scraper processes 100 messages successfully
- [ ] All Part 3 components integrated into scraper
- [ ] Addresses extracted from real historical crypto mentions
- [ ] Prices fetched from multiple APIs
- [ ] API usage statistics shown in report
- [ ] Cache hit rate > 70% on second run
- [ ] Performance tracking works across scraper runs
- [ ] CSV output contains all enriched data (23 columns)
- [ ] Google Sheets output matches CSV data
- [ ] Conditional formatting visible in Sheets
- [ ] Verification report generated with comprehensive statistics
- [ ] Processing performance meets targets (< 500ms per message avg)
- [ ] All logging requirements demonstrated with real data

---

**Implementation Order**:

1. Task 1: Address extractor + update historical scraper
2. Task 2: Price engine + update historical scraper
3. Task 3: Performance tracker + update historical scraper
4. Task 4: Data output + update historical scraper
5. Task 5: Complete pipeline integration + final scraper enhancements

**Note**: After each task, run the historical scraper to validate the component with 100 real messages. This is the primary validation method since real-time crypto messages are slow.
