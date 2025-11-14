# 24-Hour Lookback + Forward OHLC Implementation Summary

## 🎯 Goal

Implement accurate historical ROI calculation using:

1. **24-hour lookback** for entry price (instead of current price)
2. **Forward OHLC data** (30 days) to calculate actual ATH and checkpoint ROIs

---

## ✅ Current State: 90% Ready

### What Already Exists

- ✅ **HistoricalPriceRetriever** with CryptoCompare + Twelve Data support
- ✅ **CryptoCompare client** with OHLC methods (`get_daily_ohlc`, `get_hourly_ohlc`, `get_price_at_timestamp`)
- ✅ **Twelve Data client** with OHLC methods (`get_historical_ohlcv`)
- ✅ **OutcomeTracker** with checkpoint data structure
- ✅ **Integration points** in `historical_scraper.py`
- ✅ **Caching infrastructure** for historical data
- ✅ **Batch processing** support

### What's Missing (10%)

- 🔧 24-hour lookback logic (~100 lines)
- 🔧 Forward OHLC ATH calculation (~100 lines)
- 🔧 Checkpoint ROI from OHLC (~50 lines)
- 🔧 Integration updates (~50 lines)

**Total new code**: ~300 lines

---

## 🏆 Recommended Solution: CryptoCompare Primary

### Why CryptoCompare?

1. **Best rate limits**: 100,000 calls/month (vs 800/day for Twelve Data)
2. **Complete features**: Entry price + OHLC in one API
3. **Already integrated**: Client exists with all methods
4. **Symbol-based**: Works with BTC, ETH, SOL (no address mapping)
5. **Proven reliability**: Used in production

### API Fallback Chain

```
Entry Price (24h lookback):
  CryptoCompare → Twelve Data → Current Price

Forward OHLC (30 days):
  CryptoCompare → Twelve Data → Skip
```

### Capacity

- **CryptoCompare**: 1,650 signals/day (2 calls per signal)
- **With Twelve Data fallback**: 2,050 signals/day
- **More than enough** for typical usage

---

## 📋 Implementation Plan

### Phase 1: Enhance HistoricalPriceRetriever (4 hours)

**File**: `services/pricing/historical_price_retriever.py`

1. **Add 24h lookback method** (1 hour)

   - Try: message_timestamp - 24h
   - Fallback: message_timestamp - 12h
   - Fallback: message_timestamp
   - Fallback: current_price

2. **Add forward OHLC ATH calculation** (1.5 hours)

   - Fetch 30 days of OHLC from CryptoCompare
   - Find max(high) across all candles
   - Record ATH timestamp and days_to_ath
   - Add Twelve Data fallback

3. **Add checkpoint ROI from OHLC** (1 hour)

   - For each checkpoint, find matching candle
   - Use candle's close price
   - Calculate ROI = close_price / entry_price

4. **Update existing methods** (30 minutes)
   - Add data completeness tracking
   - Update caching

### Phase 2: Update historical_scraper.py (2 hours)

**File**: `scripts/historical_scraper.py`

1. **Update entry price logic** (30 minutes)

   - Replace with 24h lookback

2. **Update checkpoint calculation** (1 hour)

   - Use OHLC-based calculation
   - Update SignalOutcome with OHLC data

3. **Update statistics** (30 minutes)
   - Add new metrics

### Phase 3: Testing & Validation (4 hours)

1. **Unit tests** (2 hours)
2. **Integration tests** (1 hour)
3. **Manual validation** (1 hour)

### Phase 4: Configuration & Docs (1.5 hours)

1. **Update configuration** (30 minutes)
2. **Update documentation** (1 hour)

### Phase 5: Deployment (1 hour)

1. **Deploy to production**
2. **Monitor & optimize**

**Total time**: ~12.5 hours (~2 days)

---

## 📊 Success Metrics

### Accuracy

- ✅ Entry price accuracy: ≥95%
- ✅ ATH accuracy: ≥98%
- ✅ Checkpoint ROI accuracy: ≥95%
- ✅ Data completeness: ≥80%

### Performance

- ✅ API calls per signal: ≤2
- ✅ Processing time: ≤1 second/signal
- ✅ Batch processing: ≥50 signals/minute

### Reliability

- ✅ API fallback success: ≥95%
- ✅ Error rate: ≤5%

---

## 📁 Files to Modify

| File                                             | Changes       | Lines | Priority |
| ------------------------------------------------ | ------------- | ----- | -------- |
| `services/pricing/historical_price_retriever.py` | Add 3 methods | ~200  | HIGH     |
| `scripts/historical_scraper.py`                  | Update logic  | ~50   | HIGH     |
| `repositories/api_clients/coingecko_client.py`   | Add OHLC      | ~100  | LOW      |
| `.env.example`                                   | Add configs   | ~10   | LOW      |

