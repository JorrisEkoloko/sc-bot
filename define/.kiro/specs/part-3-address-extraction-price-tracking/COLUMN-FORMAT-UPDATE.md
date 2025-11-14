# CSV Column Format Update

## Summary of Changes

**Previous Format:** 26 columns
**New Format:** 23 columns
**Net Change:** -3 columns (removed 6, added 3)

---

## Columns Removed (6)

| Column               | Reason for Removal                           |
| -------------------- | -------------------------------------------- |
| `hdrb_raw`           | Redundant - hdrb_score is sufficient         |
| `sentiment_score`    | Redundant - sentiment category is sufficient |
| `processing_time_ms` | Internal metric, not business-critical       |
| `error`              | Internal metric, logged separately           |
| `replies`            | Low engagement metric, rarely used           |
| `reactions`          | Low engagement metric, rarely used           |

---

## Columns Added (3)

| Column            | Data Source       | Description                                              |
| ----------------- | ----------------- | -------------------------------------------------------- |
| `time_to_ath`     | Local calculation | Duration (in seconds) from tracking start to ATH         |
| `is_at_ath`       | Local calculation | Boolean flag indicating if token is currently at ATH     |
| `pair_created_at` | DexScreener API   | Unix timestamp when trading pair was created (token age) |

---

## Final 23-Column Format

```
1.  timestamp              # Message timestamp
2.  channel_name           # Telegram channel name
3.  message_id             # Message ID
4.  message_text           # Message content
5.  hdrb_score             # HDRB score (0-100)
6.  crypto_mentions        # Detected tickers/addresses
7.  addresses              # Validated blockchain addresses
8.  sentiment              # Sentiment (positive/negative/neutral)
9.  confidence             # Overall confidence score
10. is_high_confidence     # Boolean flag
11. price_usd              # Current price in USD
12. market_cap             # Market capitalization
13. volume_24h             # 24-hour trading volume
14. price_change_24h       # 24-hour price change %
15. ath_price              # All-time high price (since tracking)
16. ath_multiplier         # ATH multiplier (ath_price / start_price)
17. current_multiplier     # Current multiplier (current_price / start_price)
18. days_tracked           # Days since tracking started
19. time_to_ath            # Seconds from start to ATH
20. is_at_ath              # Boolean: currently at ATH?
21. pair_created_at        # Unix timestamp of pair creation
22. forwards               # Message forwards count
23. views                  # Message views count
```

---

## Data Availability Verification

### ✅ All 23 Columns Can Be Populated

| Column | Source                  | Available? |
| ------ | ----------------------- | ---------- |
| 1-4    | Telegram                | ✅ YES     |
| 5-10   | Part 2 (Local)          | ✅ YES     |
| 11-14  | APIs (All 4)            | ✅ YES     |
| 15-18  | Part 3 (Local Tracking) | ✅ YES     |
| 19-20  | Part 3 (Calculated)     | ✅ YES     |
| 21     | DexScreener API         | ✅ YES     |
| 22-23  | Telegram                | ✅ YES     |

---

## Benefits of New Format

### 1. **More Focused Data**

- Removed redundant metrics (hdrb_raw, sentiment_score)
- Removed internal metrics (processing_time_ms, error)
- Removed low-value engagement metrics (replies, reactions)

### 2. **Enhanced Performance Insights**

- `time_to_ath`: Understand how quickly tokens reach peak
- `is_at_ath`: Identify tokens currently at peak performance
- `pair_created_at`: Assess token age and maturity

### 3. **Better Business Intelligence**

- Cleaner dataset for analysis
- More actionable performance metrics
- Token age context for risk assessment

### 4. **Maintained Completeness**

- All essential business metrics retained
- No loss of critical information
- Enhanced with valuable new metrics

---

## Implementation Notes

### PriceData Dataclass Update

```python
@dataclass
class PriceData:
    price_usd: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    pair_created_at: Optional[int] = None  # NEW: Unix timestamp
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
```

### PerformanceData Dataclass (Already Has These)

```python
@dataclass
class PerformanceData:
    # ... existing fields ...
    time_to_ath: Optional[timedelta] = None  # Already defined
    is_at_ath: bool = False  # Already defined
```

### DexScreener Client Update

Extract `pairCreatedAt` from API response:

```python
return PriceData(
    price_usd=safe_float(pair.get('priceUsd'), 0.0),
    market_cap=safe_float(pair.get('marketCap')),
    volume_24h=safe_float(volume_24h),
    price_change_24h=safe_float(price_change_24h),
    pair_created_at=pair.get('pairCreatedAt')  # NEW
)
```

---

## Migration Impact

### Files Updated

1. ✅ `.kiro/specs/part-3-address-extraction-price-tracking/tasks.md`
2. ✅ `.kiro/specs/part-3-address-extraction-price-tracking/design.md`
3. ✅ `.kiro/specs/part-3-address-extraction-price-tracking/requirements.md`

### Implementation Files to Update

1. `core/api_clients/base_client.py` - Add `pair_created_at` to PriceData
2. `core/api_clients/dexscreener_client.py` - Extract `pairCreatedAt`
3. `core/data_output.py` - Update COLUMNS list and row mapping

### No Breaking Changes

- Existing data structures remain compatible
- Only CSV output format changes
- All existing functionality preserved

---

## Validation Checklist

- [x] Verified `time_to_ath` can be calculated from existing data
- [x] Verified `is_at_ath` can be calculated from existing data
- [x] Verified `pair_created_at` is available from DexScreener API
- [x] Updated all documentation references to column count
- [x] Updated CSV column list in design document
- [x] Updated requirements document
- [x] Updated tasks document
- [x] Created migration notes

---

## Next Steps

1. Update `core/api_clients/base_client.py` - Add `pair_created_at` field
2. Update `core/api_clients/dexscreener_client.py` - Extract pair creation timestamp
3. Update `core/data_output.py` - Implement new 23-column format
4. Test with historical scraper to verify all columns populate correctly
5. Verify Google Sheets conditional formatting works with new format

---

**Status:** ✅ Documentation Updated - Ready for Implementation
