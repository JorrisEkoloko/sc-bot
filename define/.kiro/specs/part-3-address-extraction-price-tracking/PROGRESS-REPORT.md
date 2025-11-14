# Part 3: Address Extraction & Price Tracking - Progress Report

## 📋 Overview

**Status**: Ready to Begin  
**Prerequisites**: Part 2 Complete ✅  
**Dependencies**: All Part 2 components verified and working  
**Target**: Implement address extraction, price engine, performance tracking, and data output

---

## 🎯 Part 3 Objectives

Transform processed messages with crypto mentions into actionable intelligence by:

1. Extracting blockchain addresses from messages
2. Fetching real-time price data from multiple APIs
3. Tracking 7-day ATH performance
4. Outputting results to CSV and Google Sheets

---

## ✅ Completed Prerequisites (Part 2)

### Infrastructure Ready

- ✅ **TelegramMonitor** - Message reception working
- ✅ **MessageProcessor** - Pipeline coordinator ready
- ✅ **CryptoDetector** - Identifies crypto mentions (tickers + addresses)
- ✅ **ProcessedMessage** - Data structure with crypto_mentions field
- ✅ **ErrorHandler** - Retry logic and circuit breaker available
- ✅ **Configuration System** - Settings loader ready for API keys
- ✅ **Logging System** - Structured logging in place

### Verified Capabilities

- ✅ Crypto detection working (19% detection rate on test data)
- ✅ Ticker symbols detected: BTC, ETH, SOL, AVAX, NEAR
- ✅ Ethereum addresses detected: 0x[40 hex chars]
- ✅ Solana addresses detected: base58 format
- ✅ Performance: 0.82ms average processing time
- ✅ Error handling: Zero errors in 42-message test

### Available Data

From Part 2, we have:

```python
ProcessedMessage:
    crypto_mentions: list        # ['BTC', '0x...', 'base58...']
    is_crypto_relevant: bool     # True if mentions found
    message_text: str            # Full message content
    timestamp: datetime          # When message was sent
    channel_name: str            # Source channel
    # ... other fields
```

---

## 🔧 Part 3 Components to Implement

### 1. Address Extractor (Enhanced)

**Purpose**: Extract and validate blockchain addresses from crypto_mentions

**Current State**:

- CryptoDetector finds addresses in text
- Addresses included in crypto_mentions list
- No validation or chain identification

**Needed**:

```python
class AddressExtractor:
    """Extract and validate blockchain addresses."""

    def extract_addresses(self, crypto_mentions: list) -> list[Address]:
        """
        Extract addresses from crypto mentions.

        Returns list of Address objects with:
        - address: str
        - chain: str ('ethereum', 'solana', 'bsc', etc.)
        - is_valid: bool
        """
        pass

    def validate_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum address format and checksum."""
        pass

    def validate_solana_address(self, address: str) -> bool:
        """Validate Solana address format."""
        pass

    def identify_chain(self, address: str) -> str:
        """Identify blockchain from address format."""
        pass
```

**Integration Point**: After CryptoDetector in MessageProcessor pipeline

---

### 2. Price Engine (Multi-API)

**Purpose**: Fetch real-time price data with intelligent failover

**APIs to Integrate**:

1. **CoinGecko** (Primary) - 50 req/min, free tier
2. **Birdeye** (Solana-focused) - 60 req/min
3. **Moralis** (Multi-chain) - 25 req/min
4. **DexScreener** (Fallback) - No key required

**Needed**:

