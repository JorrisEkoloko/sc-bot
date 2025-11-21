# Requirements Document

## Introduction

This specification defines a comprehensive table verification system for the crypto intelligence platform. The system validates data integrity across 8 output tables containing 110+ columns, ensuring accurate data flow from source systems through processing pipelines to final output. The verification system employs isolated unit testing for each table column followed by integrated end-to-end validation.

## Glossary

- **DataOutput**: The system component responsible for writing data to CSV files and Google Sheets
- **PerformanceTracker**: Service that tracks token performance metrics over time
- **OutcomeTracker**: Service that records final trading outcomes for signals
- **MessageProcessor**: Component that processes incoming Telegram messages
- **ChannelReputation**: System that maintains reputation scores for Telegram channels
- **SignalOutcome**: Data structure containing final performance results for a signal
- **PerformanceData**: Data structure containing ongoing performance metrics
- **MESSAGES Table**: Output table containing raw message data (16 columns)
- **PERFORMANCE Table**: Output table containing performance tracking data (19 columns)
- **OUTCOMES Table**: Output table containing final trading results (15 columns)
- **CHANNEL_REPUTATION Table**: Output table containing channel scoring data (14 columns)
- **MARKET_ANALYSIS Table**: Output table containing market intelligence (12 columns)
- **HDRB_SCORES Table**: Output table containing holistic signal scores (10 columns)
- **ACTIVE_TRACKING Table**: Output table containing currently monitored tokens (8 columns)
- **SUMMARY_STATS Table**: Output table containing aggregated statistics (18 columns)
- **Test Fixture**: Predefined test data with known expected outputs
- **Unit Test**: Isolated test validating a single column or component
- **Integration Test**: Test validating data flow between multiple components
- **End-to-End Test**: Complete system test from message input to table output

## Requirements

### Requirement 1: MESSAGES Table Column Verification

**User Story:** As a data analyst, I want every column in the MESSAGES table to be individually verified, so that I can trust the accuracy of raw message data.

#### Acceptance Criteria

1. WHEN the verification system tests column 1 (message_id), THE Verification_System SHALL validate that message IDs are unique integers greater than zero
2. WHEN the verification system tests column 2 (timestamp), THE Verification_System SHALL validate that timestamps are valid ISO 8601 format strings
3. WHEN the verification system tests column 3 (channel_name), THE Verification_System SHALL validate that channel names match configured channel identifiers
4. WHEN the verification system tests column 4 (message_text), THE Verification_System SHALL validate that message text is non-empty and properly escaped
5. WHEN the verification system tests column 5 (coin_symbol), THE Verification_System SHALL validate that coin symbols are uppercase alphanumeric strings
6. WHEN the verification system tests column 6 (chain), THE Verification_System SHALL validate that chain values are either "ethereum" or "solana"
7. WHEN the verification system tests column 7 (contract_address), THE Verification_System SHALL validate that addresses match chain-specific format patterns
8. WHEN the verification system tests column 8 (initial_price), THE Verification_System SHALL validate that prices are positive decimal numbers with proper precision
9. WHEN the verification system tests column 9 (initial_market_cap), THE Verification_System SHALL validate that market caps are positive integers or "N/A"
10. WHEN the verification system tests column 10 (market_cap_tier), THE Verification_System SHALL validate that tiers are "micro", "small", or "large"
11. WHEN the verification system tests column 11 (sentiment_score), THE Verification_System SHALL validate that scores are decimals between -1.0 and 1.0
12. WHEN the verification system tests column 12 (hdrb_score), THE Verification_System SHALL validate that scores are decimals between 0.0 and 1.0
13. WHEN the verification system tests column 13 (channel_reputation), THE Verification_System SHALL validate that reputation scores are decimals between 0.0 and 1.0
14. WHEN the verification system tests column 14 (channel_win_rate), THE Verification_System SHALL validate that win rates are percentages between 0.0 and 100.0
15. WHEN the verification system tests column 15 (channel_avg_roi), THE Verification_System SHALL validate that ROI values are decimal multipliers
16. WHEN the verification system tests column 16 (channel_total_signals), THE Verification_System SHALL validate that signal counts are non-negative integers

