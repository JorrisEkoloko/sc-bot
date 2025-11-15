# Implementation Plan - Part 8: Channel Reputation + Outcome Learning (ROI-Driven)

## Core Principle

**Every component in Part 8 exists to answer one question: "What ROI can I expect from this channel?"**

The entire reputation system is built around ROI (Return on Investment):

1. Channel mentions token at entry price X
2. System tracks price to ATH price Y
3. Calculate ROI = (Y - X) / X
4. Update channel reputation based on actual ROI
5. Predict future ROI using temporal difference learning

---

## - [ ] 1. Implement ROI calculation and tracking at checkpoints

Create the core ROI calculation system that tracks returns at multiple time intervals.

**ROI Focus**: This is the foundation - accurate ROI calculation at every checkpoint (1h, 4h, 24h, 3d, 7d, 30d) to measure channel performance.

**Implementation Details**:

- Create `intelligence/outcome_tracker.py` with OutcomeTracker class
- Implement SignalOutcome data class to store entry price and ROI at each checkpoint
- Implement CheckpointData data class with ROI percentage and multiplier
- Add ROI calculation: `roi_percentage = ((current_price - entry_price) / entry_price) * 100`
- Add multiplier calculation: `roi_multiplier = current_price / entry_price`
- Track ROI at checkpoints: 1h, 4h, 24h, 3d, 7d, 30d
- Identify ATH (highest ROI achieved) and days to reach it
- Determine if signal is "winner" (ROI ≥ 2.0x = 100% gain)
- Add JSON persistence for signal outcomes

**External Verification with fetch MCP**:

- Verify ROI formula: https://www.investopedia.com/terms/r/returnoninvestment.asp
- Verify pump-and-dump lifecycle: https://www.investopedia.com/terms/p/pumpanddump.asp
- Verify checkpoint timing for crypto trading patterns

**Files to Create**:

- `intelligence/outcome_tracker.py` (~350 lines)
- `intelligence/__init__.py` (update exports)
- `data/reputation/signal_outcomes.json` (created at runtime)

**Validation**:

- Calculate ROI correctly: entry $1.47, current $4.78 → ROI = 225.2%, multiplier = 3.252x
- Track ROI at each checkpoint (1h, 4h, 24h, 3d, 7d, 30d)
- Identify ATH: highest ROI multiplier achieved
- Determine winner: ROI ≥ 2.0x (100% gain)
- Calculate days to ATH for speed metrics
- Test ROI calculation → $1.47 to $4.78 = 3.252x ✓
- Test checkpoint tracking → 1h: 1.034x, 4h: 1.286x, 24h: 3.252x ✓
- Test ATH detection → 3.252x is highest = ATH ✓
- Test winner classification → 3.252x ≥ 2.0x = winner ✓
- Test persistence → outcomes saved with all ROI data ✓

**Historical Scraper Verification**:

Run `python scripts/historical_scraper.py` and verify:

1. ✓ OutcomeTracker initialized successfully
2. ✓ Signals tracked with entry price and ROI
3. ✓ Checkpoints calculated at each price update
4. ✓ ATH detected and tracked correctly
5. ✓ Winners classified (ROI ≥ 2.0x)
6. ✓ Signal outcomes saved to JSON
7. ✓ Logs show: "OutcomeTracker: Tracking signal [address] at entry price $X"
8. ✓ Logs show: "Checkpoint 1h: ROI X.XXx"
9. ✓ Logs show: "ATH reached: X.XXx at checkpoint [time]"
10. ✓ Logs show: "Signal complete: WINNER (ROI ≥ 2.0x)" or "Signal complete: LOSER (ROI < 2.0x)"

**ROI Output Example**:

```
Signal: AVICI at $1.47
1h ROI: 3.4% (1.034x)
4h ROI: 28.6% (1.286x)
24h ROI: 225.2% (3.252x) ← ATH
Result: WINNER (>2x threshold)
```

**Requirements**: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5

---

## - [ ] 2. Calculate channel reputation from aggregated ROI metrics

Create the reputation engine that aggregates ROI outcomes to calculate channel quality scores.

**ROI Focus**: Transform individual signal ROIs into channel-level metrics that answer "What ROI can I expect?"

**Implementation Details**:

- Create `intelligence/channel_reputation.py` with ReputationEngine class
- Implement ChannelReputation data class with ROI-based metrics
- Calculate **Win Rate**: % of signals with ROI ≥ 2.0x (100% gain)
- Calculate **Average ROI**: Mean ROI multiplier across all signals
- Calculate **Sharpe Ratio**: (avg_roi - 1.0) / std_dev(roi) for risk-adjusted returns
- Calculate **Speed Score**: Average days to reach ATH (faster = better ROI timing)
- Calculate **Composite Reputation Score**: Weighted formula based on ROI metrics
  - Win Rate × 30% (most important psychologically)
  - Avg ROI × 25% (financial outcome)
  - Sharpe Ratio × 20% (risk-adjusted)
  - Speed × 15% (meme coins move fast)
  - Confidence × 10% (signal quality)
- Classify into reputation tiers based on ROI performance
- Add JSON persistence for channel reputations

**External Verification with fetch MCP**:

- Verify Sharpe ratio: https://www.investopedia.com/terms/s/sharperatio.asp
- Verify reputation systems: https://en.wikipedia.org/wiki/Reputation_system
- Verify weighted scoring methodologies

**Files to Create**:

- `intelligence/channel_reputation.py` (~450 lines)
- `data/reputation/channels.json` (created at runtime)

**Validation**:

- Calculate win rate from ROI outcomes: 10 wins (≥2x) out of 15 signals = 66.7%
- Calculate average ROI: (3.252x + 0.932x + 2.150x + ...) / 15 = 1.85x
- Calculate Sharpe ratio: (1.85 - 1.0) / 0.95 = 0.89
- Calculate speed score: average 2.3 days to ATH
- Calculate composite score: (66.7 × 0.30) + (1.85 × 25) + (0.89 × 20) + (78.5 × 0.15) + (82 × 0.10) = 59.5/100
- Classify tier: 59.5 = "Average" tier
- Test win rate → 10/15 = 66.7% ✓
- Test average ROI → 1.85x (85% average gain) ✓
- Test Sharpe ratio → 0.89 (risk-adjusted) ✓
- Test composite score → 59.5/100 ✓
- Test tier classification → "Average" ✓
- Test persistence → reputation saved with all metrics ✓

**Historical Scraper Verification**:

Run `python scripts/historical_scraper.py` and verify:

1. ✓ ReputationEngine initialized successfully
2. ✓ Channel reputations calculated from outcomes
3. ✓ Win rate, avg ROI, Sharpe ratio computed correctly
4. ✓ Composite reputation score calculated (0-100)
5. ✓ Reputation tier assigned (Elite/Excellent/Good/Average/Poor)
6. ✓ Reputations saved to channels.json
7. ✓ Logs show: "ReputationEngine: Calculating reputation for [channel]"
8. ✓ Logs show: "Win Rate: XX.X% (X/X signals ≥2x)"
9. ✓ Logs show: "Average ROI: X.XXx (XX% average gain)"
10. ✓ Logs show: "Reputation Score: XX.X/100 → [Tier]"

**ROI Output Example**:

```
Channel: Eric Cryptomans Journal
Win Rate: 66.7% (10/15 signals ≥2x)
Average ROI: 1.85x (85% average gain)
Sharpe Ratio: 0.89 (risk-adjusted)
Speed: 2.3 days to ATH
Reputation Score: 59.5/100 → "Average" tier
Expected ROI: 1.85x (85% gain per signal)
```

**Requirements**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7

---

## - [ ] 3. Implement multi-dimensional temporal difference learning to predict future ROI

Implement TD learning at THREE levels: overall channel, coin-specific, and cross-channel. Track ALL prediction errors with comprehensive metadata for complete learning history.

**ROI Focus**: Learn from prediction errors at multiple dimensions - "Eric typically delivers 1.85x, but Eric calling AVICI delivers 2.55x, and AVICI across all channels delivers 2.08x"

**Implementation Details**:

**Level 1: Overall Channel TD Learning**

- Add `expected_roi` field to ChannelReputation (already exists, enhance usage)
- Implement `apply_td_learning()` method: `new_expected_roi = old_expected_roi + alpha * (actual_roi - old_expected_roi)`
- Set learning rate alpha = 0.1 for gradual adaptation
- Track ALL prediction errors (no 100-error limit) with full metadata
- Change `prediction_error_history` from `List[float]` to `List[dict]` with:
  - timestamp, signal_id, coin_symbol, coin_address
  - predicted_roi, actual_roi, error, error_percentage
  - entry_price, ath_price, days_to_ath, outcome_category
- Add statistics: `total_predictions`, `correct_predictions` (within 10%), `overestimations`, `underestimations`
- Calculate `mean_absolute_error` and `mean_squared_error` from all errors
- Apply recency weighting: recent signals matter more (lambda = 0.01 decay)

**Level 2: Coin-Specific TD Learning (NEW!)**

- Add `coin_specific_performance` dict to ChannelReputation
- Create `CoinSpecificPerformance` dataclass with:
  - symbol, address, total_mentions, signals list
  - average_roi, expected_roi (TD learning per coin)
  - win_rate, best_roi, worst_roi
  - prediction_error_history (ALL errors for this coin)
  - total_predictions, correct_predictions, overestimations, underestimations
  - mean_absolute_error, last_mentioned, days_since_last_mention