```python
class PriceEngine:
    """Multi-API price fetching with failover."""

    def __init__(self, api_keys: dict, error_handler: ErrorHandler):
        """Initialize with API keys and error handler."""
        self.coingecko = CoinGeckoAPI(api_keys['coingecko'])
        self.birdeye = BirdeyeAPI(api_keys['birdeye'])
        self.moralis = MoralisAPI(api_keys['moralis'])
        self.dexscreener = DexScreenerAPI()  # No key needed
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5-min cache

    async def get_price(self, address: str, chain: str) -> PriceData:
        """
        Get price with failover.

        Returns PriceData with:
        - price_usd: float
        - market_cap: float
        - volume_24h: float
        - price_change_24h: float
        - source: str (which API provided data)
        - timestamp: datetime
        """
        # Try cache first
        # Try CoinGecko
        # Fallback to Birdeye (if Solana)
        # Fallback to Moralis
        # Fallback to DexScreener
        # Return None if all fail
        pass

    async def get_price_by_ticker(self, ticker: str) -> PriceData:
        """Get price by ticker symbol (BTC, ETH, etc.)."""
        pass

    def _should_use_cache(self, cache_entry) -> bool:
        """Check if cached data is still valid."""
        pass
```

**Rate Limiting**:

- Implement per-API rate limiters
- Track requests per minute
- Delay when approaching limits
- Log rate limit warnings

**Caching Strategy**:

- TTL: 5 minutes (300 seconds)
- Cache key: f"{chain}:{address}"
- Reduces API calls by ~80%

---

### 3. Performance Tracker (7-Day ATH)

**Purpose**: Track price performance over 7 days

**Needed**:

```python
class PerformanceTracker:
    """Track 7-day ATH performance."""

    def __init__(self, data_dir: str = "data/performance"):
        """Initialize with data directory."""
        self.data_dir = Path(data_dir)
        self.tracking_data = {}  # address -> performance data

    def start_tracking(self, address: str, chain: str, initial_price: float):
        """
        Start tracking a new address.

        Creates tracking entry with:
        - address: str
        - chain: str
        - start_price: float
        - start_time: datetime
        - ath_price: float (initially = start_price)
        - ath_time: datetime
        - current_price: float
        - last_update: datetime
        """
        pass

    async def update_price(self, address: str, current_price: float):
        """
        Update current price and ATH if needed.

        Updates:
        - current_price
        - last_update
        - ath_price (if current > ath)
        - ath_time (if new ATH)
        """
        pass

    def get_performance(self, address: str) -> PerformanceData:
        """
        Get performance metrics.

        Returns PerformanceData with:
        - address: str
        - days_tracked: int
        - start_price: float
        - current_price: float
        - ath_price: float
        - ath_multiplier: float (ath / start)
        - current_multiplier: float (current / start)
        - time_to_ath: timedelta
        - is_at_ath: bool
        """
        pass

    def cleanup_old_entries(self, days: int = 7):
        """Remove entries older than specified days."""
        pass

    def save_to_disk(self):
        """Persist tracking data to JSON file."""
        pass

    def load_from_disk(self):
        """Load tracking data from JSON file."""
        pass
```

**Update Strategy**:

- Update every 2 hours (configurable)
- Only update tracked addresses (not all mentions)
- Persist to disk after each update
- Load on startup for continuity

---

### 4. Data Output (CSV + Google Sheets)

**Purpose**: Export processed data to CSV and Google Sheets

**CSV Output**:

```python
class CSVOutput:
    """Output to CSV files."""

    def __init__(self, output_dir: str = "output"):
        """Initialize with output directory."""
        self.output_dir = Path(output_dir)
        self.current_file = None

    def write_message(self, enriched_message: EnrichedMessage):
        """
        Write message to CSV.

        Columns (26 total):
        - timestamp
        - channel_name
        - message_id
        - message_text
        - hdrb_score
        - hdrb_raw
        - crypto_mentions (comma-separated)
        - addresses (comma-separated)
        - sentiment
        - sentiment_score
        - confidence
        - is_high_confidence
        - price_usd
        - market_cap
        - volume_24h
        - price_change_24h
        - ath_price
        - ath_multiplier
        - current_multiplier
        - days_tracked
        - forwards
        - reactions
        - replies
        - views
        - processing_time_ms
        - error
        """
        pass

    def rotate_file(self):
        """Create new file for new day."""
        pass
```