### Requirement 2: PERFORMANCE Table Column Verification

**User Story:** As a performance analyst, I want every column in the PERFORMANCE table to be individually verified, so that I can accurately track token performance over time.

#### Acceptance Criteria

1. WHEN the verification system tests column 1 (coin_symbol), THE Verification_System SHALL validate that symbols match corresponding MESSAGES table entries
2. WHEN the verification system tests column 2 (contract_address), THE Verification_System SHALL validate that addresses match corresponding MESSAGES table entries
3. WHEN the verification system tests column 3 (initial_price), THE Verification_System SHALL validate that prices match corresponding MESSAGES table entries
4. WHEN the verification system tests column 4 (current_price), THE Verification_System SHALL validate that prices are positive decimals updated within 2 hours
5. WHEN the verification system tests column 5 (ath_price), THE Verification_System SHALL validate that ATH prices are greater than or equal to initial prices
6. WHEN the verification system tests column 6 (current_roi), THE Verification_System SHALL validate that ROI equals (current_price / initial_price)
7. WHEN the verification system tests column 7 (ath_roi), THE Verification_System SHALL validate that ATH ROI equals (ath_price / initial_price)
8. WHEN the verification system tests column 8 (days_tracked), THE Verification_System SHALL validate that days are non-negative integers less than or equal to 30
9. WHEN the verification system tests column 9 (last_updated), THE Verification_System SHALL validate that timestamps are within the last 2 hours
10. WHEN the verification system tests column 10 (tracking_status), THE Verification_System SHALL validate that status is "active", "completed", or "failed"
11. WHEN the verification system tests column 11 (day_7_price), THE Verification_System SHALL validate that day 7 prices are positive decimals or "N/A"
12. WHEN the verification system tests column 12 (day_7_roi), THE Verification_System SHALL validate that day 7 ROI equals (day_7_price / initial_price) or "N/A"
13. WHEN the verification system tests column 13 (day_30_price), THE Verification_System SHALL validate that day 30 prices are positive decimals or "N/A"
14. WHEN the verification system tests column 14 (day_30_roi), THE Verification_System SHALL validate that day 30 ROI equals (day_30_price / initial_price) or "N/A"
15. WHEN the verification system tests column 15 (days_to_ath), THE Verification_System SHALL validate that days to ATH are positive integers less than or equal to days_tracked
16. WHEN the verification system tests column 16 (ath_timestamp), THE Verification_System SHALL validate that ATH timestamps are valid ISO 8601 format strings
17. WHEN the verification system tests column 17 (trajectory), THE Verification_System SHALL validate that trajectory is "improved", "crashed", or "stable"
18. WHEN the verification system tests column 18 (peak_timing), THE Verification_System SHALL validate that timing is "early_peaker", "late_peaker", or "N/A"
19. WHEN the verification system tests column 19 (final_roi), THE Verification_System SHALL validate that final ROI is populated only when tracking_status is "completed"

### Requirement 3: OUTCOMES Table Column Verification

**User Story:** As a trading analyst, I want every column in the OUTCOMES table to be individually verified, so that I can accurately assess final trading results.

#### Acceptance Criteria

