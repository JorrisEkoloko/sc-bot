# Implementation Plan - Time-Based Performance Classification System

## Task Overview

This implementation plan adds time-based performance classification in 5 focused tasks. Each task delivers working functionality that integrates into the existing pipeline, transforming single-point classification into dual-checkpoint analysis (Day 7 + Day 30) with trajectory insights.

## Core Principle

**The system answers: "Should I exit at day 7 or hold for day 30?"**

Current system: Single classification at 30-day completion

- Traders don't know if they should exit early or hold longer
- No visibility into whether peaks come early or late
- Can't distinguish "peaked early then crashed" vs "peaked late and held"

New system: Dual checkpoint with trajectory

- Day 7: "Should I take profits now?" (short-term decision)
- Day 30: "Was my strategy correct?" (long-term outcome)
- Trajectory: "Did it improve or crash after day 7?" (timing insight)
- Peak timing: "When do this channel's calls typically peak?" (pattern learning)

## Validation Approach

Use the existing `scripts/historical_scraper.py` as the **primary validation method**. After implementing each component, run the historical scraper with past messages to validate time-based classification appears in output with correct Day 7 and Day 30 data, trajectory analysis, and peak timing.

The historical scraper processes past Telegram messages and calculates outcomes using historical price data, making it ideal for testing the complete time-based classification flow without waiting for real-time signals to complete.

---

## - [ ] 1. Extend SignalOutcome data model with time-based fields

Add time-based performance fields to the SignalOutcome data model to store Day 7 and Day 30 checkpoint data.

**Purpose**: Store dual-checkpoint performance data (Day 7 + Day 30) with trajectory analysis to enable traders to understand timing patterns and optimal exit windows.

**Implementation Details**:

- Modify `crypto-intelligence/domain/signal_outcome.py`
- Add 8 new fields to SignalOutcome dataclass:
  - `day_7_price: float = 0.0` - Price at day 7 checkpoint
  - `day_7_multiplier: float = 0.0` - ROI multiplier at day 7
  - `day_7_classification: str = ""` - Classification at day 7 (MOON/WINNER/GOOD/BREAK-EVEN/LOSER)
  - `day_30_price: float = 0.0` - Price at day 30 checkpoint
  - `day_30_multiplier: float = 0.0` - ROI multiplier at day 30
  - `day_30_classification: str = ""` - Final classification at day 30
  - `trajectory: str = ""` - Performance trend ("improved" or "crashed")
  - `peak_timing: str = ""` - When ATH occurred ("early_peaker" or "late_peaker")
- All new fields default to 0.0 or empty string
- Maintain backward compatibility with existing signal outcomes
- Update `to_dict()` and `from_dict()` methods to include new fields
- Add docstrings explaining each field's purpose

**External Verification with fetch MCP**:

- Verify Python dataclass best practices: https://docs.python.org/3/library/dataclasses.html
- Verify Optional type hints: https://docs.python.org/3/library/typing.html
- Verify backward compatibility patterns for dataclass extensions

**Files to Modify**:

- `crypto-intelligence/domain/signal_outcome.py` (~20 lines added)

**Validation via Logging**:

Run `python scripts/historical_scraper.py --limit 10` and verify logs show:

1. ✓ "SignalOutcome created with time-based fields: day_7_price, day_7_multiplier, day_7_classification, day_30_price, day_30_multiplier, day_30_classification, trajectory, peak_timing"
2. ✓ "Loading existing signal outcomes: X outcomes loaded successfully"
3. ✓ "Backward compatibility: Existing outcomes loaded with default time-based fields"
4. ✓ "Serializing signal outcome: All 8 time-based fields included in JSON"
5. ✓ "Deserializing signal outcome: Missing time-based fields set to defaults"
6. ✓ No errors when loading existing signal_outcomes.json
7. ✓ Verify signal_outcomes.json contains new fields after save
8. ✓ Verify existing outcomes work without new fields (defaults applied)

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "SignalOutcome data model loaded with time-based fields"
3. Verify no errors from SignalOutcome changes
4. Verify existing signal loading still works
5. Verify new fields can be accessed (even if empty initially)
6. Verify backward compatibility maintained
7. Verify SignalOutcome serialization works with new fields
8. Review verification report confirms no breaking changes

