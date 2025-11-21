================================================================================
HISTORICAL SCRAPER VERIFICATION REPORT
================================================================================

Generated: 2025-11-15 23:49:21

================================================================================
SUMMARY STATISTICS
================================================================================
Total messages fetched: 42
Successfully processed: 42
Processing errors: 0
Success rate: 100.0%

================================================================================
HDRB SCORE STATISTICS
================================================================================
Minimum: 0.30/100
Maximum: 7.40/100
Average: 1.93/100

================================================================================
CRYPTO DETECTION STATISTICS
================================================================================
Crypto relevant messages: 27/42
Crypto relevance rate: 64.3%

================================================================================
ADDRESS EXTRACTION STATISTICS (PART 3)
================================================================================
Total addresses found: 5
EVM addresses (Ethereum, BSC, Polygon, etc.): 4
Solana addresses: 1
Invalid addresses: 0
Validation rate: 100.0%

================================================================================
PRICE FETCHING STATISTICS (PART 3)
================================================================================
Valid addresses: 5
Prices fetched: 2
Price failures: 0
Price fetch success rate: 40.0%

API Usage Breakdown:
  coingecko+dexscreener: 2 requests (100.0%)

================================================================================
PERFORMANCE TRACKING STATISTICS (PART 3 - TASK 3)
================================================================================
New addresses tracked: 0
Existing addresses updated: 0
Performance ATH updates detected: 0
Outcome ATH updates detected: 0

================================================================================
MULTI-TABLE OUTPUT STATISTICS (PART 3 - TASK 4)
================================================================================
Messages written: 27
Token prices written: 2
Performance records written: 1
Historical records written: 1

================================================================================
PART 8: CHANNEL REPUTATION + OUTCOME LEARNING
================================================================================
Signals tracked: 1
Dead tokens detected: 0
Dead tokens skipped (blacklisted): 3
Winners classified (ROI ≥ 1.5x): 0
Losers classified (ROI < 1.5x): 1
Reputations calculated: 1

Channel Reputations:

  Eric Cryptomans Journal:
    Reputation Score: 56.1/100 (Unproven)
    Total Signals: 7
    Win Rate: 14.3% (1 winners)
    Average ROI: 11.989x (1098.9% gain)
    Sharpe Ratio: 0.38
    Speed Score: 86.6
    Expected ROI: 12.915x

Total addresses in tracker: 8

Addresses by chain:
  evm: 8

Average ATH multiplier (since tracking started): 10.65x

Best performer (since tracking started):
  Address: 0x21e133e0...
  Chain: evm
  ATH Multiplier: 76.99x
  Start Price: $0.000429
  ATH Price: $0.033023
  Note: For historical signals, see OutcomeTracker for 30-day ATH

================================================================================
SENTIMENT ANALYSIS STATISTICS
================================================================================
Positive: 10
Negative: 1
Neutral: 31

================================================================================
CONFIDENCE STATISTICS
================================================================================
High confidence messages: 7/42
High confidence rate: 16.7%
Average confidence: 0.28

================================================================================
PERFORMANCE STATISTICS
================================================================================
Average processing time: 0.75ms
Minimum processing time: 0.39ms
Maximum processing time: 1.41ms
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
✗ Performance tracking working (Part 3 - Task 3)
✓ Performance tracker has data (Part 3 - Task 3)
✗ CSV writer initialized (Part 3 - Task 3)
✓ Messages written to MESSAGES table (Part 3 - Task 4)
✓ Token prices written to TOKEN_PRICES table (Part 3 - Task 4)
✓ Performance written to PERFORMANCE table (Part 3 - Task 4)
✓ Historical data fetching implemented (Part 3 - Task 4)
✓ ✓ Signals tracked with entry price and ROI (Part 8 - Task 1)
✓ ✓ Winners classified (ROI ≥ 1.5x) (Part 8 - Task 1)
✓ ✓ Channel reputations calculated from outcomes (Part 8 - Task 2)

Verification: 16/18 checks passed

✗ 2 verification check(s) failed

================================================================================