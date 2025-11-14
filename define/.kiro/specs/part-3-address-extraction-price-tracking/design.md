# Design Document - Part 3: Address Extraction & Price Tracking

## Overview

Part 3 extends the crypto intelligence pipeline with four new components that transform crypto mentions into actionable price intelligence. The design emphasizes reliability through multi-API failover, efficiency through aggressive caching, and persistence through disk-based tracking. All components integrate seamlessly with the existing Part 2 pipeline while maintaining the async/await architecture.

## Architecture

### System Context

```
Part 2 Output (ProcessedMessage)
    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Part 3 Pipeline                               │
│                                                                  │
│  Address Extractor → Price Engine → Performance Tracker         │
│                           ↓                                      │
│                    Multi-Table Data Output                       │
│                    ├─ MESSAGES (CSV + Sheets)                   │
│                    ├─ TOKEN_PRICES (CSV + Sheets)               │
│                    ├─ PERFORMANCE (CSV + Sheets)                │
│                    └─ HISTORICAL (CSV + Sheets)                 │
└─────────────────────────────────────────────────────────────────┘
    ↓
EnrichedMessage (to console/future components)
```

### Component Interaction with Multi-Table Output

```
┌──────────────────┐
│ ProcessedMessage │
│ (from Part 2)    │
└────────┬─────────┘
         │
         ↓
┌────────────────────┐
│ Address Extractor  │
│ - Extract addresses│
│ - Validate format  │
│ - Identify chain   │
└────────┬───────────┘
         │ list[Address]
         ↓
┌────────────────────────────────────────────────────┐
│ For each address:                                  │
│                                                    │
│  ┌────────────────┐                               │
│  │  Price Engine  │                               │
│  │ - Check cache  │                               │
│  │ - Fetch price  │                               │
│  └────────┬───────┘                               │
│           │ PriceData                             │
│           ↓                                        │
│  ┌────────────────────┐                           │
│  │ Performance Tracker│                           │
│  │ - Start/update     │                           │
│  │ - Calculate ATH    │                           │
│  └────────┬───────────┘                           │
│           │ PerformanceData                       │
└───────────┼───────────────────────────────────────┘
            ↓
┌────────────────────────────────────────────────────┐
│  Multi-Table Data Output                           │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ 1. Write to MESSAGES table                   │ │
│  │    - message_id, timestamp, channel, text... │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ 2. For each address:                         │ │
│  │    Write/Update TOKEN_PRICES table           │ │
│  │    - address, chain, price, market_cap...    │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ 3. For each address:                         │ │
│  │    Write/Update PERFORMANCE table            │ │
│  │    - address, ath_multiplier, days_tracked...│ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ 4. For each address (optional):              │ │
│  │    Write/Update HISTORICAL table             │ │
│  │    - address, all_time_ath, all_time_atl...  │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

### Integration Flow

```python
async def process_message(processed_message: ProcessedMessage):
    """Complete Part 3 pipeline with multi-table output."""

    # 1. Extract addresses
    addresses = address_extractor.extract_addresses(
        processed_message.crypto_mentions
    )

    # 2. Write message to MESSAGES table
    await data_output.write_message(processed_message)

    # 3. Process each address
    for address in addresses:
        if not address.is_valid:
            continue

        # 3a. Fetch price
        price_data = await price_engine.get_price(
            address.address,
            address.chain
        )

        if price_data:
            # 3b. Write to TOKEN_PRICES table
            await data_output.write_token_price(
                address.address,
                address.chain,
                price_data
            )

            # 3c. Update performance tracking
            if address.address not in performance_tracker.tracking_data:
                performance_tracker.start_tracking(
                    address.address,
                    address.chain,
                    price_data.price_usd
                )
            else:
                await performance_tracker.update_price(
                    address.address,
                    price_data.price_usd
                )

            # 3d. Get performance data
            perf_data = performance_tracker.get_performance(address.address)

            if perf_data:
                # 3e. Write to PERFORMANCE table
                await data_output.write_performance(
                    address.address,
                    address.chain,
                    perf_data,
                    processed_message.message_id
                )

            # 3f. Optionally fetch and write historical data
            # (Implementation depends on CoinGecko historical API)

    logger.info(f"Processed message {processed_message.message_id} with {len(addresses)} addresses")
