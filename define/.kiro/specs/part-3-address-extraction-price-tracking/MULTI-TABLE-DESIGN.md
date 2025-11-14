# Multi-Table Design Documentation

## Overview

Part 3 implements a **multi-table architecture** with 4 separate tables for clean data separation and flexible analysis.

---

## 📊 **4-TABLE ARCHITECTURE**

### **TABLE 1: MESSAGES** (Crypto Signals)

**Purpose:** Track crypto signals from Telegram channels  
**Update:** Append-only (new messages)  
**Columns:** 8

```csv
message_id,timestamp,channel_name,message_text,hdrb_score,crypto_mentions,sentiment,confidence
3641,2024-11-08T10:30:00,Eric Cryptomans Journal,"NEAR looking strong!",3.10,"NEAR,0x123...",neutral,0.41
```

**Business Value:**

- Signal history and analysis
- Channel performance tracking
- Sentiment analysis

---

### **TABLE 2: TOKEN_PRICES** (Market Data)

**Purpose:** Current price and market data for tokens  
**Update:** Update or insert (latest prices)  
**Columns:** 9

```csv
address,chain,symbol,price_usd,market_cap,volume_24h,price_change_24h,liquidity_usd,pair_created_at
So11111111111111111111111111111111111111112,solana,SOL,166.41,98966940732,232826573.39,1.7,46124277.92,1688106058000
```

**Business Value:**

- Real-time price monitoring
- Market cap analysis
- Liquidity assessment
- Token age context

---

### **TABLE 3: PERFORMANCE** (Since Mention)

**Purpose:** Track ROI from when channel mentioned token  
**Update:** Update or insert (tracking data)  
**Columns:** 10

```csv
address,chain,first_message_id,start_price,start_time,ath_since_mention,ath_time,ath_multiplier,current_multiplier,days_tracked
So11111111111111111111111111111111111111112,solana,3641,150.00,2024-11-01T10:00:00,180.00,2024-11-05T14:30:00,1.20,1.11,7
```

**Business Value:**

- ROI from channel calls
- Performance since mention
- Channel accuracy tracking
- Speed to peak analysis

---

### **TABLE 4: HISTORICAL** (All-Time Context)

**Purpose:** Historical ATH/ATL context from CoinGecko  
**Update:** Daily or on-demand  
**Columns:** 8

```csv
address,chain,all_time_ath,all_time_ath_date,distance_from_ath,all_time_atl,all_time_atl_date,distance_from_atl
So11111111111111111111111111111111111111112,solana,260.06,2021-11-06T21:54:35,-36.0,0.50,2020-05-11T19:35:23,33182.0
```

**Business Value:**

- Historical context
- Upside potential analysis
- Risk assessment
- Recovery strength indicator

---

## 📁 **FILE STRUCTURE**

### **CSV Files (Daily Rotation)**

```
crypto-intelligence/
├── output/
│   ├── 2024-11-08/
│   │   ├── messages.csv          (8 columns)
│   │   ├── token_prices.csv      (9 columns)
│   │   ├── performance.csv       (10 columns)
│   │   └── historical.csv        (8 columns)
│   └── 2024-11-09/
│       ├── messages.csv
│       ├── token_prices.csv
│       ├── performance.csv
│       └── historical.csv
```

### **Google Sheets (Single Spreadsheet)**

```
Crypto Intelligence Dashboard
├── Sheet 1: Messages          (8 columns)
├── Sheet 2: Token Prices      (9 columns)
├── Sheet 3: Performance       (10 columns)
└── Sheet 4: Historical        (8 columns)
```

---

## 🔗 **TABLE RELATIONSHIPS**

### **How Tables Connect**

```
MESSAGES (message_id)
    ↓
PERFORMANCE (first_message_id) → Links to first message that mentioned token
    ↓
TOKEN_PRICES (address) → Current market data
    ↓
HISTORICAL (address) → All-time context (optional)
```

### **Google Sheets Formulas**

**Get current price for token in Performance sheet:**

```
=VLOOKUP(A2,'Token Prices'!A:D,4,FALSE)
```

**Get message text for performance entry:**

```
=VLOOKUP(C2,Messages!A:D,4,FALSE)
```

**Complete view with all data:**