**Google Sheets Output**:

```python
class GoogleSheetsOutput:
    """Output to Google Sheets with conditional formatting."""

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """Initialize with service account credentials."""
        self.client = gspread.service_account(credentials_path)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        self.worksheet = self.spreadsheet.sheet1

    def write_message(self, enriched_message: EnrichedMessage):
        """Append message to Google Sheets."""
        pass

    def apply_conditional_formatting(self):
        """
        Apply formatting rules:
        - High confidence: Green background
        - Crypto relevant: Blue text
        - High HDRB: Bold
        - ATH > 2x: Gold background
        """
        pass

    def update_header(self):
        """Update header row with column names."""
        pass
```

---

## 📊 Enhanced Data Structure

### EnrichedMessage (extends ProcessedMessage)

```python
@dataclass
class EnrichedMessage(ProcessedMessage):
    """Message with price and performance data."""

    # Address extraction
    addresses: list[Address] = field(default_factory=list)

    # Price data
    price_data: Optional[PriceData] = None

    # Performance tracking
    performance_data: Optional[PerformanceData] = None

    # Output metadata
    output_timestamp: datetime = None
    output_error: Optional[str] = None
```

### Address

```python
@dataclass
class Address:
    """Blockchain address with metadata."""
    address: str
    chain: str  # 'ethereum', 'solana', 'bsc', etc.
    is_valid: bool
    ticker: Optional[str] = None  # Associated ticker if known
```

### PriceData

```python
@dataclass
class PriceData:
    """Price information from API."""
    price_usd: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    source: str = "unknown"  # Which API provided data
    timestamp: datetime = None
```

### PerformanceData

```python
@dataclass
class PerformanceData:
    """7-day ATH performance metrics."""
    address: str
    chain: str
    start_price: float
    current_price: float
    ath_price: float
    ath_multiplier: float  # ath / start
    current_multiplier: float  # current / start
    days_tracked: int
    time_to_ath: Optional[timedelta] = None
    is_at_ath: bool = False
```

---

## 🔄 Updated Pipeline Flow

```
ProcessedMessage (from Part 2)
    ↓
AddressExtractor
    ├─► Extract addresses from crypto_mentions
    ├─► Validate address formats
    ├─► Identify blockchain chains
    └─► Returns: list[Address]
    ↓
PriceEngine
    ├─► Check cache (5-min TTL)
    ├─► Fetch price from APIs (with failover)
    │   ├─► Try CoinGecko
    │   ├─► Fallback to Birdeye (Solana)
    │   ├─► Fallback to Moralis
    │   └─► Fallback to DexScreener
    ├─► Update cache
    └─► Returns: PriceData
    ↓
PerformanceTracker
    ├─► Check if address already tracked
    ├─► Start tracking if new
    ├─► Update current price
    ├─► Update ATH if needed
    └─► Returns: PerformanceData
    ↓
EnrichedMessage (complete data)
    ↓
DataOutput
    ├─► Write to CSV
    └─► Write to Google Sheets
```

---

## 🔑 Configuration Requirements

### API Keys Needed

```env
# CoinGecko API
COINGECKO_API_KEY=your_key_here

# Birdeye API (Solana)
BIRDEYE_API_KEY=your_key_here

# Moralis API
MORALIS_API_KEY=your_key_here

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here

# Performance Tracking
PERFORMANCE_UPDATE_INTERVAL=7200  # 2 hours in seconds
PERFORMANCE_TRACKING_DAYS=7

# Output
CSV_OUTPUT_DIR=output
CSV_ROTATE_DAILY=true
```

### Config Classes Needed