```

## Components and Interfaces

### 1. Address Extractor

**File:** `core/address_extractor.py`

**Purpose:** Extract and validate blockchain addresses from crypto mentions.

**Class Design:**

```python
class AddressExtractor:
    """Extract and validate blockchain addresses from crypto mentions."""

    def __init__(self, logger):
        """Initialize with logger."""
        self.logger = logger
        self.ethereum_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        self.solana_pattern = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

    def extract_addresses(self, crypto_mentions: list[str]) -> list[Address]:
        """
        Extract addresses from crypto mentions list.

        Args:
            crypto_mentions: List of strings (tickers and addresses)

        Returns:
            List of Address objects with validation status
        """
        addresses = []
        for mention in crypto_mentions:
            if self._looks_like_address(mention):
                chain = self.identify_chain(mention)
                is_valid = self.validate_address(mention, chain)
                addresses.append(Address(
                    address=mention,
                    chain=chain,
                    is_valid=is_valid
                ))
        return addresses

    def identify_chain(self, address: str) -> str:
        """Identify blockchain from address format."""
        if self.ethereum_pattern.match(address):
            return 'ethereum'
        elif self.solana_pattern.match(address):
            return 'solana'
        return 'unknown'

    def validate_address(self, address: str, chain: str) -> bool:
        """Validate address format for specific chain."""
        if chain == 'ethereum':
            return self.validate_ethereum_address(address)
        elif chain == 'solana':
            return self.validate_solana_address(address)
        return False

    def validate_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum address with checksum."""
        if not self.ethereum_pattern.match(address):
            return False
        # Basic format validation (checksum validation optional)
        return True

    def validate_solana_address(self, address: str) -> bool:
        """Validate Solana address format."""
        if not self.solana_pattern.match(address):
            return False
        # Base58 validation
        try:
            import base58
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False

    def _looks_like_address(self, text: str) -> bool:
        """Quick check if text looks like an address."""
        return (text.startswith('0x') and len(text) == 42) or \
               (len(text) >= 32 and len(text) <= 44 and text[0] in '123456789ABCDEFGHJKLMNPQRSTUVWXYZ')
```

**Dependencies:**

- `re` (standard library)
- `base58` (new dependency)
- Logger from Part 1

### 2. Price Engine

**File:** `core/price_engine.py`

**Purpose:** Fetch price data from multiple APIs with intelligent failover and caching.

**Class Design:**

```python
class PriceEngine:
    """Multi-API price fetching with failover and caching."""

    def __init__(self, config: PriceConfig, error_handler, logger):
        """Initialize with configuration and dependencies."""
        self.config = config
        self.error_handler = error_handler
        self.logger = logger

        # Initialize API clients
        self.coingecko = CoinGeckoAPI(config.coingecko_api_key)
        self.birdeye = BirdeyeAPI(config.birdeye_api_key)
        self.moralis = MoralisAPI(config.moralis_api_key)
        self.dexscreener = DexScreenerAPI()

        # Initialize cache (5-minute TTL)
        from cachetools import TTLCache
        self.cache = TTLCache(maxsize=1000, ttl=config.cache_ttl)

        # Initialize rate limiters
        self.rate_limiters = {
            'coingecko': RateLimiter(45, 60),  # 45 req/min
            'birdeye': RateLimiter(54, 60),    # 54 req/min
            'moralis': RateLimiter(22, 60)     # 22 req/min
        }

    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """
        Get price with failover.

        Args:
            address: Token contract address
            chain: Blockchain name (ethereum, solana, etc.)

        Returns:
            PriceData object or None if all APIs fail
        """
        cache_key = f"{chain}:{address}"

        # Check cache first
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]

        # Try APIs in sequence
        apis = self._get_api_sequence(chain)

        for api_name, api_func in apis:
            try:
                await self.rate_limiters[api_name].acquire()
                price_data = await api_func(address, chain)

                if price_data:
                    price_data.source = api_name
                    self.cache[cache_key] = price_data
                    self.logger.info(f"Price fetched from {api_name}: ${price_data.price_usd}")
                    return price_data

            except Exception as e:
                self.logger.warning(f"{api_name} failed for {address}: {e}")
                continue

        self.logger.error(f"All APIs failed for {address} on {chain}")
        return None

    def _get_api_sequence(self, chain: str) -> list:
        """Get API sequence based on chain."""
        if chain == 'solana':
            return [
                ('birdeye', self.birdeye.get_price),
                ('coingecko', self.coingecko.get_price),
                ('moralis', self.moralis.get_price),
                ('dexscreener', self.dexscreener.get_price)
            ]
        else:  # ethereum, bsc, etc.
            return [
                ('coingecko', self.coingecko.get_price),
                ('moralis', self.moralis.get_price),
                ('dexscreener', self.dexscreener.get_price)
            ]
```

**API Client Interfaces:**

Each API client follows this interface:

```python
class BaseAPIClient:
    """Base class for API clients."""

    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """Fetch price data from API."""
        raise NotImplementedError
```

**Rate Limiter:**

```python
class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire permission to make request (blocks if rate limit reached)."""
        async with self.lock:
            now = time.time()
            # Remove old requests outside time window
            self.requests = [req_time for req_time in self.requests
                           if now - req_time < self.time_window]

            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest = self.requests[0]
                wait_time = self.time_window - (now - oldest)
                await asyncio.sleep(wait_time)

            self.requests.append(time.time())