---

## 🔍 Key Implementation Details

### 24-Hour Lookback Logic

```python
async def fetch_entry_price_with_24h_lookback(
    self, symbol: str, message_timestamp: datetime
) -> Optional[float]:
    # Try 24h before message
    lookback_24h = message_timestamp - timedelta(hours=24)
    price = await self._fetch_cryptocompare_price_at_timestamp(symbol, lookback_24h)
    if price: return price

    # Try 12h before message
    lookback_12h = message_timestamp - timedelta(hours=12)
    price = await self._fetch_cryptocompare_price_at_timestamp(symbol, lookback_12h)
    if price: return price

    # Try message timestamp
    price = await self._fetch_cryptocompare_price_at_timestamp(symbol, message_timestamp)
    if price: return price

    # Fallback to Twelve Data
    price = await self._fetch_twelvedata_price_at_timestamp(symbol, message_timestamp)
    return price
```

### Forward OHLC ATH Calculation

```python
async def fetch_ath_from_forward_ohlc(
    self, symbol: str, entry_timestamp: datetime, window_days: int = 30
) -> Optional[Dict]:
    # Fetch OHLC from CryptoCompare
    ohlc_data = await self.cryptocompare_client.get_daily_ohlc(
        symbol=symbol, limit=window_days
    )

    if not ohlc_data:
        # Fallback to Twelve Data
        ohlc_data = await self.twelvedata_client.get_historical_ohlcv(
            symbol=f"{symbol}/USD", outputsize=window_days
        )

    # Find ATH
    ath_candle = max(ohlc_data, key=lambda c: c['high'])

    return {
        'ath_price': ath_candle['high'],
        'ath_timestamp': datetime.fromtimestamp(ath_candle['time']),
        'days_to_ath': (ath_timestamp - entry_timestamp).days,
        'candles': ohlc_data
    }
```

### Checkpoint ROI Calculation

```python
async def calculate_checkpoint_rois_from_ohlc(
    self, entry_price: float, entry_timestamp: datetime,
    checkpoints: List[Tuple[str, timedelta]], candles: List[Dict]
) -> Dict[str, float]:
    checkpoint_rois = {}

    for checkpoint_name, delta in checkpoints:
        checkpoint_time = entry_timestamp + delta

        # Find matching candle
        candle = self._find_candle_at_time(candles, checkpoint_time)
        if candle:
            checkpoint_price = candle['close']
            roi_multiplier = checkpoint_price / entry_price
            checkpoint_rois[checkpoint_name] = roi_multiplier

    return checkpoint_rois
```

---

## 🚨 Risk Mitigation

| Risk                    | Mitigation                                  |
| ----------------------- | ------------------------------------------- |
| API rate limits         | Exponential backoff, caching, fallback APIs |
| Missing historical data | 24h → 12h → 0h fallback, track completeness |
| Symbol mapping issues   | Use CryptoCompare (symbol-based)            |
| Performance degradation | Batch processing, async/await, caching      |

---

## 📚 Documentation

### Created Documents

1. **24h-lookback-ohlc-analysis.md** - Complete technical analysis
2. **api-comparison-summary.md** - API comparison and recommendations
3. **implementation-checklist.md** - Step-by-step implementation tasks
4. **IMPLEMENTATION-SUMMARY.md** - This document (executive summary)

### Key Resources

- CryptoCompare API: https://min-api.cryptocompare.com/documentation
- Twelve Data API: https://twelvedata.com/docs
- HistoricalPriceRetriever: `services/pricing/historical_price_retriever.py`
- CryptoCompare Client: `repositories/api_clients/cryptocompare_client.py`

---

## 🎯 Next Steps

1. ✅ **Analysis complete** (DONE)
2. 🔧 **Implement Phase 1**: Enhance HistoricalPriceRetriever
3. 🔧 **Implement Phase 2**: Update historical_scraper
4. 🧪 **Test with real data**: 100 historical messages
5. 📊 **Validate accuracy**: Compare with manual calculations
6. 🚀 **Deploy**: Integrate into production

---

## ✅ Conclusion

**Infrastructure**: 90% ready, just need to wire up the logic

**Recommended approach**: CryptoCompare primary + Twelve Data fallback

**Timeline**: 2 days for implementation + testing

**Confidence**: HIGH - All infrastructure exists, just need to connect the pieces

**Risk**: LOW - Proven APIs, existing clients, clear fallback chain

**Ready to implement**: YES ✅
