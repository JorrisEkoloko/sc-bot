# Task 3 & 4 Updates: Multi-Table Architecture

## Summary of Changes

**Previous Design:** Single table with 23-26 columns  
**New Design:** 4 separate tables with 35 total columns  
**Impact:** Significant architectural changes to both tasks

---

## 📊 **TASK 3: PERFORMANCE TRACKER - CHANGES**

### **What Changed**

#### **1. Output Responsibility**

**OLD:** PerformanceTracker only saves to internal JSON  
**NEW:** PerformanceTracker writes to PERFORMANCE table (CSV + Sheets)

#### **2. Data Structure**

**OLD:** Single JSON file with all tracking data  
**NEW:** Internal JSON + PERFORMANCE table (10 columns)

#### **3. Dependencies**

**OLD:** No external dependencies  
**NEW:** Requires CSVTableWriter and GoogleSheetsMultiTable

### **New Implementation**

```python
class PerformanceTracker:
    """Track performance with multi-table output."""

    def __init__(self, config, csv_writer, sheets_writer):
        # Internal tracking (fast lookups)
        self.tracking_data = {}
        self.data_file = Path(config.data_dir) / "tracking.json"

        # Table writers
        self.csv_writer = csv_writer  # CSVTableWriter for PERFORMANCE
        self.sheets_writer = sheets_writer  # GoogleSheetsMultiTable

        self.load_from_disk()

    def start_tracking(self, address, chain, initial_price, message_id):
        """Start tracking and write to PERFORMANCE table."""
        # 1. Create internal tracking entry
        self.tracking_data[address] = {
            'address': address,
            'chain': chain,
            'first_message_id': message_id,
            'start_price': initial_price,
            'start_time': datetime.now().isoformat(),
            'ath_price': initial_price,
            'ath_time': datetime.now().isoformat()
        }

        # 2. Save to internal JSON
        self.save_to_disk()

        # 3. Write to PERFORMANCE table
        row = self.to_table_row(address)
        self.csv_writer.append(row)
        self.sheets_writer.write_to_sheet('performance', row)

    async def update_price(self, address, current_price):
        """Update price and sync to PERFORMANCE table."""
        entry = self.tracking_data[address]
        entry['current_price'] = current_price

        # Check for new ATH
        if current_price > entry['ath_price']:
            entry['ath_price'] = current_price
            entry['ath_time'] = datetime.now().isoformat()

        # Save to internal JSON
        self.save_to_disk()

        # Update PERFORMANCE table
        row = self.to_table_row(address)
        self.csv_writer.update(address, row)
        self.sheets_writer.update_in_sheet('performance', address, row)

    def to_table_row(self, address) -> list:
        """Convert to PERFORMANCE table format (10 columns)."""
        entry = self.tracking_data[address]
        start_time = datetime.fromisoformat(entry['start_time'])

        return [
            address,
            entry['chain'],
            entry['first_message_id'],
            entry['start_price'],
            entry['start_time'],
            entry['ath_price'],
            entry['ath_time'],
            entry['ath_price'] / entry['start_price'],  # ath_multiplier
            entry.get('current_price', entry['start_price']) / entry['start_price'],  # current_multiplier
            (datetime.now() - start_time).days  # days_tracked
        ]
```

### **New Files for Task 3**

1. **`core/performance_tracker.py`** (~300 lines)

   - Enhanced with table output
   - Coordinates with CSVTableWriter
   - Syncs to Google Sheets

2. **`core/csv_table_writer.py`** (~150 lines)

   - Generic CSV table operations
   - Handles append and update
   - Used by PerformanceTracker

3. **`config/performance_config.py`** (~20 lines)
   - Configuration dataclass

---

## 📊 **TASK 4: DATA OUTPUT - CHANGES**

### **What Changed**

#### **1. Architecture**

**OLD:** Single CSV file + Single Google Sheet  
**NEW:** 4 CSV files + 4 Google Sheets

#### **2. Write Operations**

**OLD:** Append only (one enriched message per row)  
**NEW:** Append (MESSAGES) + Update/Insert (TOKEN_PRICES, PERFORMANCE, HISTORICAL)

#### **3. Class Structure**

**OLD:** DataOutput → CSVOutput + GoogleSheetsOutput  
**NEW:** MultiTableDataOutput → 4x CSVTableWriter + GoogleSheetsMultiTable

### **New Implementation**