```

**Dependencies:**

- `aiohttp` (async HTTP client)
- `cachetools` (TTL cache)
- Error handler from Part 2
- Logger from Part 1

### 3. Performance Tracker

**File:** `core/performance_tracker.py`

**Purpose:** Track 7-day ATH performance for addresses.

**Class Design:**

```python
class PerformanceTracker:
    """Track 7-day ATH performance for addresses."""

    def __init__(self, config: PerformanceConfig, logger):
        """Initialize with configuration."""
        self.config = config
        self.logger = logger
        self.data_dir = Path(config.data_dir)
        self.data_file = self.data_dir / 'tracking.json'
        self.tracking_data = {}

        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.load_from_disk()

    def start_tracking(self, address: str, chain: str, initial_price: float):
        """
        Start tracking a new address.

        Args:
            address: Token contract address
            chain: Blockchain name
            initial_price: Starting price in USD
        """
        if address in self.tracking_data:
            self.logger.debug(f"Address {address} already tracked")
            return

        now = datetime.now()
        self.tracking_data[address] = {
            'address': address,
            'chain': chain,
            'start_price': initial_price,
            'start_time': now.isoformat(),
            'ath_price': initial_price,
            'ath_time': now.isoformat(),
            'current_price': initial_price,
            'last_update': now.isoformat()
        }

        self.logger.info(f"Started tracking {address} at ${initial_price}")
        self.save_to_disk()

    async def update_price(self, address: str, current_price: float):
        """
        Update current price and ATH if needed.

        Args:
            address: Token contract address
            current_price: Current price in USD
        """
        if address not in self.tracking_data:
            self.logger.warning(f"Address {address} not tracked, cannot update")
            return

        entry = self.tracking_data[address]
        entry['current_price'] = current_price
        entry['last_update'] = datetime.now().isoformat()

        # Update ATH if current price is higher
        if current_price > entry['ath_price']:
            entry['ath_price'] = current_price
            entry['ath_time'] = datetime.now().isoformat()
            self.logger.info(f"New ATH for {address}: ${current_price}")

        self.save_to_disk()

    def get_performance(self, address: str) -> Optional[PerformanceData]:
        """
        Get performance metrics for address.

        Args:
            address: Token contract address

        Returns:
            PerformanceData object or None if not tracked
        """
        if address not in self.tracking_data:
            return None

        entry = self.tracking_data[address]
        start_time = datetime.fromisoformat(entry['start_time'])
        days_tracked = (datetime.now() - start_time).days

        ath_multiplier = entry['ath_price'] / entry['start_price']
        current_multiplier = entry['current_price'] / entry['start_price']
        is_at_ath = abs(entry['current_price'] - entry['ath_price']) < 0.01

        ath_time = datetime.fromisoformat(entry['ath_time'])
        time_to_ath = ath_time - start_time if not is_at_ath else None

        return PerformanceData(
            address=address,
            chain=entry['chain'],
            start_price=entry['start_price'],
            current_price=entry['current_price'],
            ath_price=entry['ath_price'],
            ath_multiplier=ath_multiplier,
            current_multiplier=current_multiplier,
            days_tracked=days_tracked,
            time_to_ath=time_to_ath,
            is_at_ath=is_at_ath
        )

    def cleanup_old_entries(self):
        """Remove entries older than configured days."""
        now = datetime.now()
        to_remove = []

        for address, entry in self.tracking_data.items():
            start_time = datetime.fromisoformat(entry['start_time'])
            age_days = (now - start_time).days

            if age_days > self.config.tracking_days:
                to_remove.append(address)

        for address in to_remove:
            del self.tracking_data[address]
            self.logger.info(f"Removed old tracking entry: {address}")

        if to_remove:
            self.save_to_disk()

    def save_to_disk(self):
        """Persist tracking data to JSON file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.tracking_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save tracking data: {e}")

    def load_from_disk(self):
        """Load tracking data from JSON file."""
        if not self.data_file.exists():
            self.logger.info("No existing tracking data found")
            return

        try:
            with open(self.data_file, 'r') as f:
                self.tracking_data = json.load(f)
            self.logger.info(f"Loaded {len(self.tracking_data)} tracking entries")
        except Exception as e:
            self.logger.error(f"Failed to load tracking data: {e}")
            self.tracking_data = {}
```

**Dependencies:**

- `json` (standard library)
- `pathlib` (standard library)
- Logger from Part 1

### 4. Multi-Table Data Output

**Files:**

- `core/data_output.py` - Main coordinator
- `core/csv_table_writer.py` - Generic CSV table operations
- `core/sheets_multi_table.py` - Multi-sheet Google Sheets manager

**Purpose:** Write data to 4 separate tables (MESSAGES, TOKEN_PRICES, PERFORMANCE, HISTORICAL) in both CSV and Google Sheets formats.

**Architecture:**

```
MultiTableDataOutput
├── CSVTableWriter (messages)
├── CSVTableWriter (token_prices)
├── CSVTableWriter (performance)
├── CSVTableWriter (historical)
└── GoogleSheetsMultiTable
    ├── Sheet: Messages
    ├── Sheet: Token Prices
    ├── Sheet: Performance
    └── Sheet: Historical
```

**Table Definitions:**

```python
# Table column definitions
MESSAGES_COLUMNS = [
    'message_id', 'timestamp', 'channel_name', 'message_text',
    'hdrb_score', 'crypto_mentions', 'sentiment', 'confidence'
]

TOKEN_PRICES_COLUMNS = [
    'address', 'chain', 'symbol', 'price_usd', 'market_cap',
    'volume_24h', 'price_change_24h', 'liquidity_usd', 'pair_created_at'
]

PERFORMANCE_COLUMNS = [
    'address', 'chain', 'first_message_id', 'start_price', 'start_time',
    'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked'
]

HISTORICAL_COLUMNS = [
    'address', 'chain', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
    'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
]
```

**Main Coordinator Class:**

```python
class MultiTableDataOutput:
    """Write to 4 separate tables in CSV and Google Sheets."""

    def __init__(self, config: OutputConfig, logger):
        """Initialize with configuration."""
        self.config = config
        self.logger = logger

        # Initialize CSV writers for each table
        self.csv_writers = {
            'messages': CSVTableWriter('messages', MESSAGES_COLUMNS, config.csv_output_dir, logger),
            'token_prices': CSVTableWriter('token_prices', TOKEN_PRICES_COLUMNS, config.csv_output_dir, logger),
            'performance': CSVTableWriter('performance', PERFORMANCE_COLUMNS, config.csv_output_dir, logger),
            'historical': CSVTableWriter('historical', HISTORICAL_COLUMNS, config.csv_output_dir, logger)
        }

        # Initialize Google Sheets writer if enabled
        self.sheets_writer = None
        if config.google_sheets_enabled:
            try:
                self.sheets_writer = GoogleSheetsMultiTable(
                    config.google_sheets_credentials,
                    config.google_sheets_spreadsheet_id,
                    logger
                )
                self.logger.info("Google Sheets multi-table writer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Sheets: {e}")

    async def write_message(self, processed_message: ProcessedMessage):
        """
        Write message to MESSAGES table (append-only).

        Args:
            processed_message: Processed message from Part 2
        """
        # Only write crypto-relevant messages
        if not processed_message.is_crypto_relevant:
            return

        row = [
            processed_message.message_id,
            processed_message.timestamp.isoformat(),
            processed_message.channel_name,
            processed_message.message_text[:500],
            processed_message.hdrb_score,
            ','.join(processed_message.crypto_mentions),
            processed_message.sentiment,
            processed_message.confidence
        ]

        # Write to CSV
        try:
            self.csv_writers['messages'].append(row)
        except Exception as e:
            self.logger.error(f"CSV write failed for MESSAGES: {e}")

        # Write to Google Sheets
        if self.sheets_writer:
            try:
                await self.sheets_writer.append_to_sheet('Messages', row)
            except Exception as e:
                self.logger.error(f"Google Sheets write failed for MESSAGES: {e}")

    async def write_token_price(self, address: str, chain: str, price_data: PriceData):
        """
        Write/update token price in TOKEN_PRICES table (update or insert).

        Args:
            address: Token contract address
            chain: Blockchain type
            price_data: Price data from API
        """
        row = [
            address,
            chain,
            price_data.symbol or 'UNKNOWN',
            price_data.price_usd,
            price_data.market_cap,
            price_data.volume_24h,
            price_data.price_change_24h,
            price_data.liquidity_usd,
            price_data.pair_created_at
        ]

        # Update CSV (update existing row or append new)
        try:
            self.csv_writers['token_prices'].update_or_insert(address, row)
        except Exception as e:
            self.logger.error(f"CSV update failed for TOKEN_PRICES: {e}")

        # Update Google Sheets (update existing row or append new)
        if self.sheets_writer:
            try:
                await self.sheets_writer.update_or_insert_in_sheet('Token Prices', address, row)
            except Exception as e:
                self.logger.error(f"Google Sheets update failed for TOKEN_PRICES: {e}")

    async def write_performance(self, address: str, chain: str, performance_data: PerformanceData, first_message_id: str):
        """
        Write/update performance tracking in PERFORMANCE table (update or insert).

        Args:
            address: Token contract address
            chain: Blockchain type
            performance_data: Performance tracking data
            first_message_id: ID of first message mentioning this address
        """
        row = [
            address,
            chain,
            first_message_id,
            performance_data.start_price,
            performance_data.start_time.isoformat() if hasattr(performance_data.start_time, 'isoformat') else performance_data.start_time,
            performance_data.ath_price,
            performance_data.ath_time.isoformat() if hasattr(performance_data.ath_time, 'isoformat') else performance_data.ath_time,
            performance_data.ath_multiplier,
            performance_data.current_multiplier,
            performance_data.days_tracked
        ]

        # Update CSV (update existing row or append new)
        try:
            self.csv_writers['performance'].update_or_insert(address, row)
        except Exception as e:
            self.logger.error(f"CSV update failed for PERFORMANCE: {e}")

        # Update Google Sheets (update existing row or append new)
        if self.sheets_writer:
            try:
                await self.sheets_writer.update_or_insert_in_sheet('Performance', address, row)
            except Exception as e:
                self.logger.error(f"Google Sheets update failed for PERFORMANCE: {e}")

    async def write_historical(self, address: str, chain: str, historical_data: dict):
        """
        Write/update historical ATH/ATL data in HISTORICAL table (update or insert).

        Args:
            address: Token contract address
            chain: Blockchain type
            historical_data: Historical ATH/ATL data from CoinGecko
        """
        row = [
            address,
            chain,
            historical_data.get('all_time_ath'),
            historical_data.get('all_time_ath_date'),
            historical_data.get('distance_from_ath'),
            historical_data.get('all_time_atl'),
            historical_data.get('all_time_atl_date'),
            historical_data.get('distance_from_atl')
        ]

        # Update CSV (update existing row or append new)
        try:
            self.csv_writers['historical'].update_or_insert(address, row)
        except Exception as e:
            self.logger.error(f"CSV update failed for HISTORICAL: {e}")

        # Update Google Sheets (update existing row or append new)
        if self.sheets_writer:
            try:
                await self.sheets_writer.update_or_insert_in_sheet('Historical', address, row)
            except Exception as e:
                self.logger.error(f"Google Sheets update failed for HISTORICAL: {e}")
```

**CSV Table Writer:**

```python
class CSVTableWriter:
    """Generic CSV table writer with update/insert capability."""

    def __init__(self, table_name: str, columns: list, output_dir: str, logger):
        """Initialize CSV table writer."""
        self.table_name = table_name
        self.columns = columns
        self.output_dir = Path(output_dir)
        self.logger = logger
        self.current_file = None
        self.current_date = None
        self.row_index = {}  # Maps key to row number for updates

    def append(self, row: list):
        """Append row to table (for append-only tables like MESSAGES)."""
        self._ensure_file()

        with open(self.current_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def update_or_insert(self, key: str, row: list):
        """Update existing row or insert new row (for tables like TOKEN_PRICES, PERFORMANCE)."""
        self._ensure_file()

        # Read all rows
        rows = []
        if self.current_file.exists():
            with open(self.current_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

        # Find row with matching key (first column)
        updated = False
        for i, existing_row in enumerate(rows[1:], start=1):  # Skip header
            if existing_row and existing_row[0] == key:
                rows[i] = row
                updated = True
                break

        # If not found, append
        if not updated:
            rows.append(row)

        # Write all rows back
        with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def _ensure_file(self):
        """Ensure CSV file exists with header."""
        today = datetime.now().date()

        # Check if we need to rotate file
        if self.current_date != today:
            self._rotate_file(today)

    def _rotate_file(self, date):
        """Create new file for date."""
        date_dir = self.output_dir / date.isoformat()
        date_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.table_name}.csv"
        self.current_file = date_dir / filename
        self.current_date = date

        # Write header if new file
        if not self.current_file.exists():
            with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
            self.logger.info(f"Created new CSV file: {date.isoformat()}/{filename}")
```

**Google Sheets Multi-Table Writer:**

```python
class GoogleSheetsMultiTable:
    """Manage 4 separate sheets in a single Google Spreadsheet."""

    def __init__(self, credentials_path: str, spreadsheet_id: str, logger):
        """Initialize Google Sheets multi-table writer."""
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        self.logger = logger

        # Authenticate
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope)
        self.client = gspread.authorize(creds)

        # Open spreadsheet
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)

        # Get or create sheets
        self.sheets = {
            'Messages': self._get_or_create_sheet('Messages', MESSAGES_COLUMNS),
            'Token Prices': self._get_or_create_sheet('Token Prices', TOKEN_PRICES_COLUMNS),
            'Performance': self._get_or_create_sheet('Performance', PERFORMANCE_COLUMNS),
            'Historical': self._get_or_create_sheet('Historical', HISTORICAL_COLUMNS)
        }

        self.logger.info(f"Initialized 4 sheets in spreadsheet: {spreadsheet_id}")

    def _get_or_create_sheet(self, sheet_name: str, columns: list):
        """Get existing sheet or create new one with header."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(columns))
            worksheet.append_row(columns)
            self.logger.info(f"Created new sheet: {sheet_name}")

        # Ensure header exists
        if not worksheet.row_values(1):
            worksheet.append_row(columns)

        return worksheet

    async def append_to_sheet(self, sheet_name: str, row: list):
        """Append row to sheet (for append-only tables like Messages)."""
        worksheet = self.sheets[sheet_name]
        worksheet.append_row(row)
        self.logger.debug(f"Appended row to {sheet_name}")

    async def update_or_insert_in_sheet(self, sheet_name: str, key: str, row: list):
        """Update existing row or insert new row (for tables with keys)."""
        worksheet = self.sheets[sheet_name]

        # Find row with matching key (first column)
        try:
            cell = worksheet.find(key, in_column=1)
            # Update existing row
            worksheet.update(f'A{cell.row}', [row])
            self.logger.debug(f"Updated row in {sheet_name} for key: {key}")
        except gspread.exceptions.CellNotFound:
            # Append new row
            worksheet.append_row(row)
            self.logger.debug(f"Inserted new row in {sheet_name} for key: {key}")

    def apply_conditional_formatting(self):
        """Apply conditional formatting rules to sheets."""
        # High confidence messages: green background
        # High HDRB scores: bold
        # ATH > 2x: gold background
        # Implementation depends on gspread formatting API
        pass