```
=QUERY({Performance!A:J,
        ARRAYFORMULA(VLOOKUP(Performance!A:A,'Token Prices'!A:D,4,FALSE)),
        ARRAYFORMULA(VLOOKUP(Performance!A:A,Historical!A:C,3,FALSE))},
       "SELECT * WHERE Col1 IS NOT NULL")
```

---

## 🔄 **UPDATE LOGIC**

### **MESSAGES Table**

```python
# Append only - new messages
if processed_message.is_crypto_relevant:
    data_output.write_message(processed_message)
```

### **TOKEN_PRICES Table**

```python
# Update or insert - latest prices
price_data = await price_engine.get_price(address, chain)
data_output.write_token_price(address, price_data)
```

### **PERFORMANCE Table**

```python
# Update or insert - tracking data
await performance_tracker.update_price(address, current_price)
# PerformanceTracker automatically writes to table
```

### **HISTORICAL Table**

```python
# Update or insert - daily refresh
historical_data = await fetch_coingecko_ath(address, chain)
if historical_data:
    data_output.write_historical(address, historical_data)
```

---

## 🎯 **IMPLEMENTATION COMPONENTS**

### **Task 3: Performance Tracker**

**Files:**

- `core/performance_tracker.py` - Main tracking logic + table output
- `core/csv_table_writer.py` - Generic CSV table operations
- `config/performance_config.py` - Configuration

**Key Methods:**

```python
class PerformanceTracker:
    def start_tracking(address, chain, price, message_id)
        # Create tracking entry
        # Write to PERFORMANCE table

    def update_price(address, current_price)
        # Update ATH if needed
        # Save to internal JSON
        # Update PERFORMANCE table

    def to_table_row(address) -> list
        # Convert to 10-column format
```

---

### **Task 4: Multi-Table Data Output**

**Files:**

- `core/data_output.py` - Multi-table coordinator
- `core/csv_table_writer.py` - CSV table writer
- `core/sheets_multi_table.py` - Google Sheets manager
- `config/output_config.py` - Configuration

**Key Classes:**

```python
class MultiTableDataOutput:
    def write_message(processed_message)
        # Write to MESSAGES table

    def write_token_price(address, price_data)
        # Update TOKEN_PRICES table

    def write_performance(address, perf_data)
        # Update PERFORMANCE table

    def write_historical(address, hist_data)
        # Update HISTORICAL table

class CSVTableWriter:
    def append(row_data)
        # Append row (for MESSAGES)

    def update(key, row_data)
        # Update or insert row (for other tables)

class GoogleSheetsMultiTable:
    def write_to_sheet(sheet_name, row_data)
        # Append to specific sheet

    def update_in_sheet(sheet_name, key, row_data)
        # Update or insert in specific sheet
```

---

## ✅ **BENEFITS**

### **1. Clean Separation**

- Messages: Immutable signal history
- Prices: Frequently updated market data
- Performance: Our tracking logic
- Historical: Optional context

### **2. Efficient Updates**

- Only update what changes
- Prices update every 2-5 min
- Performance updates with prices
- Historical updates daily
- Messages never update

### **3. Flexible Analysis**

- Analyze messages independently
- Track token performance across channels
- Compare current vs historical
- Join tables as needed for different views

### **4. Scalability**

- Easy to add new tables
- No column limit issues
- Can archive old data per table
- Optimized storage

### **5. Professional Architecture**

- Industry-standard normalization
- Reduces data duplication
- Easier to maintain
- Better for future enhancements

---

## 📊 **DATA FLOW**

```
Telegram Message
    ↓
Message Processor (Part 2)
    ↓
[Is Crypto Relevant?] → NO → Skip
    ↓ YES
Write to MESSAGES table
    ↓
Address Extractor (Part 3)
    ↓
For each address:
    ↓
Price Engine → Write to TOKEN_PRICES table
    ↓
Performance Tracker → Write to PERFORMANCE table
    ↓
(Optional) Historical Fetcher → Write to HISTORICAL table
```

---

## 🎯 **SUMMARY**

**Total Columns:** 35 across 4 tables  
**Storage:** CSV files + Google Sheets  
**Update Strategy:** Append (MESSAGES) + Update/Insert (others)  
**Benefits:** Clean, scalable, professional architecture

**This multi-table design provides a solid foundation for comprehensive crypto intelligence analysis!** 🚀