```python
class MultiTableDataOutput:
    """Manage output to 4 separate tables."""

    def __init__(self, config):
        self.config = config

        # Initialize CSV writers for each table
        self.csv_writers = {
            'messages': CSVTableWriter('messages', MESSAGES_COLUMNS),
            'token_prices': CSVTableWriter('token_prices', TOKEN_PRICES_COLUMNS),
            'performance': CSVTableWriter('performance', PERFORMANCE_COLUMNS),
            'historical': CSVTableWriter('historical', HISTORICAL_COLUMNS)
        }

        # Initialize Google Sheets
        if config.google_sheets_enabled:
            self.sheets = GoogleSheetsMultiTable(
                config.spreadsheet_id,
                config.credentials_path
            )

    async def write_message(self, processed_message):
        """Write to MESSAGES table (8 columns)."""
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

        self.csv_writers['messages'].append(row)
        if self.sheets:
            self.sheets.write_to_sheet('messages', row)

    async def write_token_price(self, address, price_data):
        """Write/update TOKEN_PRICES table (9 columns)."""
        row = [
            address,
            price_data.chain,
            price_data.symbol,
            price_data.price_usd,
            price_data.market_cap,
            price_data.volume_24h,
            price_data.price_change_24h,
            price_data.liquidity_usd,
            price_data.pair_created_at
        ]

        self.csv_writers['token_prices'].update(address, row)
        if self.sheets:
            self.sheets.update_in_sheet('token_prices', address, row)

    async def write_performance(self, address, perf_data):
        """Write/update PERFORMANCE table (10 columns)."""
        # Called by PerformanceTracker
        pass

    async def write_historical(self, address, hist_data):
        """Write/update HISTORICAL table (8 columns)."""
        row = [
            address,
            hist_data.chain,
            hist_data.all_time_ath,
            hist_data.all_time_ath_date,
            hist_data.distance_from_ath,
            hist_data.all_time_atl,
            hist_data.all_time_atl_date,
            hist_data.distance_from_atl
        ]

        self.csv_writers['historical'].update(address, row)
        if self.sheets:
            self.sheets.update_in_sheet('historical', address, row)
```

### **New Files for Task 4**

1. **`core/data_output.py`** (~400 lines)

   - MultiTableDataOutput class
   - Coordinates 4 table writers
   - Handles all output operations

2. **`core/csv_table_writer.py`** (~150 lines)

   - Generic CSV table writer
   - Append and update operations
   - Daily rotation logic

3. **`core/sheets_multi_table.py`** (~250 lines)

   - GoogleSheetsMultiTable class
   - Manages 4 sheets in 1 spreadsheet
   - Update and append operations
   - Conditional formatting

4. **`config/output_config.py`** (~30 lines)
   - OutputConfig dataclass

---

## 🔄 **INTEGRATION FLOW**

### **When Processing a Message**

```python
async def handle_message(telegram_message):
    # 1. Process message (Part 2)
    processed = await message_processor.process(telegram_message)

    # 2. Skip if not crypto-relevant
    if not processed.is_crypto_relevant:
        return

    # 3. Write to MESSAGES table
    await data_output.write_message(processed)

    # 4. Extract addresses (Part 3)
    addresses = address_extractor.extract(processed.crypto_mentions)

    # 5. For each address:
    for address in addresses:
        # 5a. Fetch price
        price_data = await price_engine.get_price(address.address, address.chain)

        # 5b. Write to TOKEN_PRICES table
        await data_output.write_token_price(address.address, price_data)

        # 5c. Update performance (writes to PERFORMANCE table internally)
        await performance_tracker.update_price(
            address.address,
            price_data.price_usd,
            message_id=processed.message_id  # For first mention
        )

        # 5d. Optionally fetch historical data
        if should_fetch_historical(address):
            hist_data = await fetch_coingecko_ath(address.address, address.chain)
            if hist_data:
                await data_output.write_historical(address.address, hist_data)
```

---

## ✅ **VALIDATION CHECKLIST**

### **Task 3: Performance Tracker**

- [ ] PerformanceTracker creates internal JSON
- [ ] PerformanceTracker writes to PERFORMANCE CSV
- [ ] PerformanceTracker writes to PERFORMANCE Sheet
- [ ] New tracking creates row in PERFORMANCE table
- [ ] Price updates modify existing row (not append)
- [ ] ATH updates reflected in PERFORMANCE table
- [ ] Cleanup removes from JSON and tables
- [ ] Data persists across restarts

### **Task 4: Multi-Table Data Output**

- [ ] 4 CSV files created (messages, token_prices, performance, historical)
- [ ] 4 Google Sheets created in single spreadsheet
- [ ] MESSAGES: append-only operation
- [ ] TOKEN_PRICES: update or insert operation
- [ ] PERFORMANCE: update or insert operation
- [ ] HISTORICAL: update or insert operation
- [ ] Daily rotation creates new directory
- [ ] Conditional formatting applied to appropriate sheets
- [ ] Tables can be linked via VLOOKUP formulas
- [ ] Graceful error handling (CSV continues if Sheets fails)

---

## 🎯 **NEXT STEPS**

1. ✅ Documentation updated for Task 3
2. ✅ Documentation updated for Task 4
3. ⏳ Update design.md with multi-table architecture
4. ⏳ Update requirements.md if needed
5. ⏳ Implement Task 3 with multi-table support
6. ⏳ Implement Task 4 with multi-table architecture

**All task documentation is now aligned with the multi-table design!** 🚀