```

**Dependencies:**

- `csv` (standard library)
- `gspread` (new dependency)
- `oauth2client` (new dependency)
- Logger from Part 1

## Data Models

### Address

```python
@dataclass
class Address:
    """Blockchain address with metadata."""
    address: str
    chain: str  # 'ethereum', 'solana', 'bsc', 'unknown'
    is_valid: bool
    ticker: Optional[str] = None
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
    pair_created_at: Optional[int] = None  # Unix timestamp from DexScreener
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
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
    ath_multiplier: float
    current_multiplier: float
    days_tracked: int
    time_to_ath: Optional[timedelta] = None  # Duration from start to ATH
    is_at_ath: bool = False  # True if current price equals ATH
```

### EnrichedMessage

```python
@dataclass
class EnrichedMessage(ProcessedMessage):
    """Message with price and performance data for multi-table output."""

    # Address extraction
    addresses: list[Address] = field(default_factory=list)

    # Price data (per address)
    price_data_map: dict[str, PriceData] = field(default_factory=dict)  # address -> PriceData

    # Performance tracking (per address)
    performance_data_map: dict[str, PerformanceData] = field(default_factory=dict)  # address -> PerformanceData

    # Historical data (per address, optional)
    historical_data_map: dict[str, dict] = field(default_factory=dict)  # address -> historical data

    # Output metadata
    output_timestamp: datetime = field(default_factory=datetime.now)
    output_error: Optional[str] = None