- Implement `apply_coin_specific_td_learning()` method
- First mention of coin initializes expected_roi with actual outcome
- Subsequent mentions update using TD learning formula
- Track which coins channel is good/bad at

**Level 3: Cross-Channel Coin Tracking (NEW!)**

- Create `domain/coin_cross_channel.py` with:
  - `CoinCrossChannel` dataclass (coin performance across all channels)
  - `ChannelCoinPerformance` dataclass (how each channel performs on this coin)
- Create `repositories/file_storage/coin_cross_channel_repository.py`
- Implement `update_cross_channel_coin_performance()` method
- Track: total_mentions, total_channels, average_roi_all_channels
- Identify best_channel and worst_channel for each coin
- Calculate insights: consensus strength, recommendation
- Save to `data/reputation/coins_cross_channel.json`

**Multi-Dimensional Prediction**

- When new signal arrives, combine predictions from all 3 levels:
  - Overall channel: 40% weight
  - Coin-specific: 50% weight (most important!)
  - Cross-channel: 10% weight
- Weighted prediction = (overall × 0.40) + (coin_specific × 0.50) + (cross_channel × 0.10)

**External Verification with fetch MCP**:

- Verify TD learning: https://en.wikipedia.org/wiki/Temporal_difference_learning
- Verify reinforcement learning: https://en.wikipedia.org/wiki/Reinforcement_learning
- Verify learning rate selection
- Verify multi-dimensional learning patterns

**Files to Modify**:

- `services/reputation/reputation_engine.py` (add 3 TD learning methods)
- `domain/channel_reputation.py` (add CoinSpecificPerformance, enhance error tracking)

**Files to Create**:

- `domain/coin_cross_channel.py` (~150 lines)
- `repositories/file_storage/coin_cross_channel_repository.py` (~100 lines)
- `data/reputation/coins_cross_channel.json` (created at runtime)

**Validation**:

**Overall Channel TD Learning:**

- Initialize expected ROI: 1.50x (neutral starting point)
- Signal 1 (AVICI) completes: actual ROI = 3.252x
- Calculate error: 3.252 - 1.50 = +1.752x (underestimated)
- Update expected ROI: 1.50 + (0.1 × 1.752) = 1.675x
- Store error with full metadata (timestamp, coin, prices, outcome)
- Calculate statistics: total_predictions=1, underestimations=1, MAE=1.752x
- Test TD update → 1.50x becomes 1.675x ✓
- Test error metadata → includes all context ✓
- Test statistics → MAE, MSE, accuracy calculated ✓

**Coin-Specific TD Learning:**

- Signal 1 (AVICI): Initialize AVICI expected_roi = 3.252x (first mention)
- Signal 2 (AVICI): Actual ROI = 1.85x, Error = -1.402x
- Update AVICI expected_roi: 3.252 + (0.1 × -1.402) = 3.112x
- Signal 1 (NKP): Initialize NKP expected_roi = 0.932x (different coin)
- Test coin-specific tracking → each coin has own expected_roi ✓
- Test first mention → initializes with actual outcome ✓
- Test subsequent mentions → updates with TD learning ✓
- Test multiple coins → tracked independently ✓

**Cross-Channel Tracking:**

- AVICI called by Eric: 2 signals, avg 2.551x
- AVICI called by Crypto Signals Pro: 2 signals, avg 2.200x
- Overall AVICI: (2.551 + 2.200) / 2 = 2.376x
- Best channel: Eric Cryptomans Journal
- Test cross-channel aggregation → correct average ✓
- Test best/worst identification → Eric is best ✓
- Test persistence → coins_cross_channel.json saved ✓

**Multi-Dimensional Prediction:**

- New AVICI signal from Eric
- Overall: 1.675x (40% weight) = 0.670
- Coin-specific (AVICI): 3.112x (50% weight) = 1.556
- Cross-channel (AVICI): 2.376x (10% weight) = 0.238
- Weighted prediction: 0.670 + 1.556 + 0.238 = 2.464x
- Test weighted prediction → combines all 3 sources ✓

**Historical Scraper Verification**:

Run `python scripts/historical_scraper.py` and verify:

**Overall Channel TD Learning:**

1. ✓ TD learning updates overall expected ROI after each signal
2. ✓ ALL prediction errors tracked with full metadata (no limit)
3. ✓ Error records include: timestamp, coin, prices, outcome
4. ✓ Statistics calculated: total_predictions, correct_predictions, MAE, MSE
5. ✓ Expected ROI converges toward actual average ROI
6. ✓ Logs show: "TD Learning (Overall): {channel} Expected ROI X.XXx → X.XXx (error: +X.XXx)"
7. ✓ Logs show: "Total Predictions: X, Accuracy: XX.X%, MAE: X.XXx"
8. ✓ Verify channels.json contains ALL error history
9. ✓ Verify statistics fields populated correctly
10. ✓ Verify error metadata includes all context

**Coin-Specific TD Learning:** 11. ✓ TD learning updates coin-specific expected ROI after each signal 12. ✓ First mention initializes with actual outcome (no prediction yet) 13. ✓ Subsequent mentions update using TD learning 14. ✓ Each coin tracks its own prediction errors 15. ✓ Coin-specific expected ROI converges to coin-specific average 16. ✓ Different coins have different expected ROIs for same channel 17. ✓ Logs show: "TD Learning (Coin-Specific): {channel} → {coin} Expected ROI X.XXx → X.XXx" 18. ✓ Logs show: "Coin Predictions: X, Coin Accuracy: XX.X%, Coin MAE: X.XXx" 19. ✓ Verify coin_specific_performance dict populated 20. ✓ Verify each coin has independent learning history

**Cross-Channel Tracking:** 21. ✓ Cross-channel data updates when any channel completes signal for coin 22. ✓ Overall coin average calculated across all channels 23. ✓ Best/worst channels identified for each coin 24. ✓ Insights generated (consensus strength, recommendation) 25. ✓ Logs show: "Cross-Channel Update: {coin} - Best: {channel} ({roi}x)" 26. ✓ Verify coins_cross_channel.json created and updated 27. ✓ Verify channel_performance dict per coin 28. ✓ Verify best_channel and worst_channel identified

**Multi-Dimensional Prediction:** 29. ✓ Weighted prediction combines all 3 sources 30. ✓ Coin-specific gets highest weight (50%) 31. ✓ Overall channel gets 40% weight 32. ✓ Cross-channel gets 10% weight 33. ✓ Logs show: "Prediction: Overall X.XXx (40%), Coin-Specific X.XXx (50%), Cross-Channel X.XXx (10%) = X.XXx"

**ROI Learning Example**:

```
=== OVERALL CHANNEL LEARNING ===
Initial: Expected ROI = 1.50x

Signal 1 (AVICI): Actual ROI = 3.252x → Error = +1.752x
Update: Expected ROI = 1.50 + (0.1 × 1.752) = 1.675x
Store: {timestamp, signal_id, coin: "AVICI", predicted: 1.50, actual: 3.252, error: +1.752}
Stats: total_predictions=1, underestimations=1, MAE=1.752x

Signal 2 (NKP): Actual ROI = 0.932x → Error = -0.743x
Update: Expected ROI = 1.675 + (0.1 × -0.743) = 1.601x
Store: {timestamp, signal_id, coin: "NKP", predicted: 1.675, actual: 0.932, error: -0.743}
Stats: total_predictions=2, overestimations=1, underestimations=1, MAE=1.248x

Result: Overall expected ROI = 1.601x


=== COIN-SPECIFIC LEARNING ===
AVICI Signals:
Signal 1: Actual ROI = 3.252x
  → Initialize AVICI expected_roi = 3.252x
  → Store: {signal_number: 1, predicted: null, actual: 3.252, note: "First signal"}

Signal 2: Actual ROI = 1.85x → Error = -1.402x
  → Update AVICI expected_roi = 3.252 + (0.1 × -1.402) = 3.112x
  → Store: {signal_number: 2, predicted: 3.252, actual: 1.85, error: -1.402}

Result: AVICI expected ROI = 3.112x (different from overall!)

NKP Signals:
Signal 1: Actual ROI = 0.932x
  → Initialize NKP expected_roi = 0.932x

Result: NKP expected ROI = 0.932x (much lower than overall!)


=== CROSS-CHANNEL LEARNING ===
AVICI Performance:
- Eric Cryptomans Journal: 2 signals, avg 2.551x
- Crypto Signals Pro: 2 signals, avg 2.200x
- Overall AVICI: 2.376x across 2 channels
- Best channel: Eric Cryptomans Journal
- Recommendation: "Follow Eric for AVICI calls"


=== MULTI-DIMENSIONAL PREDICTION ===
New message: "$AVICI breakout!"
Channel: Eric Cryptomans Journal

Prediction sources:
1. Overall channel: 1.601x (40% weight) = 0.640
2. Coin-specific (AVICI): 3.112x (50% weight) = 1.556
3. Cross-channel (AVICI): 2.376x (10% weight) = 0.238

Weighted prediction: 0.640 + 1.556 + 0.238 = 2.434x
Expected ROI: 2.434x (143% gain)

Breakdown shown to user:
- "Eric typically delivers 1.601x"
- "Eric calling AVICI typically delivers 3.112x"
- "AVICI across all channels typically delivers 2.376x"
- "Combined prediction: 2.434x (143% expected gain)"
```