1. WHEN the verification system tests column 1 (coin_symbol), THE Verification_System SHALL validate that symbols match corresponding PERFORMANCE table entries
2. WHEN the verification system tests column 2 (contract_address), THE Verification_System SHALL validate that addresses match corresponding PERFORMANCE table entries
3. WHEN the verification system tests column 3 (channel_name), THE Verification_System SHALL validate that channel names match corresponding MESSAGES table entries
4. WHEN the verification system tests column 4 (signal_date), THE Verification_System SHALL validate that dates match corresponding MESSAGES table timestamps
5. WHEN the verification system tests column 5 (initial_price), THE Verification_System SHALL validate that prices match corresponding PERFORMANCE table entries
6. WHEN the verification system tests column 6 (final_price), THE Verification_System SHALL validate that final prices are positive decimals
7. WHEN the verification system tests column 7 (ath_price), THE Verification_System SHALL validate that ATH prices match corresponding PERFORMANCE table entries
8. WHEN the verification system tests column 8 (final_roi), THE Verification_System SHALL validate that final ROI equals (final_price / initial_price)
9. WHEN the verification system tests column 9 (ath_roi), THE Verification_System SHALL validate that ATH ROI matches corresponding PERFORMANCE table entries
10. WHEN the verification system tests column 10 (days_to_ath), THE Verification_System SHALL validate that days to ATH match corresponding PERFORMANCE table entries
11. WHEN the verification system tests column 11 (outcome_classification), THE Verification_System SHALL validate that classification is "win", "loss", or "neutral"
12. WHEN the verification system tests column 12 (trajectory), THE Verification_System SHALL validate that trajectory matches corresponding PERFORMANCE table entries
13. WHEN the verification system tests column 13 (peak_timing), THE Verification_System SHALL validate that timing matches corresponding PERFORMANCE table entries
14. WHEN the verification system tests column 14 (tracking_duration), THE Verification_System SHALL validate that duration equals days_tracked from PERFORMANCE table
15. WHEN the verification system tests column 15 (completion_timestamp), THE Verification_System SHALL validate that timestamps are valid ISO 8601 format strings

### Requirement 4: CHANNEL_REPUTATION Table Column Verification

**User Story:** As a channel analyst, I want every column in the CHANNEL_REPUTATION table to be individually verified, so that I can accurately assess channel quality.

#### Acceptance Criteria

1. WHEN the verification system tests column 1 (channel_name), THE Verification_System SHALL validate that channel names are unique identifiers
2. WHEN the verification system tests column 2 (total_signals), THE Verification_System SHALL validate that counts equal the number of OUTCOMES entries for that channel
3. WHEN the verification system tests column 3 (completed_signals), THE Verification_System SHALL validate that counts are less than or equal to total_signals
4. WHEN the verification system tests column 4 (wins), THE Verification_System SHALL validate that win counts match OUTCOMES entries with "win" classification
5. WHEN the verification system tests column 5 (losses), THE Verification_System SHALL validate that loss counts match OUTCOMES entries with "loss" classification
6. WHEN the verification system tests column 6 (win_rate), THE Verification_System SHALL validate that win rate equals (wins / completed_signals \* 100)
7. WHEN the verification system tests column 7 (avg_roi), THE Verification_System SHALL validate that average ROI equals mean of final_roi from OUTCOMES
8. WHEN the verification system tests column 8 (avg_ath_roi), THE Verification_System SHALL validate that average ATH ROI equals mean of ath_roi from OUTCOMES
9. WHEN the verification system tests column 9 (avg_days_to_ath), THE Verification_System SHALL validate that average days equals mean of days_to_ath from OUTCOMES
10. WHEN the verification system tests column 10 (reputation_score), THE Verification_System SHALL validate that scores are decimals between 0.0 and 1.0
11. WHEN the verification system tests column 11 (early_peaker_rate), THE Verification_System SHALL validate that rate equals percentage of "early_peaker" outcomes
12. WHEN the verification system tests column 12 (late_peaker_rate), THE Verification_System SHALL validate that rate equals percentage of "late_peaker" outcomes
13. WHEN the verification system tests column 13 (crash_rate), THE Verification_System SHALL validate that rate equals percentage of "crashed" trajectories
14. WHEN the verification system tests column 14 (last_updated), THE Verification_System SHALL validate that timestamps are within the last 24 hours

### Requirement 5: Remaining Tables Column Verification

**User Story:** As a system administrator, I want every column in MARKET_ANALYSIS, HDRB_SCORES, ACTIVE_TRACKING, and SUMMARY_STATS tables to be individually verified, so that I can ensure complete data integrity.

#### Acceptance Criteria