**Requirements**: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8

---

## - [ ] 2. Implement trajectory and peak timing analysis in ROICalculator

Add trajectory analysis and peak timing methods to ROICalculator utility class.

**Purpose**: Calculate trajectory (improved vs crashed) and peak timing (early vs late peaker) to help traders understand performance patterns and optimal exit timing for each channel.

**Implementation Details**:

- Modify `crypto-intelligence/utils/roi_calculator.py`
- Add `analyze_trajectory()` static method:
  - Parameters: `day_7_multiplier: float, day_30_multiplier: float`
  - Returns: `Tuple[str, float]` - (trajectory, crash_severity_percentage)
  - Logic: If day_30 < day_7 → "crashed", else → "improved"
  - Calculate crash severity: `((day_7 - day_30) / day_7) * 100`
  - Example: 2.0x → 1.0x = "crashed" with 50% severity
- Add `determine_peak_timing()` static method:
  - Parameters: `days_to_ath: float`
  - Returns: `str` - "early_peaker" or "late_peaker"
  - Logic: If days_to_ath ≤ 7 → "early_peaker", else → "late_peaker"
- Add `calculate_optimal_exit_window()` static method:
  - Parameters: `days_to_ath: float`
  - Returns: `Tuple[int, int]` - (start_day, end_day)
  - Logic: `(max(0, days_to_ath - 2), days_to_ath + 2)`
  - Example: ATH on day 15 → optimal window is days 13-17
- Add comprehensive docstrings with examples
- Add type hints for all parameters and returns

**External Verification with fetch MCP**:

- Verify statistical analysis patterns: https://en.wikipedia.org/wiki/Statistical_analysis
- Verify percentage calculation best practices
- Verify Python type hints: https://docs.python.org/3/library/typing.html

**Files to Modify**:

- `crypto-intelligence/utils/roi_calculator.py` (~60 lines added)

**Validation via Logging**:

Run `python scripts/historical_scraper.py --limit 10` and verify logs show:

1. ✓ "Trajectory analysis: day_7=2.0x, day_30=1.0x → crashed (50.0% drop)"
2. ✓ "Trajectory analysis: day_7=2.0x, day_30=3.0x → improved (50.0% gain)"
3. ✓ "Peak timing: days_to_ath=5.0 → early_peaker"
4. ✓ "Peak timing: days_to_ath=15.0 → late_peaker"
5. ✓ "Optimal exit window: ATH day 15 → window days 13-17"
6. ✓ "Optimal exit window: ATH day 1 → window days 0-3"
7. ✓ "Optimal exit window: ATH day 30 → window days 28-32"
8. ✓ "ROICalculator methods initialized: analyze_trajectory, determine_peak_timing, calculate_optimal_exit_window"
9. ✓ Verify crash severity calculated correctly in logs
10. ✓ Verify all edge cases handled (days_to_ath=0, 1, 30)

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "ROICalculator: analyze_trajectory called"
3. Verify logs show: "ROICalculator: determine_peak_timing called"
4. Verify logs show: "ROICalculator: calculate_optimal_exit_window called"
5. Verify trajectory calculations appear in logs with correct values
6. Verify peak timing classifications appear in logs
7. Verify optimal exit windows calculated correctly
8. Verify crash severity percentages calculated correctly
9. Review verification report for trajectory and peak timing statistics

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6

---

## - [ ] 3. Implement checkpoint capture logic in OutcomeTracker

Add Day 7 and Day 30 checkpoint capture logic to OutcomeTracker service.

**Purpose**: Capture performance data at Day 7 and Day 30 checkpoints, classify based on ATH at each point, and calculate trajectory to provide traders with actionable timing insights.

**Implementation Details**:

- Modify `crypto-intelligence/services/tracking/outcome_tracker.py`
- Add `_process_day_7_checkpoint()` private method:
  - Extract day_7_price from `outcome.checkpoints["7d"].price`
  - Extract day_7_multiplier from `outcome.checkpoints["7d"].roi_multiplier`
  - Classify based on current ATH using `ROICalculator.categorize_outcome(outcome.ath_multiplier)`
  - Store day_7_classification in outcome
  - Log: "Day 7 checkpoint: {symbol} - ATH {ath}x, Current {current}x, Classification: {category}"
  - Save outcome to repository