```python
@dataclass
class PriceConfig:
    """Price engine configuration."""
    coingecko_api_key: str
    birdeye_api_key: str
    moralis_api_key: str
    cache_ttl: int = 300  # 5 minutes
    rate_limit_buffer: float = 0.9  # Use 90% of rate limit

@dataclass
class PerformanceConfig:
    """Performance tracking configuration."""
    update_interval: int = 7200  # 2 hours
    tracking_days: int = 7
    data_dir: str = "data/performance"

@dataclass
class OutputConfig:
    """Data output configuration."""
    csv_output_dir: str = "output"
    csv_rotate_daily: bool = True
    google_sheets_enabled: bool = True
    google_sheets_credentials: str = ""
    google_sheets_spreadsheet_id: str = ""
```

---

## 📁 File Structure for Part 3

```
crypto-intelligence/
├── core/
│   ├── address_extractor.py     # NEW - Extract & validate addresses
│   ├── price_engine.py          # NEW - Multi-API price fetching
│   ├── performance_tracker.py   # NEW - 7-day ATH tracking
│   └── data_output.py           # NEW - CSV + Google Sheets
│
├── config/
│   ├── price_config.py          # NEW - Price engine config
│   ├── performance_config.py    # NEW - Performance tracking config
│   └── output_config.py         # NEW - Output config
│
├── data/
│   └── performance/             # NEW - Performance tracking data
│       └── tracking.json
│
├── output/                      # NEW - CSV output directory
│   └── crypto_intelligence_YYYY-MM-DD.csv
│
├── credentials/                 # NEW - API credentials
│   └── google_service_account.json
│
└── .env                         # UPDATE - Add new API keys
```

---

## 🎯 Implementation Tasks

### Task 1: Address Extractor

**Estimated Time**: 2-3 hours  
**Dependencies**: None (uses existing crypto_mentions)  
**Files**: `core/address_extractor.py`

**Subtasks**:

1. Create Address dataclass
2. Implement extract_addresses()
3. Implement validate_ethereum_address()
4. Implement validate_solana_address()
5. Implement identify_chain()
6. Add unit tests
7. Integrate into MessageProcessor

### Task 2: Price Engine

**Estimated Time**: 4-5 hours  
**Dependencies**: API keys, address extractor  
**Files**: `core/price_engine.py`, `config/price_config.py`

**Subtasks**:

1. Create PriceData dataclass
2. Implement CoinGeckoAPI wrapper
3. Implement BirdeyeAPI wrapper
4. Implement MoralisAPI wrapper
5. Implement DexScreenerAPI wrapper
6. Implement caching with TTLCache
7. Implement rate limiting
8. Implement failover logic
9. Add error handling
10. Add unit tests
11. Integrate into pipeline

### Task 3: Performance Tracker

**Estimated Time**: 3-4 hours  
**Dependencies**: Price engine  
**Files**: `core/performance_tracker.py`, `config/performance_config.py`

**Subtasks**:

1. Create PerformanceData dataclass
2. Implement start_tracking()
3. Implement update_price()
4. Implement get_performance()
5. Implement cleanup_old_entries()
6. Implement save_to_disk()
7. Implement load_from_disk()
8. Add scheduled updates (every 2 hours)
9. Add unit tests
10. Integrate into pipeline

### Task 4: Data Output

**Estimated Time**: 3-4 hours  
**Dependencies**: All previous tasks  
**Files**: `core/data_output.py`, `config/output_config.py`

**Subtasks**:

1. Create EnrichedMessage dataclass
2. Implement CSVOutput class
3. Implement GoogleSheetsOutput class
4. Implement conditional formatting
5. Implement file rotation
6. Add error handling
7. Add unit tests
8. Integrate into pipeline

### Task 5: Integration & Testing

**Estimated Time**: 2-3 hours  
**Dependencies**: All tasks complete  
**Files**: `main.py`, test files

**Subtasks**:

1. Update main.py with new pipeline
2. Update configuration loading
3. Create integration tests
4. Test with historical scraper
5. Verify CSV output
6. Verify Google Sheets output
7. Performance testing
8. Documentation updates

