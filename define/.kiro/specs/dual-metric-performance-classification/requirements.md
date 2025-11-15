# Requirements Document - Time-Based Performance Classification System

## Introduction

This specification implements a time-based performance classification system that evaluates cryptocurrency signals at two critical checkpoints: **Day 7** (short-term trading) and **Day 30** (long-term analysis). The system tracks ATH (All-Time High) continuously across the full 30-day window and compares it against prices at both checkpoints to provide traders with actionable insights about optimal exit timing.

The current system only provides a single classification at completion. The new system adds a Day 7 checkpoint to help traders make informed decisions about whether to take profits early or hold for potential late-stage gains, while still capturing the complete 30-day performance picture.

## Glossary

- **System**: The crypto intelligence monitoring application
- **Time-Based Classification**: Performance evaluation at multiple time checkpoints (Day 7 and Day 30)
- **ATH (All-Time High)**: Highest price achieved during the entire 30-day tracking window
- **Day 7 Checkpoint**: First evaluation point for short-term trading decisions
- **Day 30 Checkpoint**: Final evaluation point for complete performance analysis
- **Trajectory**: Performance trend from Day 7 to Day 30 (improved or crashed)
- **Checkpoint Data**: Price, ROI, and classification captured at specific time intervals
- **Active Tracking**: Real-time price monitoring with 2-hour updates (Days 0-7)
- **OHLC Monitoring**: Daily high/low price checks via historical data (Days 7-30)
- **Signal Outcome**: Complete tracking result including all checkpoints and classifications
- **Channel Reputation**: Quality score based on ATH performance across all signals
- **Early Peaker**: Token that reaches ATH within first 7 days
- **Late Peaker**: Token that reaches ATH after day 7
- **Optimal Exit Window**: Time period around ATH when traders should take profits
- **Performance Gap**: Difference between Day 7 and Day 30 multipliers

## Requirements

### Requirement 1: Continuous ATH Tracking (0-30 Days)

**User Story:** As a system operator, I want ATH tracked continuously across all 30 days, so that we capture the peak regardless of when it occurs.

#### Acceptance Criteria

1. WHEN tracking starts, THE System SHALL initialize ATH to entry price
2. WHILE tracking is active (days 0-30), THE System SHALL update ATH whenever current price exceeds previous ATH
3. WHEN ATH is updated, THE System SHALL record the timestamp of the new ATH
4. WHEN ATH is updated, THE System SHALL calculate days_to_ath from entry timestamp
5. WHEN 30 days elapse, THE System SHALL lock the final ATH value
6. WHERE price never exceeds entry price, THE System SHALL maintain ATH equal to entry price

### Requirement 2: Day 7 Checkpoint Capture

**User Story:** As a trader, I want to see performance at day 7, so that I can decide whether to take profits or continue holding.

#### Acceptance Criteria

1. WHEN 7 days elapse from entry, THE System SHALL capture current price as day_7_price
2. WHEN day 7 checkpoint is reached, THE System SHALL calculate day_7_multiplier as day_7_price / entry_price
3. WHEN day 7 checkpoint is reached, THE System SHALL record ATH value at that point in time
4. WHEN day 7 checkpoint is reached, THE System SHALL classify signal based on current ATH
5. WHEN day 7 checkpoint is reached, THE System SHALL store day_7_classification
6. WHEN day 7 checkpoint is reached, THE System SHALL continue tracking for remaining 23 days

### Requirement 3: Day 30 Checkpoint Capture

**User Story:** As a trader, I want to see final performance at day 30, so that I understand the complete outcome and optimal exit timing.

#### Acceptance Criteria

1. WHEN 30 days elapse from entry, THE System SHALL capture current price as day_30_price
2. WHEN day 30 checkpoint is reached, THE System SHALL calculate day_30_multiplier as day_30_price / entry_price
3. WHEN day 30 checkpoint is reached, THE System SHALL record final ATH value (locked)
4. WHEN day 30 checkpoint is reached, THE System SHALL classify signal based on final ATH
5. WHEN day 30 checkpoint is reached, THE System SHALL store day_30_classification
6. WHEN day 30 checkpoint is reached, THE System SHALL stop tracking

### Requirement 4: ATH-Based Classification

**User Story:** As a trader, I want signals classified by peak opportunity (ATH), so that channels get credit for identifying spikes regardless of post-peak crashes.

#### Acceptance Criteria

