# Multi-Table Architecture - Quick Reference

## Table Definitions

### 1. MESSAGES Table (8 columns)

**Purpose:** Store all crypto-relevant messages  
**Pattern:** Append-only  
**Primary Key:** message_id

```
message_id, timestamp, channel_name, message_text,
hdrb_score, crypto_mentions, sentiment, confidence
```

**Example Row:**

```
12345, 2024-11-10T14:30:00, Eric's Calls, "BTC looking strong! Check 0x742d35...",
67.5, "BTC,0x742d35...", positive, 0.82
```

---

### 2. TOKEN_PRICES Table (9 columns)

**Purpose:** Store current price data for each token  
**Pattern:** Update or insert (by address)  
**Primary Key:** address

```
address, chain, symbol, price_usd, market_cap,
volume_24h, price_change_24h, liquidity_usd, pair_created_at
```

**Example Row:**

```
0x742d35..., ethereum, WETH, 1234.56, 150000000,
50000000, 2.5, 10000000, 1699564800
```

---

### 3. PERFORMANCE Table (10 columns)

**Purpose:** Track 7-day ATH performance for each token  
**Pattern:** Update or insert (by address)  
**Primary Key:** address

```
address, chain, first_message_id, start_price, start_time,
ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked
```

**Example Row:**

```
0x742d35..., ethereum, 12345, 1000.00, 2024-11-03T14:30:00,
2500.00, 2024-11-05T18:45:00, 2.5, 2.3, 7
```

---

### 4. HISTORICAL Table (8 columns)

**Purpose:** Store all-time ATH/ATL data from CoinGecko (optional)  
**Pattern:** Update or insert (by address)  
**Primary Key:** address

```
address, chain, all_time_ath, all_time_ath_date, distance_from_ath,
all_time_atl, all_time_atl_date, distance_from_atl
```

**Example Row:**

```
0x742d35..., ethereum, 4800.00, 2021-11-10, -74.3%,
0.50, 2015-10-20, +246700%
```

---

## Data Flow

```
1. Message arrives
   ↓
2. Process message (Part 2)
   ↓
3. Extract addresses
   ↓
4. Write to MESSAGES table (1 row)
   ↓
5. For each address:
   ├─> Fetch price
   │   └─> Write/Update TOKEN_PRICES (1 row)
   ├─> Update performance
   │   └─> Write/Update PERFORMANCE (1 row)
   └─> Fetch historical (optional)
       └─> Write/Update HISTORICAL (1 row)
```

---

## File Structure

### CSV Files (Daily Rotation)

```
output/
├── 2024-11-10/
│   ├── messages.csv          # All messages for the day
│   ├── token_prices.csv      # Latest prices (updated throughout day)
│   ├── performance.csv       # Performance tracking (updated throughout day)
│   └── historical.csv        # Historical data (updated as fetched)
└── 2024-11-11/
    ├── messages.csv
    ├── token_prices.csv
    ├── performance.csv
    └── historical.csv
```

### Google Sheets (Single Spreadsheet)

```
Spreadsheet: "Crypto Intelligence"
├── Messages          # All messages (append-only)
├── Token Prices      # Latest prices (update or insert)
├── Performance       # Performance tracking (update or insert)
└── Historical        # Historical data (update or insert)
```

---

## Common Operations

### Write New Message

```python
await data_output.write_message(processed_message)
```

- Appends to MESSAGES table
- CSV: Append to file
- Sheets: Append row

### Update Token Price

```python
await data_output.write_token_price(address, chain, price_data)
```

- Updates or inserts in TOKEN_PRICES table
- CSV: Find row by address, update or append
- Sheets: Find row by address, update or append

### Update Performance

```python
await data_output.write_performance(address, chain, perf_data, message_id)
```

- Updates or inserts in PERFORMANCE table
- CSV: Find row by address, update or append
- Sheets: Find row by address, update or append

### Write Historical Data

```python
await data_output.write_historical(address, chain, historical_data)
```

- Updates or inserts in HISTORICAL table
- CSV: Find row by address, update or append
- Sheets: Find row by address, update or append

---