- Add `_process_day_30_checkpoint()` private method:
  - Extract day_30_price from `outcome.checkpoints["30d"].price`
  - Extract day_30_multiplier from `outcome.checkpoints["30d"].roi_multiplier`
  - Classify based on final ATH using `ROICalculator.categorize_outcome(outcome.ath_multiplier)`
  - Store day_30_classification in outcome
  - Calculate trajectory using `ROICalculator.analyze_trajectory(day_7_multiplier, day_30_multiplier)`
  - Store trajectory and crash_severity in outcome
  - Determine peak timing using `ROICalculator.determine_peak_timing(outcome.days_to_ath)`
  - Store peak_timing in outcome
  - Mark outcome as complete: `outcome.is_complete = True`, `outcome.status = "completed"`
  - Log: "Day 30 final: {symbol} - ATH {ath}x (day {days}), Final {final}x, Trajectory: {trajectory}"
  - If crash_severity > 50%, log warning: "Severe crash: {symbol} dropped {severity}% from day 7"
  - Save outcome to repository
- Modify `update_price()` method to call checkpoint processors:
  - After existing checkpoint detection logic
  - If "7d" in reached_checkpoints → call `_process_day_7_checkpoint(outcome)`
  - If "30d" in reached_checkpoints → call `_process_day_30_checkpoint(outcome)`
- Ensure checkpoint processing is idempotent (can be called multiple times safely)

**External Verification with fetch MCP**:

- Verify async/await patterns: https://docs.python.org/3/library/asyncio-task.html
- Verify error handling best practices: https://docs.python.org/3/tutorial/errors.html
- Verify logging best practices: https://docs.python.org/3/library/logging.html

**Files to Modify**:

- `crypto-intelligence/services/tracking/outcome_tracker.py` (~80 lines added)

**Validation via Logging**:

Run the system and verify logs show:

**Day 7 Checkpoint:**

1. ✓ "Day 7 checkpoint reached: {symbol}"
2. ✓ "Day 7 checkpoint: {symbol} - ATH 5.0x, Current 2.0x, Classification: MOON"
3. ✓ "Extracted day_7_price: $2.00 from checkpoints['7d']"
4. ✓ "Extracted day_7_multiplier: 2.0x from checkpoints['7d']"
5. ✓ "Day 7 classification: MOON (based on ATH 5.0x)"
6. ✓ "Saved outcome to repository after day 7 checkpoint"

**Day 30 Checkpoint:**

7. ✓ "Day 30 checkpoint reached: {symbol}"
8. ✓ "Day 30 final: {symbol} - ATH 8.0x (day 15), Final 1.0x, Trajectory: crashed"
9. ✓ "Extracted day_30_price: $1.00 from checkpoints['30d']"
10. ✓ "Extracted day_30_multiplier: 1.0x from checkpoints['30d']"
11. ✓ "Day 30 classification: MOON (based on final ATH 8.0x)"
12. ✓ "Trajectory analysis: 2.0x → 1.0x = crashed (50.0% drop)"
13. ✓ "Peak timing: ATH on day 15 → late_peaker"
14. ✓ "Severe crash: {symbol} dropped 50.0% from day 7 to day 30" (when severity > 50%)
15. ✓ "Signal marked as complete: status=completed, is_complete=True"
16. ✓ "Saved outcome to repository after day 30 checkpoint"

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "OutcomeTracker initialized successfully"
3. Verify logs show: "Processing day 7 checkpoint for {symbol}"
4. Verify logs show: "Processing day 30 checkpoint for {symbol}"
5. Verify day 7 data extracted from historical checkpoints
6. Verify day 30 data extracted from historical checkpoints
7. Verify classifications based on ATH at each checkpoint
8. Verify trajectory calculated correctly
9. Verify peak timing determined correctly
10. Verify severe crash warnings logged when appropriate
11. Review verification report for checkpoint statistics
12. Verify signal_outcomes.json contains all time-based fields

**Integration:**

17. ✓ "Checkpoint processor called: \_process_day_7_checkpoint"
18. ✓ "Checkpoint processor called: \_process_day_30_checkpoint"
19. ✓ "Checkpoint processing is idempotent: already processed, skipping"
20. ✓ No errors when processing checkpoints multiple times

