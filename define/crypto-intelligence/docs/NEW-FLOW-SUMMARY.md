# New Flow: Closest Entry Price + Forward OHLC

## ✅ Implementation Complete!

### What Changed

**OLD FLOW** ❌:

```
1. Use current price as entry → WRONG for historical messages
2. Fetch each checkpoint price individually → 7 API calls
3. Guess ATH from checkpoints → Inaccurate
```

**NEW FLOW** ✅:

```
1. Fetch closest price to message time → Accurate entry
2. Fetch 30 days of OHLC candles → 1 API call
3. Calculate real ATH from candles → Accurate
4. Calculate all checkpoint ROIs from candles → No extra calls
```

---

## New Flow Diagram

```
📅 Historical Message (30 days old)
   "Buy BTC!" sent Jan 15, 2024 at 3:00 PM
         ↓
🔍 STEP 1: Get Closest Entry Price
   Try: Exact time (Jan 15, 3:00 PM)
   ↓ (if not found)
   Try: ±1 hour (Jan 15, 2:00-4:00 PM)
   ↓ (if not found)
   Try: ±6 hours (Jan 15, 9:00 AM - 9:00 PM)
   ↓ (if not found)
   Try: ±24 hours (Jan 14-16)
   ↓
   Result: $42,000 (source: "1h_before")
         ↓
📊 STEP 2: Get 30 Days Forward OHLC
   From: Jan 15, 2024
   To: Feb 14, 2024
   ↓
   CryptoCompare API: /v2/histoday?fsym=BTC&limit=30
   ↓
   Result: 30 daily candles with OHLC data
         ↓
🏆 STEP 3: Calculate ATH from Candles
   Scan all 30 candles:
   - Day 1: High = $43,000
   - Day 5: High = $48,000 ← ATH!
   - Day 10: High = $45,000
   - Day 30: High = $44,000
   ↓
   Result: ATH = $48,000 on Day 5 (1.14x)
         ↓
⏱️ STEP 4: Calculate Checkpoint ROIs
   For each checkpoint (1h, 4h, 24h, 3d, 7d, 30d):
   - Find closest candle to checkpoint time
   - Use candle's close price
   - Calculate ROI = close_price / entry_price
   ↓
   Results:
   - 1h: $42,100 (1.002x, +0.2%)
   - 4h: $42,500 (1.012x, +1.2%)
   - 24h: $43,000 (1.024x, +2.4%)
   - 3d: $45,000 (1.071x, +7.1%)
   - 7d: $47,000 (1.119x, +11.9%)
   - 30d: $44,000 (1.048x, +4.8%)
         ↓
💾 STEP 5: Save to SignalOutcome
   ✓ entry_price: $42,000
   ✓ ath_price: $48,000
   ✓ ath_multiplier: 1.14x
   ✓ days_to_ath: 5
   ✓ All checkpoint ROIs filled
   ✓ Data completeness: 100%
```

---

## API Calls Comparison

### OLD WAY ❌

```
1. Get current price → 1 call
2. Get checkpoint 1h → 1 call
3. Get checkpoint 4h → 1 call
4. Get checkpoint 24h → 1 call
5. Get checkpoint 3d → 1 call
6. Get checkpoint 7d → 1 call
7. Get checkpoint 30d → 1 call

Total: 7 API calls per signal
```

### NEW WAY ✅

```
1. Get closest entry price → 1 call (with smart fallback)
2. Get 30 days OHLC → 1 call (includes all checkpoints)

Total: 2 API calls per signal
```

**Efficiency gain**: 71% fewer API calls! 🎉

---

## Code Changes

### File 1: `historical_price_retriever.py`

**Added 3 new methods:**

#### 1. `fetch_closest_entry_price()`

```python
async def fetch_closest_entry_price(symbol, message_timestamp):
    """
    Fetch closest price to message time with smart fallback.

    Tries: exact → ±1h → ±6h → ±24h

    Returns: (price, source)
    """
```

#### 2. `fetch_forward_ohlc_with_ath()`

```python
async def fetch_forward_ohlc_with_ath(symbol, entry_timestamp, window_days=30):
    """
    Fetch forward OHLC and calculate ATH from candles.

    Returns: {
        'ath_price': float,
        'ath_timestamp': datetime,
        'days_to_ath': float,
        'candles': List[OHLCCandle],
        'data_completeness': float
    }
    """
```

#### 3. `calculate_checkpoint_rois_from_ohlc()`

```python
async def calculate_checkpoint_rois_from_ohlc(entry_price, entry_timestamp, checkpoints, candles):
    """
    Calculate ROI at each checkpoint using OHLC candles.

    Returns: Dict[checkpoint_name, roi_multiplier]
    """
```