## Query Examples

### Get all messages with token prices

```sql
SELECT m.*, tp.price_usd, tp.market_cap
FROM messages m
JOIN token_prices tp ON tp.address IN (m.crypto_mentions)
```

### Get performance for high-confidence messages

```sql
SELECT m.message_id, m.channel_name, p.address, p.ath_multiplier
FROM messages m
JOIN performance p ON p.address IN (m.crypto_mentions)
WHERE m.confidence > 0.8
ORDER BY p.ath_multiplier DESC
```

### Get tokens with 2x+ ATH

```sql
SELECT p.address, p.ath_multiplier, p.current_multiplier, tp.price_usd
FROM performance p
JOIN token_prices tp ON tp.address = p.address
WHERE p.ath_multiplier >= 2.0
```

### Get all data for a specific token

```sql
-- Messages mentioning this token
SELECT * FROM messages WHERE crypto_mentions LIKE '%0x742d35%'

-- Current price
SELECT * FROM token_prices WHERE address = '0x742d35...'

-- Performance tracking
SELECT * FROM performance WHERE address = '0x742d35...'

-- Historical context
SELECT * FROM historical WHERE address = '0x742d35...'
```

---

## Benefits Over Single-Table Design

### Storage Efficiency

- **Single-Table:** Message with 3 tokens = 3 rows (duplicate message data)
- **Multi-Table:** Message with 3 tokens = 1 message row + 3 price rows

### Update Efficiency

- **Single-Table:** Update price = Find all message rows with that address
- **Multi-Table:** Update price = Direct lookup by address key

### Query Flexibility

- **Single-Table:** Limited to message-centric queries
- **Multi-Table:** Join tables as needed for any analysis

### Scalability

- **Single-Table:** Table grows with messages × tokens
- **Multi-Table:** Each table grows independently

---

## Implementation Classes

### MultiTableDataOutput

Main coordinator for all 4 tables

```python
class MultiTableDataOutput:
    def __init__(self, config, logger)
    async def write_message(self, processed_message)
    async def write_token_price(self, address, chain, price_data)
    async def write_performance(self, address, chain, perf_data, message_id)
    async def write_historical(self, address, chain, historical_data)
```

### CSVTableWriter

Generic CSV writer with update/insert capability

```python
class CSVTableWriter:
    def __init__(self, table_name, columns, output_dir, logger)
    def append(self, row)
    def update_or_insert(self, key, row)
```

### GoogleSheetsMultiTable

Multi-sheet manager for Google Sheets

```python
class GoogleSheetsMultiTable:
    def __init__(self, credentials_path, spreadsheet_id, logger)
    async def append_to_sheet(self, sheet_name, row)
    async def update_or_insert_in_sheet(self, sheet_name, key, row)
```

---

## Configuration

### Environment Variables

```bash
# Google Sheets
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here

# CSV Output
CSV_OUTPUT_DIR=output
CSV_ROTATE_DAILY=true
```

### Directory Setup

```bash
mkdir -p output data/performance credentials
```

---

## Error Handling

### Graceful Degradation

1. CSV write fails → Log error, try Google Sheets
2. Google Sheets write fails → Continue with CSV only
3. Both fail → Log error, queue for retry

### Retry Strategy

- CSV: Retry immediately (local file)
- Google Sheets: Queue for batch retry (API limits)

---

## Performance Targets

| Operation           | Target  | Notes              |
| ------------------- | ------- | ------------------ |
| Write to MESSAGES   | < 10ms  | CSV append is O(1) |
| Update TOKEN_PRICES | < 50ms  | Read-modify-write  |
| Update PERFORMANCE  | < 50ms  | Read-modify-write  |
| Google Sheets write | < 100ms | Batch operations   |
| Total pipeline      | < 500ms | Async operations   |

---

## Monitoring

### Key Metrics

- Write success rate (target: 99%+)
- Average write time (target: < 500ms)
- Table sizes (monitor growth)
- Error frequency (target: < 0.1%)

### Health Checks

- CSV files exist and writable
- Google Sheets connection active
- No data loss or corruption
- Performance within targets