**Edge Cases:**

21. ✓ "ATH at day 7 exactly: early_peaker classification"
22. ✓ "ATH at day 30 exactly: late_peaker classification"
23. ✓ "No ATH achieved: price only decreased, ATH = entry price"

**Requirements**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 16.1, 16.2, 16.3, 16.4, 16.5

---

## - [ ] 4. Update PERFORMANCE table output with time-based columns

Extend the PERFORMANCE table in data output to include 8 new time-based columns.

**Purpose**: Display Day 7 and Day 30 performance data in CSV and Google Sheets output so traders can analyze timing patterns and make informed exit decisions.

**Implementation Details**:

- Modify `crypto-intelligence/infrastructure/output/data_output.py`
- Update `PERFORMANCE_COLUMNS` list to add 8 new columns:
  - `peak_timing` - "early_peaker" or "late_peaker"
  - `day_7_price` - Price at day 7 checkpoint
  - `day_7_multiplier` - ROI multiplier at day 7
  - `day_7_classification` - Classification at day 7
  - `day_30_price` - Final price at day 30
  - `day_30_multiplier` - Final ROI multiplier
  - `day_30_classification` - Final classification
  - `trajectory` - "improved" or "crashed"
- Insert new columns after existing `days_to_ath` column (maintain logical grouping)
- Modify `_format_performance_row()` method to populate new columns:
  - Extract values from SignalOutcome object
  - Handle None/empty values gracefully (write empty string)
  - Format multipliers to 2 decimal places
  - Format classifications as uppercase strings
- Update Google Sheets conditional formatting (if applicable):
  - Green: trajectory="improved"
  - Red: trajectory="crashed"
  - Bold: early_peaker with high ROI
- Ensure CSV and Google Sheets both receive new columns
- Maintain column order and alignment

**External Verification with fetch MCP**:

- Verify CSV format best practices: https://docs.python.org/3/library/csv.html
- Verify Google Sheets API: https://docs.gspread.org/en/latest/
- Verify handling None/null values in CSV

**Files to Modify**:

- `crypto-intelligence/infrastructure/output/data_output.py` (~30 lines modified)

**Validation via Logging**:

Run the system and verify logs show:

**Column Updates:**

1. ✓ "PERFORMANCE_COLUMNS updated: Added 8 time-based columns"
2. ✓ "New columns: peak_timing, day_7_price, day_7_multiplier, day_7_classification, day_30_price, day_30_multiplier, day_30_classification, trajectory"
3. ✓ "Total PERFORMANCE columns: {original_count + 8}"

**CSV Output:**

4. ✓ "Writing PERFORMANCE CSV: {total_columns} columns"
5. ✓ "CSV headers: ...peak_timing, day_7_price, day_7_multiplier, day_7_classification, day_30_price, day_30_multiplier, day_30_classification, trajectory..."
6. ✓ "Formatting performance row: peak_timing=late_peaker, day_7_multiplier=2.00x, day_30_multiplier=1.00x, trajectory=crashed"
7. ✓ "Handling empty values: day_30_price='' (not yet reached)"
8. ✓ "Multipliers formatted to 2 decimals: 2.00x, 1.00x"

**Google Sheets Output:**

9. ✓ "Updating Google Sheets PERFORMANCE table: {total_columns} columns"
10. ✓ "Google Sheets headers match CSV headers"
11. ✓ "Conditional formatting applied: trajectory=improved → green, trajectory=crashed → red"
12. ✓ "Google Sheets data populated successfully"

**Data Scenarios:**

13. ✓ "Complete signal: All 8 time-based fields populated"
14. ✓ "Partial signal (day 7 only): day*7*_ populated, day*30*_ empty"
15. ✓ "In-progress signal: peak_timing and trajectory empty (not yet determined)"
16. ✓ "Backward compatibility: Existing PERFORMANCE data loaded without errors"

**File Verification:**

17. ✓ Verify token_prices.csv or performance.csv has 8 new columns
18. ✓ Verify column headers are correct
19. ✓ Verify data rows show time-based values
20. ✓ Verify Google Sheets shows new columns with data

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "PERFORMANCE_COLUMNS updated with time-based fields"
3. Verify logs show: "Writing PERFORMANCE CSV with {total_columns} columns"
4. Verify CSV file has 8 new columns
5. Verify column headers include all time-based fields
6. Verify data rows populate time-based columns
7. Verify Google Sheets updated with new columns
8. Verify conditional formatting applied
9. Review verification report for output statistics
10. Verify performance.csv or token_prices.csv contains time-based data