1. WHEN classifying at day 7, THE System SHALL use ATH from days 0-7 for classification
2. WHEN classifying at day 30, THE System SHALL use final ATH from days 0-30 for classification
3. WHEN ATH is greater than or equal to 5.0x, THE System SHALL classify as "MOON"
4. WHEN ATH is greater than or equal to 2.0x, THE System SHALL classify as "WINNER"
5. WHEN ATH is greater than or equal to 1.5x, THE System SHALL classify as "GOOD"
6. WHEN ATH is greater than or equal to 1.0x, THE System SHALL classify as "BREAK-EVEN"
7. WHEN ATH is less than 1.0x, THE System SHALL classify as "LOSER"

### Requirement 5: Trajectory Analysis

**User Story:** As a trader, I want to know if performance improved or crashed after day 7, so that I can learn optimal exit timing patterns.

#### Acceptance Criteria

1. WHEN day 30 checkpoint is reached, THE System SHALL compare day_7_multiplier with day_30_multiplier
2. WHEN day_30_multiplier is less than day_7_multiplier, THE System SHALL set trajectory to "crashed"
3. WHEN day_30_multiplier is greater than or equal to day_7_multiplier, THE System SHALL set trajectory to "improved"
4. WHEN trajectory is "crashed", THE System SHALL calculate crash_severity as percentage drop
5. WHEN crash_severity exceeds 50%, THE System SHALL flag as "severe_crash"
6. WHEN trajectory is calculated, THE System SHALL store in signal outcome

### Requirement 6: Peak Timing Analysis

**User Story:** As a trader, I want to know when the ATH occurred, so that I understand if peaks come early or late for this channel.

#### Acceptance Criteria

1. WHEN ATH is updated, THE System SHALL record ath_timestamp
2. WHEN ATH is updated, THE System SHALL calculate days_to_ath from entry_timestamp
3. WHEN days_to_ath is less than or equal to 7, THE System SHALL classify as "early_peaker"
4. WHEN days_to_ath is greater than 7, THE System SHALL classify as "late_peaker"
5. WHEN day 30 checkpoint is reached, THE System SHALL determine optimal_exit_window as days_to_ath ± 2 days
6. WHEN peak timing is determined, THE System SHALL store peak_timing classification

### Requirement 7: Signal Outcome Data Model

**User Story:** As a developer, I want signal outcomes to store both checkpoint data, so that we can analyze performance at multiple timeframes.

#### Acceptance Criteria

1. WHEN signal outcome is created, THE System SHALL initialize day_7_price field as 0.0
2. WHEN signal outcome is created, THE System SHALL initialize day_7_multiplier field as 0.0
3. WHEN signal outcome is created, THE System SHALL initialize day_7_classification field as empty string
4. WHEN signal outcome is created, THE System SHALL initialize day_30_price field as 0.0
5. WHEN signal outcome is created, THE System SHALL initialize day_30_multiplier field as 0.0
6. WHEN signal outcome is created, THE System SHALL initialize day_30_classification field as empty string
7. WHEN signal outcome is created, THE System SHALL initialize trajectory field as empty string
8. WHEN signal outcome is created, THE System SHALL initialize peak_timing field as empty string

### Requirement 8: Checkpoint Integration with Existing System

**User Story:** As a developer, I want to use existing checkpoint infrastructure, so that implementation is minimal and leverages proven code.

#### Acceptance Criteria

1. WHEN 7-day checkpoint is reached, THE System SHALL access existing checkpoints["7d"] data
2. WHEN 7-day checkpoint is reached, THE System SHALL extract price from checkpoints["7d"].price
3. WHEN 7-day checkpoint is reached, THE System SHALL extract roi_multiplier from checkpoints["7d"].roi_multiplier
4. WHEN 30-day checkpoint is reached, THE System SHALL access existing checkpoints["30d"] data
5. WHEN 30-day checkpoint is reached, THE System SHALL extract price from checkpoints["30d"].price
6. WHEN 30-day checkpoint is reached, THE System SHALL extract roi_multiplier from checkpoints["30d"].roi_multiplier

### Requirement 9: Performance Table Output

**User Story:** As a trader, I want to see both day 7 and day 30 performance in CSV output, so that I can analyze timing patterns in spreadsheets.

#### Acceptance Criteria