### File 2: `historical_scraper.py`

**Updated `update_signal_checkpoints()` method:**

```python
# OLD WAY ❌
checkpoint_prices = await fetch_checkpoint_prices(symbol, checkpoints)
for checkpoint in checkpoints:
    price = checkpoint_prices[checkpoint]
    roi = price / entry_price

# NEW WAY ✅
# Step 1: Get closest entry price
entry_price, source = await retriever.fetch_closest_entry_price(symbol, message_date)

# Step 2: Get forward OHLC with ATH
ohlc_result = await retriever.fetch_forward_ohlc_with_ath(symbol, message_date, 30)

# Step 3: Calculate all checkpoint ROIs at once
checkpoint_rois = await retriever.calculate_checkpoint_rois_from_ohlc(
    entry_price, message_date, checkpoints, ohlc_result['candles']
)
```

---

## Benefits

### 1. Accuracy ✅

- **Real entry price**: Closest to message time (not current price)
- **Real ATH**: From actual OHLC candles (not guessed)
- **Real checkpoint ROIs**: From actual candle prices

### 2. Efficiency ✅

- **71% fewer API calls**: 2 calls instead of 7
- **Faster processing**: Batch data in OHLC
- **Better caching**: Historical data never changes

### 3. Reliability ✅

- **Smart fallback**: Tries multiple time windows
- **Data completeness tracking**: Know how much data you have
- **Proven APIs**: CryptoCompare + Twelve Data

---

## Testing

### Run Tests

```bash
# Set API keys
export CRYPTOCOMPARE_API_KEY=your_key
export TWELVEDATA_API_KEY=your_key

# Run test script
python tests/test_closest_entry_price.py
```

### Expected Output

```
=== Testing Closest Entry Price ===
Test date: 2024-12-13 15:30:00
Fetching closest BTC price...

✓ SUCCESS!
  Price: $42,156.78
  Source: exact_time

=== Testing Forward OHLC with ATH ===
Entry date: 2024-11-13
Fetching 30 days of forward OHLC for BTC...

✓ SUCCESS!
  Entry price: $42,000.00
  ATH price: $48,250.00
  ATH multiplier: 1.149x
  Days to ATH: 5.0
  Candles: 30
  Data completeness: 100.0%
  Source: cryptocompare

=== Testing Checkpoint ROIs from OHLC ===
Entry date: 2024-11-13
Fetching OHLC and calculating checkpoint ROIs...

✓ SUCCESS!
  Entry price: $42,000.00

  Checkpoint ROIs:
      1h: $42,100.00 (1.002x,   +0.2%)
      4h: $42,500.00 (1.012x,   +1.2%)
     24h: $43,000.00 (1.024x,   +2.4%)
      3d: $45,000.00 (1.071x,   +7.1%)
      7d: $47,000.00 (1.119x,  +11.9%)
     30d: $44,000.00 (1.048x,   +4.8%)
```

---

## Usage in Production

### Backfill Historical Signals

```bash
# Run historical scraper with backfill
python scripts/historical_scraper.py --backfill

# Or scrape specific channel
python scripts/historical_scraper.py --channel @your_channel --limit 100
```

### What Happens

1. Loads all existing signals from `outcome_tracker`
2. For each signal:
   - Fetches closest entry price to message time
   - Fetches 30 days of forward OHLC
   - Calculates real ATH from candles
   - Calculates all checkpoint ROIs
   - Updates SignalOutcome with accurate data
3. Recalculates channel reputations with accurate ROIs
4. Saves updated data

---

## Configuration

### Environment Variables

```bash
# Required
CRYPTOCOMPARE_API_KEY=your_key_here
TWELVEDATA_API_KEY=your_key_here

# Optional (defaults shown)
ENTRY_PRICE_LOOKBACK_HOURS=24
FORWARD_OHLC_WINDOW_DAYS=30
API_TIMEOUT_SECONDS=10
MAX_RETRIES_PER_API=3
```

---

## Summary

### What We Built

✅ Smart entry price fetching (closest to message time)
✅ Forward OHLC with ATH calculation
✅ Checkpoint ROI calculation from OHLC
✅ 71% reduction in API calls
✅ Accurate historical ROI calculation

### Files Modified

- `services/pricing/historical_price_retriever.py` (+150 lines)
- `scripts/historical_scraper.py` (~50 lines modified)

### Total New Code

~200 lines

### Result

**Accurate channel reputation based on real historical performance!** 🎯