**Requirements**: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8

---

## - [ ] 5. Integrate channel reputation with timing patterns

Extend channel reputation calculation to include timing pattern metrics.

**Purpose**: Track channel-specific timing patterns (early vs late peaker ratio, average days to ATH, crash rate after day 7) so traders know when to exit for each channel.

**Implementation Details**:

- Modify `crypto-intelligence/services/reputation/reputation_calculator.py`
- Add timing pattern fields to ChannelReputation dataclass:
  - `early_peaker_percentage: float = 0.0` - % of signals that peak within 7 days
  - `late_peaker_percentage: float = 0.0` - % of signals that peak after 7 days
  - `average_days_to_ath: float = 0.0` - Mean days to reach ATH
  - `crash_rate_after_day_7: float = 0.0` - % of signals that crash from day 7 to day 30
  - `recommended_hold_period: str = ""` - "Exit early (1-7 days)" or "Hold longer (7-30 days)"
- Add `_calculate_timing_patterns()` private method:
  - Count early_peaker signals (days_to_ath ≤ 7)
  - Count late_peaker signals (days_to_ath > 7)
  - Calculate percentages
  - Calculate average days_to_ath across all signals
  - Count signals with trajectory="crashed"
  - Calculate crash_rate_after_day_7
  - Determine recommended_hold_period:
    - If early_peaker_percentage > 70% → "Exit early (1-7 days)"
    - If late_peaker_percentage > 70% → "Hold longer (7-30 days)"
    - Else → "Monitor closely, mixed patterns"
- Integrate `_calculate_timing_patterns()` into `calculate_reputation()` method
- Update reputation display to show timing patterns
- Log timing pattern insights: "Channel timing: {early}% early peakers, {late}% late peakers, avg {days} days to ATH"

**External Verification with fetch MCP**:

- Verify statistical aggregation patterns
- Verify percentage calculation best practices
- Verify recommendation logic patterns

**Files to Modify**:

- `crypto-intelligence/services/reputation/reputation_calculator.py` (~60 lines added)
- `crypto-intelligence/domain/channel_reputation.py` (~10 lines added for new fields)

**Validation via Logging**:

Run the system and verify logs show:

**Timing Pattern Calculation:**

1. ✓ "Calculating timing patterns for channel: {channel_name}"
2. ✓ "Early peakers: 7/10 signals (70.0%)"
3. ✓ "Late peakers: 3/10 signals (30.0%)"
4. ✓ "Average days to ATH: 9.8 days"
5. ✓ "Crash rate after day 7: 6/10 signals (60.0%)"

**Recommended Hold Period:**

6. ✓ "Recommended hold period: Exit early (1-7 days)" (when early_peaker_percentage > 70%)
7. ✓ "Recommended hold period: Hold longer (7-30 days)" (when late_peaker_percentage > 70%)
8. ✓ "Recommended hold period: Monitor closely, mixed patterns" (when 50/50 split)

**Integration:**

9. ✓ "Timing patterns integrated into reputation calculation"
10. ✓ "Channel timing: 70% early peakers, 30% late peakers, avg 9.8 days to ATH"
11. ✓ "Reputation display includes timing patterns"

**Edge Cases:**

12. ✓ "No signals: Timing patterns unavailable (0 signals)"
13. ✓ "Single signal: Timing patterns based on 1 signal (limited data)"
14. ✓ "All early peakers: 100% early, 0% late, recommended: Exit early"
15. ✓ "All late peakers: 0% early, 100% late, recommended: Hold longer"

**File Verification:**

16. ✓ Verify channels.json contains timing pattern fields
17. ✓ Verify early_peaker_percentage, late_peaker_percentage calculated
18. ✓ Verify average_days_to_ath, crash_rate_after_day_7 calculated
19. ✓ Verify recommended_hold_period set correctly

**Historical Scraper Verification**:

Since real-time crypto messages are slow, use the existing `scripts/historical_scraper.py` to validate this component:

1. Run `python scripts/historical_scraper.py --limit 10`
2. Verify logs show: "Calculating timing patterns for channel: {channel_name}"
3. Verify logs show: "Early peakers: X/Y signals (Z%)"
4. Verify logs show: "Late peakers: X/Y signals (Z%)"
5. Verify logs show: "Average days to ATH: X.X days"
6. Verify logs show: "Crash rate after day 7: X/Y signals (Z%)"
7. Verify logs show: "Recommended hold period: {recommendation}"
8. Verify timing patterns integrated into reputation calculation
9. Review verification report for timing pattern statistics
10. Verify channels.json contains all timing pattern fields

**Requirements**: 10.1, 10.2, 10.3, 10.4, 10.5, 17.1, 17.2, 17.3, 17.4, 17.5, 18.1, 18.2, 18.3, 18

---

---

## Final Validation Checklist

After completing all tasks, verify the complete system works end-to-end by checking logs:

### Component Verification

- [ ] ✓ "SignalOutcome data model extended with 8 time-based fields"
- [ ] ✓ "ROICalculator methods added: analyze_trajectory, determine_peak_timing, calculate_optimal_exit_window"
- [ ] ✓ "OutcomeTracker checkpoint processors implemented: \_process_day_7_checkpoint, \_process_day_30_checkpoint"
- [ ] ✓ "PERFORMANCE table extended with 8 new columns"
- [ ] ✓ "Channel reputation extended with timing pattern metrics"

### Data Flow Verification

- [ ] ✓ "Day 7 checkpoint: Data captured from checkpoints['7d']"
- [ ] ✓ "Day 7 classification: Based on current ATH"
- [ ] ✓ "Day 30 checkpoint: Data captured from checkpoints['30d']"
- [ ] ✓ "Day 30 classification: Based on final ATH"
- [ ] ✓ "Trajectory calculated: improved or crashed"
- [ ] ✓ "Peak timing determined: early_peaker or late_peaker"
- [ ] ✓ "Optimal exit window calculated: days X-Y"

### Output Verification

- [ ] ✓ "CSV output contains 8 new time-based columns"
- [ ] ✓ "Google Sheets output contains 8 new time-based columns"
- [ ] ✓ "Conditional formatting applied: green for improved, red for crashed"
- [ ] ✓ "Channel reputation includes timing patterns"
- [ ] ✓ "Recommended hold period displayed for each channel"

### Integration Verification

- [ ] ✓ "Checkpoint system integration: No breaking changes"
- [ ] ✓ "OHLC tracking continues: ATH updates through full 30 days"
- [ ] ✓ "Backward compatibility: Existing signal outcomes load correctly"
- [ ] ✓ "Performance impact: < 10ms overhead per checkpoint"

---

## Example Output

### Console Logs

```
[2025-11-10 23:00:00] [INFO] [OutcomeTracker] Day 7 checkpoint reached: AVICI
[2025-11-10 23:00:00] [INFO] [OutcomeTracker] Day 7 checkpoint: AVICI - ATH 5.0x, Current 2.0x, Classification: MOON
[2025-11-10 23:00:00] [INFO] [OutcomeTracker] Extracted day_7_price: $2.00 from checkpoints['7d']
[2025-11-10 23:00:00] [INFO] [OutcomeTracker] Extracted day_7_multiplier: 2.0x from checkpoints['7d']
[2025-11-10 23:00:00] [INFO] [OutcomeTracker] Day 7 classification: MOON (based on ATH 5.0x)
[2025-11-10 23:00:00] [INFO] [OutcomeTracker] Saved outcome to repository after day 7 checkpoint

[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Day 30 checkpoint reached: AVICI
[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Day 30 final: AVICI - ATH 8.0x (day 15), Final 1.0x, Trajectory: crashed
[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Extracted day_30_price: $1.00 from checkpoints['30d']
[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Extracted day_30_multiplier: 1.0x from checkpoints['30d']
[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Day 30 classification: MOON (based on final ATH 8.0x)
[2025-12-10 23:00:00] [INFO] [ROICalculator] Trajectory analysis: 2.0x → 1.0x = crashed (50.0% drop)
[2025-12-10 23:00:00] [INFO] [ROICalculator] Peak timing: ATH on day 15 → late_peaker
[2025-12-10 23:00:00] [WARN] [OutcomeTracker] Severe crash: AVICI dropped 50.0% from day 7 to day 30
[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Signal marked as complete: status=completed, is_complete=True
[2025-12-10 23:00:00] [INFO] [OutcomeTracker] Saved outcome to repository after day 30 checkpoint

[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Calculating timing patterns for channel: Eric Cryptomans Journal
[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Early peakers: 7/10 signals (70.0%)
[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Late peakers: 3/10 signals (30.0%)
[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Average days to ATH: 9.8 days
[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Crash rate after day 7: 6/10 signals (60.0%)
[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Recommended hold period: Monitor closely, mixed patterns
[2025-12-10 23:00:01] [INFO] [ReputationCalculator] Channel timing: 70% early peakers, 30% late peakers, avg 9.8 days to ATH

[2025-12-10 23:00:02] [INFO] [DataOutput] PERFORMANCE_COLUMNS updated: Added 8 time-based columns
[2025-12-10 23:00:02] [INFO] [DataOutput] Writing PERFORMANCE CSV: 18 columns
[2025-12-10 23:00:02] [INFO] [DataOutput] Formatting performance row: peak_timing=late_peaker, day_7_multiplier=2.00x, day_30_multiplier=1.00x, trajectory=crashed
[2025-12-10 23:00:02] [INFO] [DataOutput] Updating Google Sheets PERFORMANCE table: 18 columns
[2025-12-10 23:00:02] [INFO] [DataOutput] Conditional formatting applied: trajectory=crashed → red
```