1. WHEN writing to PERFORMANCE table, THE System SHALL include day_7_price column
2. WHEN writing to PERFORMANCE table, THE System SHALL include day_7_multiplier column
3. WHEN writing to PERFORMANCE table, THE System SHALL include day_7_classification column
4. WHEN writing to PERFORMANCE table, THE System SHALL include day_30_price column
5. WHEN writing to PERFORMANCE table, THE System SHALL include day_30_multiplier column
6. WHEN writing to PERFORMANCE table, THE System SHALL include day_30_classification column
7. WHEN writing to PERFORMANCE table, THE System SHALL include trajectory column
8. WHEN writing to PERFORMANCE table, THE System SHALL include peak_timing column

### Requirement 10: Channel Reputation Integration

**User Story:** As a trader, I want channel reputation based on ATH performance, so that channels get credit for identifying opportunities regardless of post-peak behavior.

#### Acceptance Criteria

1. WHEN calculating win rate, THE System SHALL use ATH multiplier greater than or equal to 2.0x as winner threshold
2. WHEN calculating average ROI, THE System SHALL use ATH multipliers from all signals
3. WHEN calculating reputation score, THE System SHALL NOT penalize for post-peak crashes
4. WHEN calculating reputation score, THE System SHALL use days_to_ath for speed metric
5. WHEN calculating reputation metrics, THE System SHALL track early_peaker vs late_peaker ratio as informational metric

### Requirement 11: Trader Intelligence Display

**User Story:** As a trader, I want clear display of both checkpoints, so that I can quickly understand timing and trajectory.

#### Acceptance Criteria

1. WHEN displaying signal outcome, THE System SHALL show ATH with days_to_ath
2. WHEN displaying signal outcome, THE System SHALL show day 7 price and classification
3. WHEN displaying signal outcome, THE System SHALL show day 30 price and classification
4. WHEN displaying signal outcome, THE System SHALL show trajectory with severity if crashed
5. WHEN displaying signal outcome, THE System SHALL show optimal_exit_window recommendation
6. WHEN displaying signal outcome, THE System SHALL show peak_timing classification

### Requirement 12: Backward Compatibility

**User Story:** As a system operator, I want existing signal outcomes migrated to time-based format, so that historical data remains usable.

#### Acceptance Criteria

1. WHEN loading existing signal outcomes without day_7_price, THE System SHALL extract from checkpoints["7d"].price if available
2. WHEN loading existing signal outcomes without day_7_multiplier, THE System SHALL extract from checkpoints["7d"].roi_multiplier if available
3. WHEN loading existing signal outcomes without day_30_price, THE System SHALL extract from checkpoints["30d"].price if available
4. WHEN loading existing signal outcomes without day_30_multiplier, THE System SHALL extract from checkpoints["30d"].roi_multiplier if available
5. WHEN loading existing signal outcomes, THE System SHALL recalculate classifications using ATH-based logic
6. WHEN loading existing signal outcomes, THE System SHALL calculate trajectory from checkpoint data
7. WHEN migration is complete, THE System SHALL save updated outcomes to repository

### Requirement 13: Classification Consistency

**User Story:** As a system operator, I want classification logic validated at startup, so that categories are always correct.

#### Acceptance Criteria

1. WHEN System starts, THE System SHALL validate MOON category requires ATH greater than or equal to 5.0x
2. WHEN System starts, THE System SHALL validate WINNER category requires ATH greater than or equal to 2.0x
3. WHEN System starts, THE System SHALL validate GOOD category requires ATH greater than or equal to 1.5x
4. WHEN System starts, THE System SHALL validate BREAK-EVEN category requires ATH greater than or equal to 1.0x
5. WHEN System starts, THE System SHALL validate LOSER category requires ATH less than 1.0x
6. IF any validation fails, THEN THE System SHALL log error and prevent signal processing

### Requirement 14: Real-World Validation

**User Story:** As a system operator, I want classification tested against real scenarios, so that logic handles all cases correctly.

#### Acceptance Criteria

1. WHEN testing early peaker (ATH day 2), THE System SHALL correctly classify at both day 7 and day 30
2. WHEN testing late peaker (ATH day 15), THE System SHALL show different ATH at day 7 vs day 30
3. WHEN testing crash scenario, THE System SHALL correctly identify trajectory as "crashed"
4. WHEN testing improvement scenario, THE System SHALL correctly identify trajectory as "improved"
5. WHEN testing break-even scenario, THE System SHALL correctly classify as BREAK-EVEN or LOSER