```

**Note:** The EnrichedMessage now uses maps to store data for multiple addresses, since a single message can mention multiple tokens. Each address gets its own entry in TOKEN_PRICES, PERFORMANCE, and HISTORICAL tables.

## Configuration

### PriceConfig

```python
@dataclass
class PriceConfig:
    """Price engine configuration."""
    coingecko_api_key: str
    birdeye_api_key: str
    moralis_api_key: str
    cache_ttl: int = 300  # 5 minutes
    rate_limit_buffer: float = 0.9  # Use 90% of rate limit
```

### PerformanceConfig

```python
@dataclass
class PerformanceConfig:
    """Performance tracking configuration."""
    update_interval: int = 7200  # 2 hours
    tracking_days: int = 7
    data_dir: str = "data/performance"
```

### OutputConfig

```python
@dataclass
class OutputConfig:
    """Data output configuration."""
    csv_output_dir: str = "output"
    csv_rotate_daily: bool = True
    google_sheets_enabled: bool = True
    google_sheets_credentials: str = ""
    google_sheets_spreadsheet_id: str = ""
```

### HistoricalScraperConfig

```python
@dataclass
class HistoricalScraperConfig:
    """Historical scraper configuration."""
    enabled: bool = True
    message_limit: int = 100  # Number of historical messages to fetch
    scraped_channels_file: str = "data/scraped_channels.json"