---

## 🔍 Testing Strategy

### Unit Tests

- Test each component in isolation
- Mock API responses
- Test error handling
- Test edge cases

### Integration Tests

- Test complete pipeline flow
- Test with real API calls (limited)
- Test failover scenarios
- Test rate limiting

### End-to-End Tests

- Run historical scraper with Part 3
- Verify CSV output format
- Verify Google Sheets output
- Verify performance tracking
- Check for memory leaks

---

## 📊 Success Criteria

### Functional Requirements

- ✅ Addresses extracted and validated
- ✅ Prices fetched from multiple APIs
- ✅ Failover working correctly
- ✅ Performance tracked over 7 days
- ✅ Data output to CSV
- ✅ Data output to Google Sheets
- ✅ Conditional formatting applied

### Performance Requirements

- ✅ Total processing < 500ms per message (including API calls)
- ✅ Cache hit rate > 70%
- ✅ API success rate > 95%
- ✅ Zero data loss
- ✅ Memory usage stable

### Quality Requirements

- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ Error handling comprehensive
- ✅ Logging detailed
- ✅ Documentation complete

---

## 🚨 Known Challenges

### 1. API Rate Limits

**Challenge**: Multiple APIs with different rate limits  
**Solution**:

- Implement per-API rate limiters
- Use caching aggressively (5-min TTL)
- Implement intelligent failover
- Monitor rate limit usage

### 2. Price Data Availability

**Challenge**: Not all tokens available on all APIs  
**Solution**:

- Try multiple APIs in sequence
- Log which API provided data
- Return None if all fail
- Don't crash on missing data

### 3. Address Validation

**Challenge**: Different chains have different formats  
**Solution**:

- Implement chain-specific validation
- Use checksums for Ethereum
- Use base58 validation for Solana
- Mark invalid addresses clearly

### 4. Performance Tracking Persistence

**Challenge**: Need to persist data across restarts  
**Solution**:

- Save to JSON after each update
- Load on startup
- Implement cleanup for old entries
- Handle corrupted files gracefully

### 5. Google Sheets Rate Limits

**Challenge**: Google Sheets API has rate limits  
**Solution**:

- Batch writes when possible
- Implement retry logic
- Fall back to CSV-only if needed
- Log Google Sheets errors

---

## 📈 Expected Outcomes

### Data Flow

```
42 messages (from Part 2 test)
    ↓
8 crypto-relevant messages (19%)
    ↓
~10-15 addresses extracted
    ↓
~8-12 prices fetched (some may fail)
    ↓
~8-12 performance entries created
    ↓
All data output to CSV + Google Sheets
```

### Performance Metrics

- Address extraction: < 10ms per message
- Price fetching: 100-300ms per address (with cache: < 1ms)
- Performance update: < 50ms per address
- CSV write: < 10ms per message
- Google Sheets write: 50-100ms per message
- **Total**: < 500ms per message (worst case)

### Output Format

**CSV Columns** (26 total):

1. timestamp
2. channel_name
3. message_id
4. message_text
5. hdrb_score
6. hdrb_raw
7. crypto_mentions
8. addresses
9. sentiment
10. sentiment_score
11. confidence
12. is_high_confidence
13. price_usd
14. market_cap
15. volume_24h
16. price_change_24h
17. ath_price
18. ath_multiplier
19. current_multiplier
20. days_tracked
21. forwards
22. reactions
23. replies
24. views
25. processing_time_ms
26. error

---

## 🔗 Integration Points

### From Part 2

**Input**: ProcessedMessage with:

- crypto_mentions: list
- is_crypto_relevant: bool
- All other Part 2 fields

**Used By**:

- AddressExtractor (uses crypto_mentions)
- PriceEngine (uses extracted addresses)
- PerformanceTracker (uses price data)
- DataOutput (uses all fields)

### To Part 4 (Future)