### CSV Output (performance.csv)

```csv
address,chain,first_message_id,start_price,start_time,ath_since_mention,ath_time,ath_multiplier,current_multiplier,days_tracked,days_to_ath,peak_timing,day_7_price,day_7_multiplier,day_7_classification,day_30_price,day_30_multiplier,day_30_classification,trajectory
5gb4npgfb3...,solana,12345,1.00,2025-11-10T10:00:00Z,8.00,2025-11-25T14:00:00Z,8.0,1.0,30,15.0,late_peaker,2.00,2.0,MOON,1.00,1.0,MOON,crashed
```

### Human-Readable Interpretation

```
Signal: AVICI
Entry: $1.00 on Nov 10, 2025

Day 7 Checkpoint (Nov 17):
  ATH so far: $5.00 (5.0x) - reached on day 2
  Current price: $2.00 (2.0x)
  Classification: MOON 🌙
  Decision: "Peaked early, consider taking profits"

Day 30 Final (Dec 10):
  Final ATH: $8.00 (8.0x) - reached on day 15
  Final price: $1.00 (1.0x)
  Classification: MOON 🌙 (channel gets credit for 8x peak!)
  Trajectory: Crashed (2.0x → 1.0x = 50% drop)
  Peak timing: Late peaker (day 15)
  Insight: "Peak came late (day 15), but crashed hard by day 30"

Channel Impact:
  ✅ MOON classification (8.0x ATH)
  ✅ Win rate increases
  ✅ Average ROI increases
  ℹ️ Pattern: Late peaker, high crash rate after day 7
  ℹ️ Recommendation: "Monitor closely, mixed patterns"
```

### Channel Reputation Output

```json
{
  "channel_name": "Eric Cryptomans Journal",
  "total_signals": 10,
  "win_rate": 0.6,
  "average_roi": 1.85,
  "reputation_score": 78.5,
  "reputation_tier": "Excellent",
  "early_peaker_percentage": 70.0,
  "late_peaker_percentage": 30.0,
  "average_days_to_ath": 9.8,
  "crash_rate_after_day_7": 60.0,
  "recommended_hold_period": "Monitor closely, mixed patterns"
}
```

---

## Success Criteria

- ✅ All 5 tasks completed
- ✅ Time-based performance data appears in output
- ✅ Day 7 and Day 30 checkpoints captured correctly
- ✅ Trajectory analysis works (improved vs crashed)
- ✅ Peak timing determined (early vs late peaker)
- ✅ Channel reputation includes timing patterns
- ✅ Recommended hold period calculated per channel
- ✅ No breaking changes to existing functionality
- ✅ Performance overhead < 10ms per checkpoint
- ✅ Backward compatibility maintained
- ✅ Logs provide complete visibility into time-based classification