1. WHEN the verification system tests MARKET_ANALYSIS table columns, THE Verification_System SHALL validate all 12 columns against their data type and range specifications
2. WHEN the verification system tests HDRB_SCORES table columns, THE Verification_System SHALL validate all 10 columns against their calculation formulas
3. WHEN the verification system tests ACTIVE_TRACKING table columns, THE Verification_System SHALL validate all 8 columns against current tracking state
4. WHEN the verification system tests SUMMARY_STATS table columns, THE Verification_System SHALL validate all 18 columns against aggregated source data
5. WHERE any column contains calculated values, THE Verification_System SHALL validate that calculations match documented formulas

### Requirement 6: Data Flow Verification

**User Story:** As a data engineer, I want data flow between components to be verified, so that I can ensure proper synchronization across the system.

#### Acceptance Criteria

1. WHEN a message is processed, THE Verification_System SHALL validate that data flows from MessageProcessor to DataOutput.write_message()
2. WHEN performance is tracked, THE Verification_System SHALL validate that data flows from PerformanceTracker to DataOutput.write_performance()
3. WHEN an outcome is recorded, THE Verification_System SHALL validate that data flows from OutcomeTracker to DataOutput.write_outcome()
4. WHEN channel reputation is updated, THE Verification_System SHALL validate that data flows from ChannelReputation to DataOutput.write_channel_reputation()
5. WHEN SignalOutcome is created, THE Verification_System SHALL validate that time-based fields are synchronized to PerformanceTracker

### Requirement 7: Isolated Unit Test Framework

**User Story:** As a test engineer, I want each table column to have an isolated unit test, so that I can identify exactly which data fields are failing.

#### Acceptance Criteria

1. WHEN the test framework executes, THE Test_Framework SHALL run one unit test per table column
2. WHEN a unit test executes, THE Test_Framework SHALL use predefined test fixtures with known expected values
3. WHEN a unit test fails, THE Test_Framework SHALL report the specific column name, expected value, and actual value
4. WHEN all unit tests complete, THE Test_Framework SHALL generate a detailed report showing pass/fail status for each column
5. WHERE a column depends on another column, THE Test_Framework SHALL mock dependencies to maintain test isolation

### Requirement 8: Integrated End-to-End Test

**User Story:** As a quality assurance engineer, I want a comprehensive end-to-end test that validates the entire system, so that I can verify complete data integrity.

#### Acceptance Criteria

1. WHEN the end-to-end test executes, THE Test_System SHALL process a complete message from input to all output tables
2. WHEN the end-to-end test validates data, THE Test_System SHALL verify data consistency across all 8 tables
3. WHEN the end-to-end test checks calculations, THE Test_System SHALL validate that all derived fields are correctly computed
4. WHEN the end-to-end test completes, THE Test_System SHALL generate a comprehensive report showing system-wide data integrity
5. IF any end-to-end test fails, THEN THE Test_System SHALL identify which component or data flow caused the failure

### Requirement 9: Test Data Fixtures

**User Story:** As a test developer, I want comprehensive test fixtures with known expected outputs, so that I can validate system behavior accurately.

#### Acceptance Criteria

1. WHEN test fixtures are created, THE Test_System SHALL include at least 10 realistic message scenarios
2. WHEN test fixtures define expected outputs, THE Test_System SHALL specify exact values for all 110+ table columns
3. WHEN test fixtures include edge cases, THE Test_System SHALL cover boundary conditions for all numeric fields
4. WHEN test fixtures include error cases, THE Test_System SHALL define expected behavior for invalid inputs
5. WHERE test fixtures require time-based data, THE Test_System SHALL include scenarios for day 7, day 30, and ATH timing

### Requirement 10: Test Execution and Reporting

**User Story:** As a project manager, I want clear test execution reports, so that I can understand system quality and identify issues quickly.

#### Acceptance Criteria

1. WHEN tests execute, THE Test_System SHALL run all unit tests before the integration test
2. WHEN tests complete, THE Test_System SHALL generate a summary report showing total pass/fail counts
3. WHEN tests fail, THE Test_System SHALL generate detailed failure reports with root cause analysis
4. WHEN tests pass, THE Test_System SHALL generate a certification report confirming data integrity
5. WHERE tests are automated, THE Test_System SHALL support continuous integration execution