```

## Error Handling

### Strategy

1. **Address Extraction**: Mark invalid addresses but continue processing
2. **Price Fetching**: Try all APIs, return None if all fail
3. **Performance Tracking**: Log errors but don't crash
4. **Data Output**: CSV always succeeds, Google Sheets optional

### Error Propagation

```python
# Errors are captured in EnrichedMessage.output_error field
try:
    # Process message
    pass
except Exception as e:
    enriched_message.output_error = str(e)
    logger.error(f"Processing error: {e}")
    # Continue with partial data
```

## Testing Strategy

### Unit Tests

- **Address Extractor**: Test Ethereum/Solana validation
- **Price Engine**: Mock API responses, test failover
- **Performance Tracker**: Test ATH calculation, persistence
- **Data Output**: Test CSV/Sheets writing

### Integration Tests

- **Full Pipeline**: ProcessedMessage → EnrichedMessage
- **API Failover**: Simulate API failures
- **Rate Limiting**: Verify rate limits enforced

### Performance Tests

- **Throughput**: Process 100 messages, measure time
- **Cache Hit Rate**: Verify >70% cache hits
- **Memory**: Monitor for leaks over 1000 messages

## Multi-Table Architecture

### Overview

Part 3 uses a **multi-table architecture** instead of a single wide table. This provides:

1. **Normalized data structure** - No duplicate address/price data across messages
2. **Efficient updates** - Update token prices without rewriting message rows
3. **Flexible querying** - Join tables as needed for analysis
4. **Scalability** - Each table grows independently

### Table Relationships

```
MESSAGES (1) ──┐
               │
               ├──> crypto_mentions ──> TOKEN_PRICES (N)
               │                              │
               └──────────────────────────────┼──> PERFORMANCE (N)
                                              │
                                              └──> HISTORICAL (N)