**Output**: EnrichedMessage with:

- All Part 2 fields
- addresses: list[Address]
- price_data: PriceData
- performance_data: PerformanceData

**Will Be Used By**:

- MarketAnalyzer (market cap classification)
- ChannelReputation (outcome-based learning)
- SignalScorer (holistic scoring)

---

## 📝 Documentation Needed

### User Documentation

- API key setup guide
- Google Sheets setup guide
- Configuration guide
- Output format reference
- Troubleshooting guide

### Developer Documentation

- Architecture overview
- Component interaction diagram
- API integration details
- Data flow diagrams
- Testing guide

### Operational Documentation

- Deployment guide
- Monitoring setup
- Backup procedures
- Rate limit management
- Error recovery procedures

---

## 🎯 Next Steps

### Immediate Actions

1. **Obtain API keys**:

   - Sign up for CoinGecko API
   - Sign up for Birdeye API
   - Sign up for Moralis API
   - Create Google service account

2. **Set up Google Sheets**:

   - Create spreadsheet
   - Share with service account
   - Get spreadsheet ID
   - Test write access

3. **Update .env file**:

   - Add all API keys
   - Add Google Sheets credentials path
   - Add configuration values

4. **Begin implementation**:
   - Start with Task 1 (Address Extractor)
   - Test thoroughly before moving to Task 2
   - Follow sequential task order

### Implementation Order

```
Task 1: Address Extractor (2-3 hours)
    ↓
Task 2: Price Engine (4-5 hours)
    ↓
Task 3: Performance Tracker (3-4 hours)
    ↓
Task 4: Data Output (3-4 hours)
    ↓
Task 5: Integration & Testing (2-3 hours)
    ↓
Total: 13-19 hours
```

---

## ✅ Readiness Checklist

### Prerequisites

- [x] Part 2 complete and verified
- [x] All Part 2 components working
- [x] ProcessedMessage structure defined
- [x] crypto_mentions field populated
- [x] Error handler available
- [x] Configuration system ready
- [x] Logging system in place

### Requirements

- [ ] CoinGecko API key obtained
- [ ] Birdeye API key obtained
- [ ] Moralis API key obtained
- [ ] Google service account created
- [ ] Google Sheets spreadsheet created
- [ ] .env file updated with keys
- [ ] credentials/ directory created
- [ ] data/ directory created
- [ ] output/ directory created

### Development Environment

- [x] Python 3.8+ installed
- [x] All Part 2 dependencies installed
- [ ] Additional dependencies installed:
  - [ ] `gspread` (Google Sheets)
  - [ ] `oauth2client` (Google auth)
  - [ ] `cachetools` (TTL cache)
  - [ ] `aiohttp` (async HTTP)
  - [ ] `web3` (Ethereum validation)
  - [ ] `base58` (Solana validation)

---

## 📞 Support & Resources

### API Documentation

- **CoinGecko**: https://www.coingecko.com/en/api/documentation
- **Birdeye**: https://docs.birdeye.so/
- **Moralis**: https://docs.moralis.io/
- **DexScreener**: https://docs.dexscreener.com/
- **Google Sheets**: https://developers.google.com/sheets/api

### Libraries

- **gspread**: https://docs.gspread.org/
- **web3.py**: https://web3py.readthedocs.io/
- **cachetools**: https://cachetools.readthedocs.io/

### Part 2 Reference

- `PART-2-VERIFICATION-COMPLETE.md` - Detailed verification
- `VERIFICATION-SUMMARY.md` - Quick reference
- `SYSTEM-STATUS.md` - Current system state
- `scripts/verification_report.md` - Test results

---

**Status**: Ready to Begin Part 3 Implementation  
**Estimated Duration**: 13-19 hours  
**Complexity**: Medium-High (API integration, multi-component)  
**Risk Level**: Medium (API dependencies, rate limits)  
**Success Probability**: High (solid foundation from Part 2)
