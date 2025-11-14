================================================================================
HISTORICAL SCRAPER VERIFICATION REPORT
================================================================================

Generated: 2025-11-13 19:15:30

================================================================================
SUMMARY STATISTICS
================================================================================
Total messages fetched: 80
Successfully processed: 80
Processing errors: 0
Success rate: 100.0%

================================================================================
HDRB SCORE STATISTICS
================================================================================
Minimum: 0.30/100
Maximum: 8.80/100
Average: 2.35/100

================================================================================
CRYPTO DETECTION STATISTICS
================================================================================
Crypto relevant messages: 53/80
Crypto relevance rate: 66.2%

================================================================================
ADDRESS EXTRACTION STATISTICS (PART 3)
================================================================================
Total addresses found: 15
EVM addresses (Ethereum, BSC, Polygon, etc.): 12
Solana addresses: 3
Invalid addresses: 1
Validation rate: 93.3%

================================================================================
PRICE FETCHING STATISTICS (PART 3)
================================================================================
Valid addresses: 14
Prices fetched: 9
Price failures: 0
Price fetch success rate: 64.3%

API Usage Breakdown:
  coingecko+dexscreener: 7 requests (77.8%)
  coingecko+blockscout: 2 requests (22.2%)

================================================================================
PERFORMANCE TRACKING STATISTICS (PART 3 - TASK 3)
================================================================================
New addresses tracked: 8
Existing addresses updated: 0
Performance ATH updates detected: 0
Outcome ATH updates detected: 0

================================================================================
MULTI-TABLE OUTPUT STATISTICS (PART 3 - TASK 4)
================================================================================
Messages written: 53
Token prices written: 9
Performance records written: 8
Historical records written: 8

================================================================================
PART 8: CHANNEL REPUTATION + OUTCOME LEARNING
================================================================================
Signals tracked: 8
Dead tokens detected: 0
Dead tokens skipped (blacklisted): 5
Winners classified (ROI ≥ 1.5x): 2
Losers classified (ROI < 1.5x): 7
Reputations calculated: 1

Channel Reputations:

  Eric Cryptomans Journal:
    Reputation Score: 55.8/100 (Unproven)
    Total Signals: 7
    Win Rate: 14.3% (1 winners)
    Average ROI: 11.142x (1014.2% gain)
    Sharpe Ratio: 0.38
    Speed Score: 84.4
    Expected ROI: 6.766x

Total addresses in tracker: 8

Addresses by chain:
  evm: 8

Average ATH multiplier (since tracking started): 9.89x

Best performer (since tracking started):
  Address: 0x21e133e0...
  Chain: evm
  ATH Multiplier: 71.10x
  Start Price: $0.000464
  ATH Price: $0.033023
  Note: For historical signals, see OutcomeTracker for 30-day ATH

================================================================================
SENTIMENT ANALYSIS STATISTICS
================================================================================
Positive: 23
Negative: 4
Neutral: 53

================================================================================
CONFIDENCE STATISTICS
================================================================================
High confidence messages: 21/80
High confidence rate: 26.2%
Average confidence: 0.31

================================================================================
PERFORMANCE STATISTICS
================================================================================
Average processing time: 0.81ms
Minimum processing time: 0.38ms
Maximum processing time: 2.89ms
✓ Performance target met (< 100ms)

================================================================================
VERIFICATION STATUS
================================================================================
✓ Messages processed successfully
✓ HDRB scores calculated
✓ Crypto detection working
✓ Sentiment analysis working
✓ Confidence scores calculated
✓ Performance targets met
✓ Address extraction working (Part 3)
✓ Price fetching working (Part 3)
✓ Performance tracking working (Part 3 - Task 3)
✓ Performance tracker has data (Part 3 - Task 3)
✗ CSV writer initialized (Part 3 - Task 3)
✓ Messages written to MESSAGES table (Part 3 - Task 4)
✓ Token prices written to TOKEN_PRICES table (Part 3 - Task 4)
✓ Performance written to PERFORMANCE table (Part 3 - Task 4)
✓ Historical data fetching implemented (Part 3 - Task 4)
✓ ✓ Signals tracked with entry price and ROI (Part 8 - Task 1)
✓ ✓ Winners classified (ROI ≥ 1.5x) (Part 8 - Task 1)
✓ ✓ Channel reputations calculated from outcomes (Part 8 - Task 2)

Verification: 17/18 checks passed

✗ 1 verification check(s) failed

================================================================================