### Requirement 15: Performance Impact Monitoring

**User Story:** As a system operator, I want to monitor performance impact of time-based system, so that I ensure efficiency.

#### Acceptance Criteria

1. WHEN capturing day 7 checkpoint, THE System SHALL complete in less than 10 milliseconds
2. WHEN capturing day 30 checkpoint, THE System SHALL complete in less than 10 milliseconds
3. WHEN calculating trajectory, THE System SHALL complete in less than 1 millisecond
4. WHEN storing time-based fields, THE System SHALL add no more than 64 bytes per signal outcome
5. WHEN processing 1000 signals, THE System SHALL require no more than 10 seconds total for time-based calculations

### Requirement 16: Logging and Debugging

**User Story:** As a developer, I want comprehensive logging for time-based operations, so that I can debug issues quickly.

#### Acceptance Criteria

1. WHEN day 7 checkpoint is reached, THE System SHALL log: "Day 7 checkpoint: ATH X.XXx, Current Y.YYx, Classification: CATEGORY"
2. WHEN day 30 checkpoint is reached, THE System SHALL log: "Day 30 final: ATH X.XXx, Final Y.YYx, Trajectory: TRAJECTORY"
3. WHEN ATH is updated, THE System SHALL log: "New ATH: $X.XX (Z.ZZx) on day N"
4. WHEN trajectory is "crashed", THE System SHALL log warning: "Crashed W% from day 7 to day 30"
5. WHEN peak timing is determined, THE System SHALL log: "Peak timing: TIMING (day N)"

### Requirement 17: Channel Pattern Analysis

**User Story:** As a trader, I want to see channel-specific timing patterns, so that I know when to exit for each channel.

#### Acceptance Criteria

1. WHEN calculating channel reputation, THE System SHALL track percentage of early_peaker signals
2. WHEN calculating channel reputation, THE System SHALL track percentage of late_peaker signals
3. WHEN calculating channel reputation, THE System SHALL track average days_to_ath
4. WHEN calculating channel reputation, THE System SHALL track crash_rate_after_day_7
5. WHEN displaying channel stats, THE System SHALL show recommended_hold_period based on patterns

### Requirement 18: Optimal Exit Recommendations

**User Story:** As a trader, I want system-generated exit recommendations, so that I know when to take profits.

#### Acceptance Criteria

1. WHEN signal completes, THE System SHALL calculate optimal_exit_window as days_to_ath ± 2 days
2. WHEN trajectory is "crashed", THE System SHALL recommend "Take profits within 2 days of ATH"
3. WHEN trajectory is "improved", THE System SHALL recommend "Consider holding past day 7"
4. WHEN channel is early_peaker pattern, THE System SHALL recommend "Monitor closely days 1-7"
5. WHEN channel is late_peaker pattern, THE System SHALL recommend "Be patient, peaks often after day 7"

### Requirement 19: Data Persistence

**User Story:** As a system operator, I want time-based data persisted reliably, so that analysis survives system restarts.

#### Acceptance Criteria

1. WHEN day 7 checkpoint is captured, THE System SHALL save to signal_outcomes.json within 5 seconds
2. WHEN day 30 checkpoint is captured, THE System SHALL save to signal_outcomes.json within 5 seconds
3. WHEN System restarts, THE System SHALL load all time-based fields from JSON
4. WHEN JSON file is corrupted, THE System SHALL log error and attempt recovery from backup
5. WHERE recovery fails, THE System SHALL initialize with empty data and log critical error

### Requirement 20: Documentation and User Guidance

**User Story:** As a trader, I want clear documentation explaining time-based classifications, so that I understand what each metric means.

#### Acceptance Criteria

1. WHEN System outputs results, THE System SHALL include legend explaining day 7 vs day 30
2. WHEN displaying MOON category, THE System SHALL explain: "Exceptional 5x+ peak opportunity"
3. WHEN displaying trajectory "crashed", THE System SHALL explain: "Price dropped from day 7 to day 30"
4. WHEN displaying trajectory "improved", THE System SHALL explain: "Price increased from day 7 to day 30"
5. WHEN displaying early_peaker, THE System SHALL explain: "Peak occurred within first 7 days"
6. WHEN displaying late_peaker, THE System SHALL explain: "Peak occurred after day 7"
7. WHEN displaying optimal_exit_window, THE System SHALL explain: "Best time to 