```

- One message can mention multiple tokens
- Each token has one entry in TOKEN_PRICES (updated on each price fetch)
- Each token has one entry in PERFORMANCE (updated on each price update)
- Each token has one entry in HISTORICAL (optional, from CoinGecko)

### File Structure

**CSV Output:**

```
output/
├── 2024-11-10/
│   ├── messages.csv          (8 columns, append-only)
│   ├── token_prices.csv      (9 columns, update or insert)
│   ├── performance.csv       (10 columns, update or insert)
│   └── historical.csv        (8 columns, update or insert)
├── 2024-11-11/
│   ├── messages.csv
│   ├── token_prices.csv
│   ├── performance.csv
│   └── historical.csv
```

**Google Sheets Output:**

```
Spreadsheet: "Crypto Intelligence"
├── Sheet: "Messages"          (8 columns, append-only)
├── Sheet: "Token Prices"      (9 columns, update or insert)
├── Sheet: "Performance"       (10 columns, update or insert)
└── Sheet: "Historical"        (8 columns, update or insert)
```

### Data Flow

```
ProcessedMessage
    ↓
Extract Addresses
    ↓
For each address:
    ├─> Fetch Price ──────> Write to TOKEN_PRICES table
    ├─> Update Performance ─> Write to PERFORMANCE table
    └─> Fetch Historical ──> Write to HISTORICAL table (optional)
    ↓
Write message ──────────────> Write to MESSAGES table
```

### Example Queries

**Get all messages with token prices:**

```sql
SELECT m.*, tp.price_usd, tp.market_cap
FROM messages m
JOIN token_prices tp ON tp.address IN (m.crypto_mentions)
```

**Get performance for tokens mentioned in high-confidence messages:**

```sql
SELECT m.message_id, m.channel_name, p.address, p.ath_multiplier
FROM messages m
JOIN performance p ON p.address IN (m.crypto_mentions)
WHERE m.confidence > 0.8
ORDER BY p.ath_multiplier DESC
```

**Get tokens with 2x+ ATH that are still near ATH:**

```sql
SELECT p.address, p.ath_multiplier, p.current_multiplier, tp.price_usd
FROM performance p
JOIN token_prices tp ON tp.address = p.address
WHERE p.ath_multiplier >= 2.0
  AND p.current_multiplier >= (p.ath_multiplier * 0.9)