**Requirements**: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6 (NEW), 8.7 (NEW), 8.8 (NEW), 8.9 (NEW), 8.10 (NEW)

---

## - [ ] 4. Refactor and enhance historical OHLC data fetching for ROI calculation

Refactor existing historical price fetching from `historical_scraper.py` into dedicated class with enhanced caching and fallback logic.

**ROI Focus**: Get historical prices to calculate what ROI each past signal achieved - essential for establishing baseline reputation.

**Current State**:

- `historical_scraper.py` already has `fetch_historical_price()` method using CryptoCompare
- HTTP session management via `_get_http_session()`
- Basic caching implemented

**Implementation Details**:

**Refactor Existing Code:**

- Extract `fetch_historical_price()` from `historical_scraper.py`
- Extract `_get_http_session()` and caching logic
- Create `services/pricing/historical_price_retriever.py` with HistoricalPriceRetriever class
- Keep existing CryptoCompare implementation (already works!)

**Enhance with New Features:**

- Add Twelve Data fallback (currently missing)
  - Endpoint: `/time_series?symbol=BTC/USD&interval=1day&outputsize=30`
  - Use when CryptoCompare fails or rate limited
- Implement daily OHLC fetching (not just price-at-timestamp)
  - CryptoCompare: `/data/v2/histoday?fsym=BTC&tsym=USD&limit=30`
  - Returns: 30 daily candles with open, high, low, close
- Enhance caching with persistent storage
  - Save to `data/cache/historical_prices.json`
  - Cache never expires (historical data immutable)
- Add batch fetching for multiple tokens
  - Reduce API calls by batching requests
  - Respect rate limits (CryptoCompare: 100K/month, Twelve Data: 800/day)

**Smart Checkpoint Backfilling:**

- Calculate elapsed time since message date
- Determine which checkpoints already reached
- Fetch historical prices only for reached checkpoints
- Example: Message 5 days old → fetch 1h, 4h, 24h, 3d checkpoints only
- Don't fetch 7d, 30d (not reached yet, will monitor live)

**Calculate Historical ROI:**

- Find ATH in fetched window: max(high prices)
- Calculate ROI: (ATH - entry_price) / entry_price
- Determine days to ATH: date difference
- Classify outcome: winner if ATH ≥ 2.0x
- Store all checkpoint ROIs (not just ATH)

**External Verification with fetch MCP**:

- Verify CryptoCompare API: https://min-api.cryptocompare.com/documentation
- Verify Twelve Data API: https://twelvedata.com/docs
- Verify caching best practices
- Verify batch processing patterns

**Files to Create**:

- `services/pricing/historical_price_retriever.py` (~350 lines)
- `data/cache/historical_prices.json` (created at runtime)

**Files to Modify**:

- `scripts/historical_scraper.py` (remove inline methods, use HistoricalPriceRetriever)

**Validation**:

**CryptoCompare Primary:**

- Fetch 30 days of OHLC from CryptoCompare for BTC
- Returns 30 daily candles with open, high, low, close
- Find ATH in 30-day window: max(high prices)
- Calculate historical ROI: (ATH - entry_price) / entry_price
- Determine days to ATH: date difference
- Test CryptoCompare OHLC → returns 30 candles ✓
- Test ATH detection → finds highest price in window ✓
- Test ROI calculation → correct from historical data ✓

**Twelve Data Fallback:**

- CryptoCompare fails or rate limited
- Automatically switch to Twelve Data
- Same data format returned
- Test fallback → uses Twelve Data when needed ✓
- Test seamless transition → no errors ✓

**Caching:**

- First fetch: Query API, save to cache
- Second fetch (same token/date): Load from cache, no API call
- Cache persists across restarts
- Test caching → no duplicate API calls ✓
- Test persistence → cache survives restart ✓

**Smart Checkpoint Backfilling:**

- Message 2 days old: Fetch 1h, 4h, 24h only
- Message 10 days old: Fetch 1h, 4h, 24h, 3d, 7d only
- Message 35 days old: Fetch all checkpoints (1h-30d)
- Test partial backfill → only fetches reached checkpoints ✓
- Test full backfill → fetches all when >30 days ✓

**Batch Processing:**

- Process 10 tokens at once
- Single API call per batch (where supported)
- Respect rate limits
- Test batch fetching → reduces API calls ✓
- Test rate limiting → respects limits ✓

**Historical Scraper Verification**:

Run `python scripts/historical_scraper.py` and verify:

1. ✓ HistoricalPriceRetriever initialized successfully
2. ✓ CryptoCompare API fetches historical OHLC data
3. ✓ Twelve Data fallback works when CryptoCompare fails
4. ✓ Historical prices cached to persistent storage
5. ✓ Cache loaded on restart (no duplicate API calls)
6. ✓ Smart checkpoint backfilling (only fetches reached checkpoints)
7. ✓ ATH identified from OHLC window
8. ✓ Historical ROI calculated correctly from past data
9. ✓ All checkpoint ROIs stored (not just ATH)
10. ✓ Batch processing reduces API calls
11. ✓ Rate limits respected
12. ✓ Logs show: "HistoricalPriceRetriever: Fetching OHLC for [symbol] from CryptoCompare"
13. ✓ Logs show: "30-day OHLC retrieved: X candles"
14. ✓ Logs show: "ATH found: $X.XX on [date] (day X)"
15. ✓ Logs show: "Historical ROI: X.XXx (XXX% gain)"
16. ✓ Logs show: "Cached: [symbol] at [date]"
17. ✓ Logs show: "Loaded from cache: [symbol] at [date]"
18. ✓ Logs show: "Fallback to Twelve Data" (when CryptoCompare fails)
19. ✓ Logs show: "Smart backfill: Fetching X checkpoints (Y days elapsed)"
20. ✓ Verify historical_prices.json created and populated

**Historical ROI Example**:

```
Message: "Bought $AVICI at $1.47" (Nov 10, 2025)
Today: Nov 12, 2025 (2 days elapsed)

Smart Checkpoint Backfilling:
- Elapsed: 2 days
- Reached checkpoints: 1h, 4h, 24h
- Not reached: 3d, 7d, 30d (will monitor live)

Fetch: 2 days of OHLC from Nov 10 to Nov 12 (not full 30 days!)
Find ATH: $4.78 on Nov 11 (day 1)
Calculate ROI at checkpoints:
- 1h: $1.52 → 1.034x
- 4h: $1.89 → 1.286x
- 24h: $4.78 → 3.252x (ATH)

Store: All 3 checkpoint ROIs
Status: "in_progress" (3d, 7d, 30d not reached yet)
Continue: Live monitoring for remaining checkpoints

Result: Efficient backfilling + live monitoring hybrid!
```

**Refactoring Benefits**:

- ✅ Reuses existing working code (don't reinvent wheel)
- ✅ Adds missing Twelve Data fallback
- ✅ Enhances caching with persistence
- ✅ Smart checkpoint backfilling (efficiency!)
- ✅ Batch processing support
- ✅ Cleaner separation of concerns
- ✅ Easier to test and maintain

**Requirements**: 14.1, 14.2, 14.3, 14.4, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6 (NEW), 16.7 (NEW), 17.1, 17.2, 17.3, 17.4, 17.5

---

## - [ ] 5. Refactor and enhance historical bootstrap with smart checkpoint handling

Refactor existing bootstrap logic from `historical_scraper.py` into dedicated class with enhanced progress tracking, resumability, and smart checkpoint backfilling.

**ROI Focus**: Establish baseline "What ROI can I expect?" answer by analyzing complete channel history with efficient partial checkpoint handling.

**Current State**:

- `historical_scraper.py` already has `process_messages()` method
- `backfill_historical_prices()` method exists
- Progress tracking via `stats` dictionary
- Batch processing implemented
- Task 4 completed: HistoricalPriceService with smart checkpoint calculation

**Implementation Details**:

**Refactor Existing Code:**

- Extract bootstrap logic from `historical_scraper.py`
- Create `services/reputation/historical_bootstrap.py` with HistoricalBootstrap class
- Keep existing batch processing (already works!)
- Keep existing message processing flow
- Reuse HistoricalPriceService from Task 4 (smart checkpoints already implemented)

**Enhance with New Features:**

**1. Smart Checkpoint Handling (Leverages Task 4):**

- For each historical message, calculate elapsed time to today
- Use `HistoricalPriceService.calculate_smart_checkpoints()` to determine reached checkpoints
- Use `HistoricalPriceService.fetch_forward_ohlc_with_ath()` for efficient OHLC fetching
- Examples:
  - Message 2 days old: Backfill 1h, 4h, 24h → Monitor 3d, 7d, 30d live
  - Message 10 days old: Backfill 1h-7d → Monitor 30d live
  - Message 35 days old: Backfill all → Mark "completed"
- Create SignalOutcome with appropriate status:
  - "completed" if all checkpoints reached (≥30 days old)
  - "in_progress" if some checkpoints pending (<30 days old)

**2. Two-File Tracking System (NEW!):**

- Create `data/reputation/active_tracking.json` for in-progress signals (<30 days)
- Create `data/reputation/completed_history.json` for finished signals (≥30 days)
- When signal completes (30d reached) → move from active to history atomically
- Enables fresh start re-monitoring (coin can be tracked again after completion)
- Each file maintains separate signal tracking with full metadata

**3. Deduplication Logic (NEW!):**

- Check if coin already in active_tracking.json
  - YES → Skip (duplicate mention while tracking)
  - NO → Check completed_history.json
    - Found → Start fresh tracking with new entry price (Signal #2, #3, etc.)
    - Not found → Start first tracking (Signal #1)
- Track `signal_number` for each coin (1st mention, 2nd mention, etc.)
- Store `previous_signals` reference list for context and learning
- Enable coin-specific TD learning from multiple mentions

**4. Progress Persistence (NEW!):**

- Save progress to `data/reputation/bootstrap_status.json`
- Track: total_messages, processed_messages, total_tokens, processed_tokens
- Track: successful_outcomes, failed_outcomes, api_calls_made
- Track: last_processed_message_id, last_processed_timestamp
- Enable resumability: If bootstrap crashes, resume from last checkpoint
- Save progress every 100 messages
- Clear progress file on successful completion

**5. Batch Processing Optimization:**

- Process messages in batches of 100
- Process multiple tokens in parallel (max 5 concurrent)
- Respect API rate limits (already in HistoricalPriceService)
- Cache historical prices (reuse across channels via HistoricalPriceCache)
- Use `fetch_batch_prices_at_timestamp()` for parallel fetching

**6. Initial Reputation Calculation:**

- Aggregate all completed historical outcomes per channel
- Calculate initial reputation from historical data:
  - Win rate from historical ROIs
  - Average ROI from historical outcomes
  - Sharpe ratio from historical volatility
  - Speed from historical days-to-ATH
- Initialize coin_specific_performance for each coin mentioned
- Save to channels.json before live monitoring starts

**7. MCP-Validated ROI Calculation:**

- Use Investopedia-validated ROI formula: `(current - initial) / initial * 100`
- Use multiplier format: `current / initial` for consistency
- Apply TD learning with alpha=0.1 (Wikipedia-validated learning rate)
- Track prediction errors with full metadata for learning

**External Verification with fetch MCP**:

- ✅ Verified ROI calculation formula (Investopedia): `(current - initial) / initial * 100`
- ✅ Verified TD learning formula (Wikipedia): `new = old + alpha * (actual - old)`
- ✅ Verified learning rate alpha=0.1 for gradual adaptation
- ✅ Verified batch processing patterns
- ✅ Verified progress tracking best practices
- ✅ Verified data aggregation patterns
- ✅ Verified resumability patterns

**Files to Create**:

- `services/reputation/historical_bootstrap.py` (~500 lines)
  - HistoricalBootstrap class with two-file tracking
  - Deduplication logic
  - Progress persistence
  - Fresh start re-monitoring support
- `data/reputation/active_tracking.json` (created at runtime)
  - In-progress signals (<30 days old)
  - Continues monitoring until completion
- `data/reputation/completed_history.json` (created at runtime)
  - Finished signals (≥30 days old)
  - Enables fresh start re-monitoring
- `data/reputation/bootstrap_status.json` (created at runtime)
  - Progress tracking for resumability
  - Cleared on successful completion

**Files to Modify**:

- `scripts/historical_scraper.py` (use HistoricalBootstrap class)
- `domain/signal_outcome.py` (add signal_number, previous_signals fields)
- `repositories/file_storage/outcome_repository.py` (add two-file support)

**Validation**:

**Smart Checkpoint Handling (Leverages Task 4):**

- Message 2 days old: Backfill 1h, 4h, 24h → Status "in_progress"
- Message 10 days old: Backfill 1h-7d → Status "in_progress"
- Message 35 days old: Backfill all → Status "completed"
- Test partial backfill → only fetches reached checkpoints ✓
- Test status determination → correct based on elapsed time ✓
- Test OHLC efficiency → uses forward window, not full 30 days ✓
- Test cache reuse → no duplicate API calls ✓

**Two-File Tracking System (NEW!):**

- In-progress signals → active_tracking.json
- Completed signals → completed_history.json
- Signal completes → moves from active to history atomically
- Test file separation → signals in correct file ✓
- Test archival → completed signals moved ✓
- Test atomic updates → no data loss during archival ✓
- Test file structure → both files have same schema ✓

**Deduplication Logic (NEW!):**

- First mention: Start tracking (Signal #1)
- Duplicate mention (while in active): Skip
- New mention after completion: Start fresh (Signal #2)
- Test deduplication → no duplicates in active ✓
- Test fresh start → new tracking after completion ✓
- Test signal numbering → increments correctly (1, 2, 3...) ✓
- Test previous_signals → references maintained ✓
- Test independent tracking → Signal #2 has new entry price ✓

**Progress Persistence (NEW!):**

- Bootstrap starts: Create bootstrap_status.json
- Every 100 messages: Save progress
- Bootstrap crashes: Resume from last checkpoint
- Bootstrap completes: Clear progress file
- Test persistence → progress saved every 100 messages ✓
- Test resumability → resumes from last_processed_message_id ✓
- Test crash recovery → no duplicate processing ✓
- Test completion cleanup → progress file cleared ✓

**Initial Reputation:**

- Process 100 historical messages from channel
- Extract 20 token mentions
- Calculate ROI for each: 12 winners (≥2x), 8 losers (<2x)
- Calculate initial reputation:
  - Win rate: 12/20 = 60%
  - Average ROI: 1.75x (75% average gain)
  - Sharpe: 0.82
  - Reputation score: 65/100 → "Good" tier
- Initialize coin_specific_performance for all 20 coins
- Test reputation calculation → 65/100 "Good" tier ✓
- Test coin-specific init → all coins tracked ✓

**MCP-Validated ROI Calculation:**

- Test ROI formula → matches Investopedia standard ✓
- Test multiplier format → consistent across system ✓
- Test TD learning → alpha=0.1 applied correctly ✓
- Test prediction errors → full metadata tracked ✓

**Historical Scraper Verification**:

Run `python scripts/historical_scraper.py` and verify:

**Smart Checkpoint Handling (Leverages Task 4):**

1. ✓ HistoricalBootstrap initialized successfully
2. ✓ HistoricalPriceService integrated and working
3. ✓ Elapsed time calculated for each message
4. ✓ `calculate_smart_checkpoints()` determines reached checkpoints
5. ✓ `fetch_forward_ohlc_with_ath()` fetches only needed data
6. ✓ Checkpoints backfilled based on elapsed time
7. ✓ Status set correctly ("in_progress" vs "completed")
8. ✓ Logs show: "Message X days old: Backfilling Y checkpoints, monitoring Z live"
9. ✓ Logs show: "OHLC data: X candles (Y% complete)"

**Two-File Tracking System (NEW!):**

10. ✓ active_tracking.json created with in-progress signals
11. ✓ completed_history.json created with finished signals
12. ✓ Signals move from active to history when completed
13. ✓ Atomic file updates (no data loss)
14. ✓ Both files maintain same schema
15. ✓ Logs show: "Signal completed: Moving to history"
16. ✓ Logs show: "Active signals: X, Completed signals: Y"

**Deduplication Logic (NEW!):**

17. ✓ First mention starts tracking (Signal #1)
18. ✓ Duplicate mentions skipped (already in active)
19. ✓ New mentions after completion start fresh tracking (Signal #2, #3)
20. ✓ Signal numbers increment correctly
21. ✓ previous_signals references maintained
22. ✓ Independent entry prices for each signal
23. ✓ Logs show: "Duplicate: [coin] already tracked, skipping"
24. ✓ Logs show: "[coin] previously tracked (Signal #1: X.XXx), starting Signal #2"
25. ✓ Logs show: "Fresh start: [coin] Signal #2 with entry price $X.XX"

**Progress Persistence (NEW!):**

26. ✓ bootstrap_status.json created on startup
27. ✓ Progress saved every 100 messages
28. ✓ Bootstrap resumable after crash
29. ✓ Progress file cleared on successful completion
30. ✓ last_processed_message_id tracked
31. ✓ last_processed_timestamp tracked
32. ✓ Logs show: "Progress: X/Y messages processed"
33. ✓ Logs show: "Checkpoint saved: X messages, Y tokens"
34. ✓ Logs show: "Resuming from message ID: X"
35. ✓ Logs show: "Bootstrap complete: Clearing progress file"

**Initial Reputation:**

36. ✓ Historical messages processed and outcomes calculated
37. ✓ Initial channel reputations established from complete history
38. ✓ Coin-specific performance initialized for each coin
39. ✓ Reputations saved to channels.json
40. ✓ Statistical significance achieved (100+ signals per channel)
41. ✓ Logs show: "Bootstrap: Processing [channel] history"
42. ✓ Logs show: "Processed X messages, found X token mentions"
43. ✓ Logs show: "Calculated X ROI outcomes (X winners, X losers)"
44. ✓ Logs show: "Initial reputation: XX.X/100 → [Tier]"
45. ✓ Logs show: "Coin-specific performance: X coins tracked"
46. ✓ Logs show: "Bootstrap complete: X channels initialized"

**File Verification:**

47. ✓ Verify channels.json contains initial reputations
48. ✓ Verify coin_specific_performance populated
49. ✓ Verify active_tracking.json contains in-progress signals
50. ✓ Verify completed_history.json contains finished signals
51. ✓ Verify bootstrap_status.json tracks progress (or cleared if complete)
52. ✓ Verify system ready for live monitoring with baseline data

**MCP-Validated Features:**

53. ✓ ROI calculation uses Investopedia formula
54. ✓ TD learning uses Wikipedia-validated alpha=0.1
55. ✓ Prediction errors tracked with full metadata
56. ✓ Fresh start re-monitoring enabled

**Bootstrap ROI Example**:

```
Channel: Eric Cryptomans Journal
Historical Period: Jan 2024 - Nov 2025 (2 years)
Today: Nov 12, 2025

Messages Processed: 5,234

Token Mentions: 487
├─ Completed (≥30 days old): 452
│  └─ Saved to completed_history.json
└─ In-Progress (<30 days old): 35
   └─ Saved to active_tracking.json (continue monitoring)

Smart Checkpoint Handling (Task 4 Integration):
- Message from Oct 1 (42 days old): Backfill ALL → "completed"
  - Uses fetch_forward_ohlc_with_ath() for efficient OHLC
  - Calculates ATH from 30-day window
- Message from Nov 5 (7 days old): Backfill 1h-7d → "in_progress"
  - Uses calculate_smart_checkpoints() to determine reached
  - Fetches only 7 days of data (not full 30!)
- Message from Nov 10 (2 days old): Backfill 1h-24h → "in_progress"
  - Fetches only 2 days of data
  - Will monitor 3d, 7d, 30d live

ROI Outcomes Calculated: 452 completed
- Winners (≥2x): 271 (60%)
- Average ROI: 1.85x (85% average gain)
- Best ROI: 12.5x (1,150% gain)
- Worst ROI: 0.15x (85% loss)
- Sharpe Ratio: 0.89

Coin-Specific Performance Initialized:
- AVICI: 2 mentions, avg 2.551x, expected 2.551x
  - Signal #1: 3.252x (completed)
  - Signal #2: 1.85x (completed)
- NKP: 1 mention, avg 0.932x, expected 0.932x
  - Signal #1: 0.932x (completed)
- PEAS: 2 mentions, avg 1.750x, expected 1.750x
  - Signal #1: 2.100x (completed)
  - Signal #2: 1.400x (completed)
- ... (487 total coins)

Initial Reputation: 78.5/100 → "Excellent" tier
Expected ROI (Overall): 1.85x (85% gain per signal)
TD Learning Initialized: alpha=0.1 (MCP-validated)

Files Created:
✓ channels.json (initial reputations with TD learning)
✓ active_tracking.json (35 in-progress signals)
✓ completed_history.json (452 finished signals)
✓ bootstrap_status.json (cleared after completion)

Ready for live monitoring with:
- Established baseline reputation
- 35 signals continuing to track
- Fresh start re-monitoring enabled
- Coin-specific TD learning initialized
```

**Fresh Start Re-Monitoring Example**:

```
=== AVICI Signal History ===

Signal #1 (Oct 1, 2025):
- Entry: $1.47
- ATH: $4.78 (3.252x) on day 1
- Status: completed (moved to completed_history.json)
- Outcome: WINNER

Signal #2 (Nov 5, 2025):
- Check active_tracking.json: Not found
- Check completed_history.json: Found (Signal #1: 3.252x)
- Start fresh tracking with new entry price
- Entry: $2.10 (different from Signal #1!)
- ATH: $3.89 (1.85x) on day 5
- Status: completed (moved to completed_history.json)
- Outcome: LOSER (< 2x threshold)
- Previous signals: [Signal #1: 3.252x]

Signal #3 (Nov 20, 2025):
- Check active_tracking.json: Not found
- Check completed_history.json: Found (Signal #1: 3.252x, Signal #2: 1.85x)
- Start fresh tracking with new entry price
- Entry: $1.80 (different from both previous!)
- Status: in_progress (currently tracking)
- Previous signals: [Signal #1: 3.252x, Signal #2: 1.85x]

Coin-Specific TD Learning:
- Initial expected ROI: 3.252x (from Signal #1)
- After Signal #2: 3.252 + 0.1 * (1.85 - 3.252) = 3.112x
- Prediction for Signal #3: 3.112x
- System learns: AVICI performance varies by entry timing!
```

**Key Enhancements Summary**:

**Leverages Task 4 Completion:**

- ✅ Reuses HistoricalPriceService (smart checkpoints already implemented)
- ✅ Reuses fetch_forward_ohlc_with_ath() (efficient OHLC fetching)
- ✅ Reuses calculate_smart_checkpoints() (elapsed time calculation)
- ✅ Reuses HistoricalPriceCache (no duplicate API calls)

**New Features Added:**

- ✅ Two-file tracking system (active vs completed)
- ✅ Deduplication logic (prevents duplicate tracking)
- ✅ Fresh start re-monitoring (Signal #1, #2, #3...)
- ✅ Progress persistence (resumability after crash)
- ✅ Signal numbering (tracks multiple mentions)
- ✅ Previous signals references (learning context)

**MCP-Validated Enhancements:**

- ✅ ROI formula validated by Investopedia
- ✅ TD learning formula validated by Wikipedia
- ✅ Learning rate alpha=0.1 (gradual adaptation)
- ✅ Prediction error tracking with full metadata

**Refactoring Benefits**:

- ✅ Reuses existing working code (no reinvention)
- ✅ Smart checkpoint handling (efficiency!)
- ✅ Two-file system enables fresh start re-monitoring
- ✅ Deduplication prevents duplicate tracking
- ✅ Progress persistence enables resumability
- ✅ Coin-specific performance initialized
- ✅ Cleaner separation of concerns
- ✅ Easier to test and maintain
- ✅ Atomic file updates (no data loss)
- ✅ Independent signal tracking (multiple ROI measurements)

**Requirements**: 14.5, 14.6, 14.7, 14.8, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6 (NEW), 15.7 (NEW), 17.6, 17.7, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6

---

## - [ ] 6. Integrate multi-dimensional ROI-based reputation into live monitoring pipeline with event-driven architecture

Integrate enhanced reputation system with existing components using event-driven architecture (observer pattern) for real-time multi-dimensional ROI predictions, with fresh start re-monitoring and comprehensive output.

**ROI Focus**: Use multi-dimensional "Expected ROI" (overall + coin-specific + cross-channel) to adjust confidence for new signals and continue learning from live outcomes.

**MCP-Validated Enhancements**:

- ✅ Event-driven architecture (Wikipedia) - Decoupled components with event notifications
- ✅ Observer pattern (Wikipedia) - Subject-observer relationship for signal completion events
- ✅ Callback pattern (Wikipedia) - Asynchronous notification when signals complete
- ✅ Sharpe ratio (Investopedia) - Risk-adjusted returns for reputation scoring
- ✅ Reinforcement learning (Wikipedia) - Continuous learning from outcomes

**Implementation Details**:

**1. Event-Driven Signal Completion Architecture (NEW!):**

- Create `domain/events.py` with event classes:
  - `SignalCompletedEvent` - Emitted when signal reaches 30d or stop condition
  - `CheckpointReachedEvent` - Emitted when checkpoint (1h, 4h, 24h, etc.) reached
  - `ReputationUpdatedEvent` - Emitted when reputation changes significantly (>5 points)
- Create `infrastructure/event_bus.py` with EventBus class:
  - `subscribe(event_type, callback)` - Register observers for events
  - `publish(event)` - Notify all observers of event
  - `unsubscribe(event_type, callback)` - Remove observer
- Implement observer pattern for decoupled components:
  - OutcomeTracker publishes SignalCompletedEvent
  - ReputationEngine subscribes to SignalCompletedEvent
  - DataOutput subscribes to ReputationUpdatedEvent
  - MessageProcessor subscribes to CheckpointReachedEvent

**2. Enhanced TD Learning Integration with Event Callbacks:**

- Modify `ReputationEngine.update_reputation()` to be event-driven callback
- When SignalCompletedEvent received:
  - Extract signal outcome from event payload
  - Call `apply_td_learning()` for overall channel learning
  - Call `apply_coin_specific_td_learning()` for coin-specific learning
  - Call `update_cross_channel_coin_performance()` for cross-channel tracking
  - Publish ReputationUpdatedEvent if score changes >5 points
- Check if signal is in active_tracking.json
  - YES → Archive to completed_history.json atomically (Task 5 pattern)
  - Update both files using atomic write pattern
- Enable fresh start re-monitoring (coin available for tracking again)

**3. Enhanced MessageProcessor Integration with Prediction Caching:**

- Modify `MessageProcessor.process_message()` to lookup reputation with caching
- Implement prediction cache (TTL: 5 minutes) to reduce reputation lookups
- Get multi-dimensional prediction with fallback logic:
  - Overall channel expected_roi (40% weight) - Always available
  - Coin-specific expected_roi (50% weight) - If coin previously tracked by this channel
  - Cross-channel expected_roi (10% weight) - If coin tracked by any channel
  - Fallback: Use overall only if coin-specific unavailable
- Calculate weighted prediction with confidence intervals:
  - Prediction = weighted average of available sources
  - Confidence interval = ±(std_dev × 1.96) for 95% confidence
  - Prediction accuracy = % of past predictions within confidence interval
- Adjust confidence based on reputation tier (MCP-validated Sharpe ratio approach):
  - Elite (90-100): +25% confidence boost, Sharpe >1.5
  - Excellent (75-90): +20% confidence boost, Sharpe 1.0-1.5
  - Good (60-75): +10% confidence boost, Sharpe 0.5-1.0
  - Average (40-60): No adjustment, Sharpe 0.0-0.5
  - Poor (20-40): -10% confidence reduction, Sharpe <0.0
  - Unreliable (0-20): -20% confidence reduction, Sharpe <<0.0
- Log prediction breakdown with transparency:
  - "Prediction: Overall 1.85x (40%), AVICI 3.112x (50%), Cross-channel 2.376x (10%) = 2.464x ±0.35 (95% CI)"
  - "Confidence adjusted: 0.65 → 0.78 (Excellent tier, Sharpe=1.2)"

**4. Fresh Start Re-Monitoring with Deduplication (Task 5 Integration):**

- When new message arrives with coin mention:
  - Use HistoricalBootstrap.check_for_duplicate() method (Task 5)
  - Check active_tracking.json first
    - Found → Skip (duplicate, already tracking)
    - Log: "Duplicate: {coin} already tracked, skipping"
  - Check completed_history.json
    - Found → Start fresh tracking (Signal #2, #3, etc.)
    - Log: "{coin} previously tracked (Signal #{prev_num}: {prev_roi}x), starting Signal #{new_num}"
    - Not found → Start first tracking (Signal #1)
    - Log: "First mention: {coin} Signal #1 with entry price ${price}"
- Create new SignalOutcome with:
  - New entry_price (current market price from API)
  - New signal_id (UUID for unique identification)
  - signal_number (1, 2, 3, etc.) - From check_for_duplicate()
  - previous_signals reference (list of previous signal IDs for learning context)
  - status = "in_progress" (will track for 30 days)
- Track independently from previous signals (fresh entry price, fresh tracking window)
- Publish SignalStartedEvent for observers (e.g., logging, monitoring)

**5. Enhanced DataOutput with Event-Driven Updates:**

- Subscribe to ReputationUpdatedEvent for real-time output updates
- Add reputation columns to MESSAGES table:
  - channel_reputation_score (0-100)
  - channel_reputation_tier (Elite/Excellent/Good/Average/Poor/Unreliable)
  - channel_expected_roi (overall prediction)
  - channel_coin_expected_roi (coin-specific prediction, if available)
  - channel_win_rate (% of signals ≥2x)
  - channel_sharpe_ratio (risk-adjusted returns, MCP-validated)
  - prediction_source (overall/coin-specific/multi-dimensional)
  - prediction_confidence_interval (±X.XX for 95% CI)
- Create CHANNEL_RANKINGS table (replaces CHANNEL_REPUTATION):
  - channel_name, total_signals, win_rate
  - avg_roi, median_roi, best_roi, worst_roi
  - expected_roi (overall TD learning prediction), sharpe_ratio, speed_score
  - reputation_score, reputation_tier
  - total_predictions, prediction_accuracy (% within CI), mean_absolute_error
  - mean_squared_error, confidence_interval_width
  - first_signal_date, last_signal_date, last_updated
  - Sort by reputation_score descending (best channels first)
  - Add rank column (1, 2, 3, ...) for easy comparison
- Create CHANNEL_COIN_PERFORMANCE table (NEW!):
  - channel_name, coin_symbol, mentions
  - avg_roi, expected_roi (coin-specific TD learning), win_rate
  - best_roi, worst_roi, prediction_accuracy
  - sharpe_ratio (coin-specific risk-adjusted returns)
  - last_mentioned, days_since_last_mention
  - recommendation (Strong Buy/Buy/Hold/Avoid based on expected_roi)
  - Sort by avg_roi descending within each channel
- Create COIN_CROSS_CHANNEL table (NEW!):
  - coin_symbol, total_mentions, total_channels
  - avg_roi_all_channels, median_roi_all_channels
  - best_channel, best_channel_roi, best_channel_mentions
  - worst_channel, worst_channel_roi, worst_channel_mentions
  - consensus_strength (0-100, based on channel agreement)
  - recommendation (Strong consensus/Weak consensus/Conflicting signals)
  - Sort by avg_roi_all_channels descending
- Create PREDICTION_ACCURACY table (NEW!):
  - channel_name, total_predictions, correct_predictions (within CI)
  - accuracy_percentage, mean_absolute_error, mean_squared_error
  - overestimations, underestimations, avg_error_magnitude
  - Sort by accuracy_percentage descending
- Add conditional formatting in Google Sheets (MCP-validated color psychology):
  - Green: reputation_score > 75, expected_roi > 2.0, sharpe_ratio > 1.0
  - Yellow: reputation_score 40-75, expected_roi 1.5-2.0, sharpe_ratio 0.5-1.0
  - Red: reputation_score < 40, expected_roi < 1.5, sharpe_ratio < 0.5
  - Bold: Elite tier channels
  - Italic: Unproven channels (<10 signals)

**6. Event-Driven Live Monitoring Continuation:**

- Load active_tracking.json on startup using HistoricalBootstrap (Task 5)
- Subscribe to CheckpointReachedEvent for checkpoint monitoring
- Continue monitoring in-progress signals with event-driven architecture
- When checkpoint time arrives (1h, 4h, 24h, 3d, 7d, 30d):
  - Publish CheckpointReachedEvent with signal_id and checkpoint_name
  - OutcomeTracker receives event and fetches current price
  - Calculate ROI: (current_price - entry_price) / entry_price
  - Update checkpoint data in SignalOutcome
  - Save to active_tracking.json atomically (Task 5 pattern)
  - Publish CheckpointUpdatedEvent for observers
- When 30d checkpoint reached OR stop condition met:
  - Mark signal as complete
  - Publish SignalCompletedEvent with full outcome data
  - ReputationEngine receives event and applies TD learning (all 3 levels):
    - Overall channel: new_expected = old_expected + 0.1 × (actual - old_expected)
    - Coin-specific: new_coin_expected = old_coin_expected + 0.1 × (actual - old_coin_expected)
    - Cross-channel: Update aggregated coin performance across all channels
  - Archive to completed_history.json atomically (Task 5 pattern)
  - Remove from active_tracking.json atomically
  - Publish ReputationUpdatedEvent if score changes >5 points
- Implement graceful shutdown:
  - Save all in-progress signals to active_tracking.json
  - Persist event subscriptions for restart
  - Log shutdown summary: X signals in progress, Y signals completed today

**External Verification with fetch MCP**:

- ✅ Event-driven architecture (Wikipedia) - Verified pattern for decoupled components
- ✅ Observer pattern (Wikipedia) - Verified subject-observer relationship
- ✅ Callback pattern (Wikipedia) - Verified asynchronous notification pattern
- ✅ Sharpe ratio (Investopedia) - Verified risk-adjusted returns formula
- ✅ Reinforcement learning (Wikipedia) - Verified continuous learning approach
- ✅ ROI calculation (Investopedia) - Previously verified in Task 1
- ✅ TD learning (Wikipedia) - Previously verified in Task 3

**Files to Create**:

- `domain/events.py` (~150 lines) - Event classes for event-driven architecture
- `infrastructure/event_bus.py` (~200 lines) - EventBus for publish-subscribe pattern
- `utils/prediction_cache.py` (~100 lines) - Prediction caching with TTL

**Files to Modify**:

- `services/reputation/reputation_engine.py` (add event-driven TD learning callbacks)
- `services/message_processing/message_processor.py` (add reputation lookup with caching and multi-dimensional prediction)
- `infrastructure/output/data_output.py` (add 4 new tables + enhanced reputation columns, subscribe to ReputationUpdatedEvent)
- `services/tracking/outcome_tracker.py` (add event publishing, archival logic with Task 5 integration)
- `services/reputation/historical_bootstrap.py` (integrate with event bus for startup)

**Pipeline Verification Steps**:

**After Bootstrap:**

1. Run system after historical bootstrap complete
2. Verify EventBus initialized with all subscriptions
3. Verify active_tracking.json loaded (35 in-progress signals) via HistoricalBootstrap
4. Verify completed_history.json loaded (452 finished signals) via HistoricalBootstrap
5. Verify logs show: "EventBus: Registered X observers for Y event types"
6. Verify logs show: "Loaded X active signals, Y completed signals"
7. Verify logs show: "Loaded reputation for [channel]: score=78.5, expected_roi=1.85x, sharpe=0.89"
8. Verify prediction cache initialized (TTL: 5 minutes)

**New Message Processing (Event-Driven):**

9. New message arrives: "$AVICI breakout!"
10. MessageProcessor publishes MessageReceivedEvent
11. Check active_tracking.json: AVICI not found (completed previously)
12. Check completed_history.json: AVICI found (Signal #1: 3.252x)
13. Start fresh tracking: Signal #2 with new entry price
14. Publish SignalStartedEvent with signal details
15. Get multi-dimensional prediction with caching:
    - Cache miss → Calculate prediction
    - Overall: 1.85x (40%) = 0.740
    - Coin-specific (AVICI): 3.112x (50%) = 1.556
    - Cross-channel (AVICI): 2.376x (10%) = 0.238
    - Weighted: 2.534x ±0.35 (95% CI)
    - Cache result for 5 minutes
16. Adjust confidence: 0.65 → 0.78 (excellent tier +20%, Sharpe=1.2)
17. Verify logs show: "Multi-dimensional prediction: Overall 1.85x (40%), AVICI 3.112x (50%), Cross-channel 2.376x (10%) = 2.534x ±0.35 (95% CI)"
18. Verify logs show: "Confidence adjusted: 0.65 → 0.78 (Excellent tier, Sharpe=1.2)"
19. Verify logs show: "Starting Signal #2 for AVICI (previous: Signal #1: 3.252x)"
20. Verify logs show: "Event published: SignalStartedEvent for AVICI Signal #2"

**Checkpoint Monitoring (Event-Driven):**

21. 1h checkpoint arrives
22. Publish CheckpointReachedEvent(signal_id, "1h")
23. OutcomeTracker receives event, fetches price, calculates ROI
24. Publish CheckpointUpdatedEvent with ROI data
25. Verify logs show: "Checkpoint 1h reached: AVICI ROI=1.034x"
26. Verify logs show: "Event published: CheckpointUpdatedEvent for AVICI 1h"
27. Repeat for 4h, 24h, 3d, 7d checkpoints

**Signal Completion (Event-Driven):**

28. 30d checkpoint reached OR stop condition met
29. Actual ROI: 2.15x
30. Publish SignalCompletedEvent with full outcome data
31. ReputationEngine receives event via callback
32. Apply TD learning (all 3 levels):
    - Overall: 1.85 + (0.1 × 0.30) = 1.88x
    - Coin-specific (AVICI): 3.112 + (0.1 × -0.962) = 3.016x
    - Cross-channel (AVICI): Update with new data point
33. Reputation score changes: 78.5 → 79.2 (+0.7, <5 threshold, no event)
34. Archive to completed_history.json atomically (Task 5 pattern)
35. Remove from active_tracking.json atomically
36. Verify logs show: "Event received: SignalCompletedEvent for AVICI Signal #2"
37. Verify logs show: "Signal complete: actual ROI=2.15x"
38. Verify logs show: "TD Learning (Overall): 1.85x → 1.88x (error: +0.30x)"
39. Verify logs show: "TD Learning (Coin-Specific): AVICI 3.112x → 3.016x (error: -0.962x)"
40. Verify logs show: "Cross-Channel Update: AVICI avg 2.363x across 2 channels"
41. Verify logs show: "Archived to history: AVICI Signal #2 (atomic write)"
42. Verify logs show: "Reputation updated: 78.5 → 79.2 (no event, <5 threshold)"

**Output Verification (Event-Driven):**

43. DataOutput subscribed to ReputationUpdatedEvent (no event this time)
44. Verify MESSAGES table includes:
    - channel_reputation_score=79.2
    - channel_expected_roi=1.88
    - channel_coin_expected_roi=3.016 (AVICI)
    - channel_sharpe_ratio=0.89
    - prediction_source="multi-dimensional"
    - prediction_confidence_interval="±0.35"
45. Verify CHANNEL_RANKINGS table:
    - Sorted by reputation_score descending
    - Rank column: 1, 2, 3, ...
    - Shows: win_rate=60%, avg_roi=1.85x, expected_roi=1.88x, sharpe_ratio=0.89
    - Shows: prediction_accuracy=63.9%, mean_absolute_error=0.423x, MSE=0.289
46. Verify CHANNEL_COIN_PERFORMANCE table:
    - Eric → AVICI: 2 mentions, avg 2.701x, expected 3.016x, sharpe=1.15
    - Eric → NKP: 1 mention, avg 0.932x, expected 0.932x, sharpe=-0.25
    - Sorted by avg_roi descending within channel
    - Recommendation: "Strong Buy" for AVICI, "Avoid" for NKP
47. Verify COIN_CROSS_CHANNEL table:
    - AVICI: 2 channels, avg 2.363x, median 2.300x
    - Best: Eric (2.701x, 2 mentions), Worst: Other (2.025x, 1 mention)
    - Consensus strength: 85/100 (strong agreement)
    - Sorted by avg_roi_all_channels descending
48. Verify PREDICTION_ACCURACY table:
    - Eric: 487 predictions, 311 correct (63.9%), MAE=0.423x, MSE=0.289
    - Sorted by accuracy_percentage descending
49. Verify Google Sheets conditional formatting:
    - Green: Eric (79.2 score, 1.88x expected, sharpe=0.89)
    - Bold: Elite tier channels
    - Yellow/Red: Other channels based on scores
50. Verify all tables update after each signal completion

**Next Signal (Fresh Start Re-Monitoring):**

51. New message from Eric: "$AVICI dip buy!"
52. Check active_tracking.json: AVICI not found
53. Check completed_history.json: AVICI found (2 previous signals)
54. Start fresh tracking: Signal #3 with new entry price $1.80
55. Get prediction from cache (if within 5 min) or calculate: 3.016x
56. Publish SignalStartedEvent
57. Verify logs show: "Starting Signal #3 for AVICI (previous: Signal #1: 3.252x, Signal #2: 2.15x)"
58. Verify logs show: "Event published: SignalStartedEvent for AVICI Signal #3"
59. Verify fresh start re-monitoring works correctly with independent tracking

**Event Bus Verification:**

60. Verify EventBus has active subscriptions:
    - SignalCompletedEvent → ReputationEngine.on_signal_completed
    - CheckpointReachedEvent → OutcomeTracker.on_checkpoint_reached
    - ReputationUpdatedEvent → DataOutput.on_reputation_updated
    - SignalStartedEvent → Logger.on_signal_started
61. Verify event publishing works asynchronously (non-blocking)
62. Verify observers receive events in correct order
63. Verify graceful shutdown saves all subscriptions

**Historical Scraper Verification**:

Run `python scripts/historical_scraper.py` and verify:

**Integration:**

1. ✓ MessageProcessor uses multi-dimensional reputation for confidence
2. ✓ Multi-dimensional prediction calculated (3 sources weighted)
3. ✓ Confidence adjusted based on reputation tier
4. ✓ Fresh start re-monitoring works (new tracking after completion)
5. ✓ Signal numbering increments correctly (Signal #1, #2, #3)
6. ✓ TD learning applied at all 3 levels after completion
7. ✓ Archival works (active → history)
8. ✓ Deduplication works (skips duplicates in active)

**Output Tables:** 9. ✓ MESSAGES table includes all reputation columns 10. ✓ CHANNEL_RANKINGS table created and sorted correctly 11. ✓ CHANNEL_COIN_PERFORMANCE table created with coin-specific data 12. ✓ COIN_CROSS_CHANNEL table created with cross-channel data 13. ✓ Google Sheets conditional formatting applied 14. ✓ All tables update after each signal completion

**Logs:** 15. ✓ Logs show: "Multi-dimensional prediction: Overall X.XXx, Coin-Specific X.XXx, Cross-Channel X.XXx = X.XXx" 16. ✓ Logs show: "Confidence adjusted: X.XX → X.XX (reputation tier: [tier])" 17. ✓ Logs show: "Starting Signal #X for [coin] (previous: [rois])" 18. ✓ Logs show: "TD Learning (Overall): X.XXx → X.XXx (error: +X.XXx)" 19. ✓ Logs show: "TD Learning (Coin-Specific): [coin] X.XXx → X.XXx (error: +X.XXx)" 20. ✓ Logs show: "Cross-Channel Update: [coin] avg X.XXx across X channels" 21. ✓ Logs show: "Archived to history: [coin] Signal #X"

**Files:** 22. ✓ Verify MESSAGES.csv contains reputation columns 23. ✓ Verify CHANNEL_RANKINGS.csv sorted by reputation_score descending 24. ✓ Verify CHANNEL_COIN_PERFORMANCE.csv shows coin-specific performance 25. ✓ Verify COIN_CROSS_CHANNEL.csv shows cross-channel data 26. ✓ Verify active_tracking.json updates correctly 27. ✓ Verify completed_history.json archives correctly 28. ✓ Verify Google Sheets formatting applied correctly

**End-to-End Flow:** 29. ✓ Complete pipeline: bootstrap → load → predict → track → complete → learn → archive → output 30. ✓ Fresh start re-monitoring: complete → new mention → fresh tracking 31. ✓ Multi-dimensional learning: all 3 levels update independently 32. ✓ System continuously improves predictions at all levels

**Success Criteria**:

- ✅ Historical bootstrap establishes baseline reputation (overall + coin-specific)
- ✅ Event-driven architecture decouples components (observer pattern)
- ✅ Live monitoring uses multi-dimensional prediction (3 sources weighted)
- ✅ Prediction caching reduces reputation lookups (5-minute TTL)
- ✅ Confidence intervals provide prediction uncertainty (±X.XX for 95% CI)
- ✅ TD learning updates at all 3 levels after each signal
- ✅ Fresh start re-monitoring works (coins can be tracked multiple times)
- ✅ Deduplication prevents duplicate tracking (Task 5 integration)
- ✅ Archival system works atomically (active → history, Task 5 pattern)
- ✅ Output shows comprehensive metrics (4 new tables including PREDICTION_ACCURACY)
- ✅ Sharpe ratio provides risk-adjusted returns (MCP-validated)
- ✅ Event bus enables asynchronous notifications (non-blocking)
- ✅ System answers: "What ROI can I expect from this channel calling this coin?"

**Key Enhancements Over Original Task 6**:

**Event-Driven Architecture (NEW!):**

- ✅ EventBus with publish-subscribe pattern (Wikipedia-validated)
- ✅ Observer pattern for decoupled components
- ✅ Asynchronous event notifications (non-blocking)
- ✅ Event types: SignalCompletedEvent, CheckpointReachedEvent, ReputationUpdatedEvent, SignalStartedEvent
- ✅ Graceful shutdown with subscription persistence

**Enhanced Prediction System (NEW!):**

- ✅ Prediction caching with 5-minute TTL (reduces lookups)
- ✅ Confidence intervals (±X.XX for 95% CI) for prediction uncertainty
- ✅ Prediction accuracy tracking (% within confidence interval)
- ✅ Fallback logic when coin-specific data unavailable
- ✅ Transparent logging of prediction breakdown

**Risk-Adjusted Metrics (NEW!):**

- ✅ Sharpe ratio for risk-adjusted returns (Investopedia-validated)
- ✅ Sharpe-based confidence adjustments (Elite: >1.5, Excellent: 1.0-1.5, etc.)
- ✅ Coin-specific Sharpe ratios in CHANNEL_COIN_PERFORMANCE table
- ✅ Mean squared error (MSE) in addition to MAE

**Enhanced Output Tables (NEW!):**

- ✅ PREDICTION_ACCURACY table (tracks prediction performance)
- ✅ Rank column in CHANNEL_RANKINGS (1, 2, 3, ...)
- ✅ Consensus strength in COIN_CROSS_CHANNEL (0-100 scale)
- ✅ Recommendation column (Strong Buy/Buy/Hold/Avoid)
- ✅ Enhanced conditional formatting (bold for Elite, italic for Unproven)

**Task 5 Integration:**

- ✅ Reuses HistoricalBootstrap.check_for_duplicate() for deduplication
- ✅ Reuses atomic write pattern for archival (no data loss)
- ✅ Reuses two-file tracking system (active vs completed)
- ✅ Reuses signal numbering (Signal #1, #2, #3, ...)

**MCP Validation:**

- ✅ Event-driven architecture (Wikipedia)
- ✅ Observer pattern (Wikipedia)
- ✅ Callback pattern (Wikipedia)
- ✅ Sharpe ratio (Investopedia)
- ✅ Reinforcement learning (Wikipedia)
- ✅ ROI calculation (Investopedia) - Task 1
- ✅ TD learning (Wikipedia) - Task 3

**ROI Integration Example**:

```
Bootstrap Complete:
- Channel: Eric Cryptomans Journal
- Historical Win Rate: 60%
- Historical Avg ROI: 1.85x
- Expected ROI (Overall): 1.85x
- AVICI Specific: 2 signals, avg 2.551x, expected 2.551x
- Reputation: 78.5/100 "Excellent"

Live Message Arrives: "$AVICI breakout!"
- Check active: Not found (completed previously)
- Check history: Found (Signal #1: 3.252x, Signal #2: 1.85x)
- Start fresh: Signal #3 with new entry price $2.50

Multi-Dimensional Prediction:
- Overall channel: 1.85x (40% weight) = 0.740
- Coin-specific (AVICI): 2.551x (50% weight) = 1.276
- Cross-channel (AVICI): 2.376x (10% weight) = 0.238
- Weighted prediction: 2.254x (125% expected gain)

Confidence Adjustment:
- Base confidence: 0.65
- Reputation boost: +20% (excellent tier)
- Adjusted confidence: 0.78

Signal Completes (30 days later):
- Actual ROI: 1.95x (95% gain)
- Errors:
  - Overall: 1.95 - 1.85 = +0.10x
  - Coin-specific: 1.95 - 2.551 = -0.601x
  - Cross-channel: 1.95 - 2.376 = -0.426x

TD Learning Updates:
- Overall: 1.85 + (0.1 × 0.10) = 1.86x
- Coin-specific (AVICI): 2.551 + (0.1 × -0.601) = 2.491x
- Cross-channel (AVICI): Updated with new data point

Archive:
- Move Signal #3 to completed_history.json
- Remove from active_tracking.json
- AVICI now available for Signal #4

Output:
- CHANNEL_RANKINGS: Eric 78.5/100, expected 1.86x
- CHANNEL_COIN_PERFORMANCE: Eric → AVICI 3 signals, avg 2.399x, expected 2.491x
- COIN_CROSS_CHANNEL: AVICI 2 channels, avg 2.300x, best: Eric

Next Signal: "$AVICI dip buy at $1.80!"
- Start Signal #4 with fresh tracking
- Prediction: 2.491x (learned from 3 previous signals)
- System continuously improves!
```

**Requirements**: 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6 (NEW), 11.7 (NEW), 11.8 (NEW), 12.1, 12.2, 12.3, 12.4, 12.5, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8

---

## Implementation Notes

### ROI-Centric Design Philosophy

Every component must answer: **"What ROI can I expect from this channel?"**

- **OutcomeTracker**: Calculates actual ROI achieved
- **ReputationEngine**: Aggregates ROI into channel metrics
- **TD Learning**: Predicts future ROI from past ROI
- **Historical Bootstrap**: Establishes baseline ROI expectations
- **Live Integration**: Uses ROI predictions for confidence

### API Priority for Historical ROI Calculation

**Primary: CryptoCompare (FREE)**

- 100,000 calls/month (3,333/day)
- Daily OHLC: `/data/v2/histoday`
- Price at timestamp: `/data/pricehistorical`
- Perfect for historical ROI calculation

**Fallback: Twelve Data**

- 800 calls/day
- Daily OHLC: `/time_series`
- Use when CryptoCompare fails

### ROI Calculation Formula (Validated by Investopedia)

```python
# ROI Percentage
roi_percentage = ((current_price - entry_price) / entry_price) * 100

# ROI Multiplier
roi_multiplier = current_price / entry_price

# Example:
# Entry: $1.47, ATH: $4.78
# ROI% = (($4.78 - $1.47) / $1.47) * 100 = 225.2%
# Multiplier = $4.78 / $1.47 = 3.252x
```

### Reputation Score Formula (ROI-Based)

```python
reputation_score = (
    win_rate * 30 +           # % of signals ≥2x ROI
    (avg_roi - 1.0) * 100 * 25 +  # Average ROI gain
    sharpe_ratio * 10 * 20 +      # Risk-adjusted ROI
    speed_score * 15 +            # Days to ATH
    confidence_score * 10         # Signal quality
)
```

### TD Learning Formula (ROI Prediction)

```python
# Update expected ROI after each signal
new_expected_roi = old_expected_roi + alpha * (actual_roi - old_expected_roi)

# Example:
# Old: 1.50x, Actual: 3.252x, Alpha: 0.1
# New = 1.50 + 0.1 * (3.252 - 1.50) = 1.675x
```

### File Structure After Completion

```
crypto-intelligence/
├── intelligence/
│   ├── outcome_tracker.py             # NEW: ROI calculation & tracking
│   ├── channel_reputation.py          # NEW: ROI-based reputation
│   ├── historical_price_retriever.py  # NEW: Historical OHLC for ROI
│   ├── historical_bootstrap.py        # NEW: Historical ROI analysis
│   └── market_analyzer.py             # EXISTING
├── core/
│   ├── performance_tracker.py         # MODIFIED: Emit ROI events
│   ├── message_processor.py           # MODIFIED: Use expected ROI
│   └── data_output.py                 # MODIFIED: Output ROI metrics + CHANNEL_RANKINGS
├── data/
│   └── reputation/                    # NEW
│       ├── channels.json              # ROI-based reputations
│       ├── signal_outcomes.json       # Individual ROI outcomes
│       └── bootstrap_status.json      # Bootstrap progress
├── output/
│   └── YYYY-MM-DD/
│       ├── messages.csv               # MODIFIED: Add reputation columns
│       ├── channel_rankings.csv       # NEW: Channel reputation rankings
│       └── (other tables)
```

### CHANNEL_RANKINGS Table Schema

```
channel_name          | Eric Cryptomans Journal
total_signals         | 487
win_rate              | 60.0%
avg_roi               | 1.85x
expected_roi          | 1.88x (TD learning prediction)
sharpe_ratio          | 0.89
speed_score           | 78.5
reputation_score      | 78.5
reputation_tier       | Excellent
first_signal_date     | 2024-01-15
last_signal_date      | 2025-11-10
last_updated          | 2025-11-11 18:45:00
```

**Sorted by reputation_score descending** - Best channels appear first!

### Success Metrics

- Historical bootstrap calculates ROI for 90%+ of past signals
- Initial reputation scores based on 100+ historical ROI outcomes
- Live monitoring updates expected ROI after each signal
- TD learning reduces prediction error over time
- Output clearly shows: win rate, avg ROI, expected ROI
- System answers: "What ROI can I expect?" for every channel

### Testing Approach

Each task tests ROI calculation accuracy:

1. **Unit**: Test ROI formula with known inputs/outputs
2. **Integration**: Test ROI flows through components
3. **Pipeline**: Test complete ROI tracking from entry to reputation update

### Performance Targets

- ROI calculation: <1ms per checkpoint
- Historical ROI fetch: <2 seconds per token (30 days)
- Reputation calculation: <100ms per channel
- Bootstrap: ~1 second per historical message
- Memory: <100MB for 1000 ROI outcomes