```

## Deployment Considerations

### Dependencies

New dependencies to add to `requirements.txt`:

```
aiohttp>=3.9.0
cachetools>=5.3.0
gspread>=5.12.0
oauth2client>=4.1.3
base58>=2.1.1
```

### Environment Variables

Add to `.env`:

```
COINGECKO_API_KEY=your_key
BIRDEYE_API_KEY=your_key
MORALIS_API_KEY=your_key
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
PERFORMANCE_UPDATE_INTERVAL=7200
PERFORMANCE_TRACKING_DAYS=7
CSV_OUTPUT_DIR=output
HISTORICAL_SCRAPER_ENABLED=true
HISTORICAL_SCRAPER_MESSAGE_LIMIT=100
```

### Directory Structure

Create directories:

```
crypto-intelligence/
├── data/
│   ├── performance/
│   │   └── tracking.json
│   └── scraped_channels.json
├── output/
│   └── YYYY-MM-DD/
│       ├── messages.csv
│       ├── token_prices.csv
│       ├── performance.csv
│       └── historical.csv
└── credentials/
    └── google_service_account.json
```

## Automatic Historical Scraping

### Overview

On system startup, automatically scrape historical messages for any channel that hasn't been scraped yet. This provides immediate data population and context before real-time monitoring begins.

### Implementation

```python
class HistoricalScraper:
    """Automatic historical scraping for new channels."""

    def __init__(self, config: HistoricalScraperConfig, telegram_monitor, pipeline_components):
        """Initialize with configuration and pipeline components."""
        self.config = config
        self.telegram_monitor = telegram_monitor
        self.pipeline_components = pipeline_components
        self.scraped_channels_file = Path(config.scraped_channels_file)
        self.scraped_channels = self._load_scraped_channels()

    def _load_scraped_channels(self) -> set:
        """Load list of previously scraped channels."""
        if not self.scraped_channels_file.exists():
            return set()

        try:
            with open(self.scraped_channels_file, 'r') as f:
                data = json.load(f)
                return set(data.get('scraped_channels', []))
        except Exception:
            return set()

    def _save_scraped_channels(self):
        """Save list of scraped channels."""
        self.scraped_channels_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.scraped_channels_file, 'w') as f:
            json.dump({'scraped_channels': list(self.scraped_channels)}, f, indent=2)

    async def scrape_if_needed(self, channel: ChannelConfig) -> bool:
        """
        Scrape channel if not previously scraped.

        Returns:
            True if scraping was performed or skipped, False if failed
        """
        if channel.id in self.scraped_channels:
            logger.info(f"Channel {channel.name} already scraped, skipping")
            return True

        logger.info(f"Channel {channel.name} not scraped, fetching {self.config.message_limit} historical messages")

        try:
            # Fetch historical messages
            messages = await self._fetch_messages(channel.id, self.config.message_limit)

            # Process through pipeline
            await self._process_messages(messages, channel.name)

            # Mark as scraped
            self.scraped_channels.add(channel.id)
            self._save_scraped_channels()

            logger.info(f"Historical scraping complete for {channel.name}")
            return True

        except Exception as e:
            logger.error(f"Historical scraping failed for {channel.name}: {e}")
            return False

    async def _fetch_messages(self, channel_id: str, limit: int) -> list:
        """Fetch historical messages from channel."""
        channel = await self.telegram_monitor.client.get_entity(channel_id)
        messages = []

        async for message in self.telegram_monitor.client.iter_messages(channel, limit=limit):
            if message.text:
                messages.append(message)

        return messages

    async def _process_messages(self, messages: list, channel_name: str):
        """Process messages through complete pipeline."""
        for i, message in enumerate(messages, 1):
            if i % 10 == 0:
                logger.info(f"Processing historical message {i}/{len(messages)}")

            # Process through complete Part 1 + Part 2 + Part 3 pipeline
            # (same as real-time message handling)
            await self.pipeline_components.process_message(message, channel_name)
```

### Integration in main.py

```python
async def start(self):
    """Start the system."""
    # ... existing initialization ...

    # Initialize historical scraper
    if self.config.historical_scraper.enabled:
        self.historical_scraper = HistoricalScraper(
            self.config.historical_scraper,
            self.telegram_monitor,
            self.pipeline_components
        )

        # Scrape new channels before starting real-time monitoring
        for channel in self.config.channels:
            if channel.enabled:
                await self.historical_scraper.scrape_if_needed(channel)

    # Start real-time monitoring
    await self.telegram_monitor.start_monitoring(self.handle_message)
```

## Performance Targets

- Address extraction: <10ms per message
- Price fetch (cached): <1ms
- Price fetch (API): <300ms per address
- Performance update: <50ms per address
- CSV write: <10ms
- Google Sheets write: <100ms
- **Total pipeline**: <500ms per message
