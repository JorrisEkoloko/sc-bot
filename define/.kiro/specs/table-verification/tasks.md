# Implementation Plan

## Overview

This implementation plan breaks down the table verification system into isolated, testable components. Each task focuses on a specific table or column set, ensuring complete test isolation before integration.

- [ ] 1. Create test infrastructure and fixtures
- [ ] 1.1 Create test fixture manager with data models

  - Implement MessageFixture, PerformanceFixture, OutcomeFixture, ChannelReputationFixture dataclasses
  - Create TestFixtureManager class with methods for each fixture scenario
  - Define 10 fixture scenarios: basic_ethereum_signal, basic_solana_signal, early_peaker, late_peaker, crashed_token, stable_token, high_market_cap, micro_cap, missing_data, edge_case_values
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 1.2 Create ValidationResult and TestReport data models

  - Implement ValidationResult dataclass with is_valid, column_name, expected, actual, error_message, validation_rule fields
  - Implement TestReport dataclass with test_type, total_tests, passed, failed, skipped, execution_time, results, summary fields
  - Implement EndToEndTestReport dataclass with scenario_name, message_processed, tables_updated, data_consistency_checks, calculation_validations, overall_status, failure_points, execution_time fields
  - _Requirements: 7.3, 10.2, 10.3_

- [ ] 1.3 Create base ColumnValidator class with validation methods

  - Implement validate_message_id() for unique integers > 0
  - Implement validate_timestamp() for ISO 8601 format validation
  - Implement validate_channel_name() for configured channel identifiers
  - Implement validate_coin_symbol() for uppercase alphanumeric strings
  - Implement validate_chain() for "ethereum" or "solana" enum
  - Implement validate_contract_address() with chain-specific format patterns
  - Implement validate_price() for positive decimal numbers
  - Implement validate_market_cap() for positive integers or "N/A"
  - Implement validate_market_cap_tier() for "micro", "small", or "large" enum
  - Implement validate_sentiment_score() for range -1.0 to 1.0
  - Implement validate_hdrb_score() for range 0.0 to 1.0
  - Implement validate_reputation_score() for range 0.0 to 1.0
  - Implement validate_win_rate() for percentage 0.0 to 100.0
  - Implement validate_roi() for decimal multipliers
  - Implement validate_signal_count() for non-negative integers
  - Implement validate_days_tracked() for integers 0 to 30
  - Implement validate_tracking_status() for "active", "completed", or "failed" enum
  - Implement validate_trajectory() for "improved", "crashed", or "stable" enum
  - Implement validate_peak_timing() for "early_peaker", "late_peaker", or "N/A" enum
  - Implement validate_outcome_classification() for "win", "loss", or "neutral" enum
  - _Requirements: 1.1-1.16, 2.1-2.19, 3.1-3.15, 4.1-4.14_

- [ ] 2. Create MESSAGES table unit tests (16 isolated tests)

- [ ] 2.1 Create isolated test for MESSAGES column 1 (message_id)

  - Write test_messages_col_01_message_id() function
  - Load basic_ethereum_signal fixture
  - Validate message_id is unique integer > 0
  - Assert validation passes with correct error reporting
  - _Requirements: 1.1, 7.1, 7.2, 7.3_

- [ ] 2.2 Create isolated test for MESSAGES column 2 (timestamp)

  - Write test_messages_col_02_timestamp() function
  - Load basic_ethereum_signal fixture
  - Validate timestamp is ISO 8601 format
  - Assert validation passes with correct error reporting
  - _Requirements: 1.2, 7.1, 7.2, 7.3_

- [ ] 2.3 Create isolated test for MESSAGES column 3 (channel_name)

  - Write test_messages_col_03_channel_name() function
  - Load basic_ethereum_signal fixture
  - Validate channel_name matches configured identifiers
  - Assert validation passes with correct error reporting
  - _Requirements: 1.3, 7.1, 7.2, 7.3_

- [ ] 2.4 Create isolated test for MESSAGES column 4 (message_text)

  - Write test_messages_col_04_message_text() function
  - Load basic_ethereum_signal fixture
  - Validate message_text is non-empty and properly escaped
  - Assert validation passes with correct error reporting
  - _Requirements: 1.4, 7.1, 7.2, 7.3_

- [ ] 2.5 Create isolated test for MESSAGES column 5 (coin_symbol)

  - Write test_messages_col_05_coin_symbol() function
  - Load basic_ethereum_signal fixture
  - Validate coin_symbol is uppercase alphanumeric
  - Assert validation passes with correct error reporting
  - _Requirements: 1.5, 7.1, 7.2, 7.3_

- [ ] 2.6 Create isolated test for MESSAGES column 6 (chain)

  - Write test_messages_col_06_chain() function
  - Load basic_ethereum_signal and basic_solana_signal fixtures
  - Validate chain is "ethereum" or "solana"
  - Assert validation passes with correct error reporting
  - _Requirements: 1.6, 7.1, 7.2, 7.3_

- [ ] 2.7 Create isolated test for MESSAGES column 7 (contract_address)

  - Write test_messages_col_07_contract_address() function
  - Load basic_ethereum_signal and basic_solana_signal fixtures
  - Validate address matches chain-specific format patterns
  - Assert validation passes with correct error reporting
  - _Requirements: 1.7, 7.1, 7.2, 7.3_

- [ ] 2.8 Create isolated test for MESSAGES column 8 (initial_price)

  - Write test_messages_col_08_initial_price() function
  - Load basic_ethereum_signal fixture
  - Validate price is positive decimal with proper precision
  - Assert validation passes with correct error reporting
  - _Requirements: 1.8, 7.1, 7.2, 7.3_

- [ ] 2.9 Create isolated test for MESSAGES column 9 (initial_market_cap)

  - Write test_messages_col_09_initial_market_cap() function
  - Load high_market_cap and missing_data fixtures
  - Validate market_cap is positive integer or "N/A"
  - Assert validation passes with correct error reporting
  - _Requirements: 1.9, 7.1, 7.2, 7.3_

- [ ] 2.10 Create isolated test for MESSAGES column 10 (market_cap_tier)

  - Write test_messages_col_10_market_cap_tier() function
  - Load micro_cap, high_market_cap fixtures
  - Validate tier is "micro", "small", or "large"
  - Assert validation passes with correct error reporting
  - _Requirements: 1.10, 7.1, 7.2, 7.3_

- [ ] 2.11 Create isolated test for MESSAGES column 11 (sentiment_score)

  - Write test_messages_col_11_sentiment_score() function
  - Load basic_ethereum_signal and edge_case_values fixtures
  - Validate score is decimal between -1.0 and 1.0
  - Assert validation passes with correct error reporting
  - _Requirements: 1.11, 7.1, 7.2, 7.3_

- [ ] 2.12 Create isolated test for MESSAGES column 12 (hdrb_score)

  - Write test_messages_col_12_hdrb_score() function
  - Load basic_ethereum_signal and edge_case_values fixtures
  - Validate score is decimal between 0.0 and 1.0
  - Assert validation passes with correct error reporting
  - _Requirements: 1.12, 7.1, 7.2, 7.3_

- [ ] 2.13 Create isolated test for MESSAGES column 13 (channel_reputation)

  - Write test_messages_col_13_channel_reputation() function
  - Load basic_ethereum_signal and edge_case_values fixtures
  - Validate reputation is decimal between 0.0 and 1.0
  - Assert validation passes with correct error reporting
  - _Requirements: 1.13, 7.1, 7.2, 7.3_

- [ ] 2.14 Create isolated test for MESSAGES column 14 (channel_win_rate)

  - Write test_messages_col_14_channel_win_rate() function
  - Load basic_ethereum_signal and edge_case_values fixtures
  - Validate win_rate is percentage between 0.0 and 100.0
  - Assert validation passes with correct error reporting
  - _Requirements: 1.14, 7.1, 7.2, 7.3_

- [ ] 2.15 Create isolated test for MESSAGES column 15 (channel_avg_roi)

  - Write test_messages_col_15_channel_avg_roi() function
  - Load basic_ethereum_signal fixture
  - Validate avg_roi is decimal multiplier
  - Assert validation passes with correct error reporting
  - _Requirements: 1.15, 7.1, 7.2, 7.3_

- [ ] 2.16 Create isolated test for MESSAGES column 16 (channel_total_signals)

  - Write test_messages_col_16_channel_total_signals() function
  - Load basic_ethereum_signal fixture
  - Validate signal_count is non-negative integer
  - Assert validation passes with correct error reporting
  - _Requirements: 1.16, 7.1, 7.2, 7.3_

- [ ] 3. Create PERFORMANCE table unit tests (19 isolated tests)
- [ ] 3.1 Create isolated test for PERFORMANCE column 1 (coin_symbol)

  - Write test_performance_col_01_coin_symbol() function
  - Load basic_ethereum_signal fixture
  - Validate coin_symbol matches MESSAGES table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 2.1, 7.1, 7.2, 7.3_

- [ ] 3.2 Create isolated test for PERFORMANCE column 2 (contract_address)

  - Write test_performance_col_02_contract_address() function
  - Load basic_ethereum_signal fixture
  - Validate contract_address matches MESSAGES table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 2.2, 7.1, 7.2, 7.3_

- [ ] 3.3 Create isolated test for PERFORMANCE column 3 (initial_price)

  - Write test_performance_col_03_initial_price() function
  - Load basic_ethereum_signal fixture
  - Validate initial_price matches MESSAGES table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 2.3, 7.1, 7.2, 7.3_

- [ ] 3.4 Create isolated test for PERFORMANCE column 4 (current_price)

  - Write test_performance_col_04_current_price() function
  - Load basic_ethereum_signal fixture
  - Validate current_price is positive decimal updated within 2 hours
  - Assert validation passes with correct error reporting
  - _Requirements: 2.4, 7.1, 7.2, 7.3_

- [ ] 3.5 Create isolated test for PERFORMANCE column 5 (ath_price)

  - Write test_performance_col_05_ath_price() function
  - Load early_peaker fixture
  - Validate ath_price >= initial_price
  - Assert validation passes with correct error reporting
  - _Requirements: 2.5, 7.1, 7.2, 7.3_

- [ ] 3.6 Create isolated test for PERFORMANCE column 6 (current_roi)

  - Write test_performance_col_06_current_roi() function
  - Load basic_ethereum_signal fixture
  - Validate current_roi = current_price / initial_price
  - Assert validation passes with correct error reporting
  - _Requirements: 2.6, 7.1, 7.2, 7.3_

- [ ] 3.7 Create isolated test for PERFORMANCE column 7 (ath_roi)

  - Write test_performance_col_07_ath_roi() function
  - Load early_peaker fixture
  - Validate ath_roi = ath_price / initial_price
  - Assert validation passes with correct error reporting
  - _Requirements: 2.7, 7.1, 7.2, 7.3_

- [ ] 3.8 Create isolated test for PERFORMANCE column 8 (days_tracked)

  - Write test_performance_col_08_days_tracked() function
  - Load basic_ethereum_signal and edge_case_values fixtures
  - Validate days_tracked is integer 0-30
  - Assert validation passes with correct error reporting
  - _Requirements: 2.8, 7.1, 7.2, 7.3_

- [ ] 3.9 Create isolated test for PERFORMANCE column 9 (last_updated)

  - Write test_performance_col_09_last_updated() function
  - Load basic_ethereum_signal fixture
  - Validate last_updated is within last 2 hours
  - Assert validation passes with correct error reporting
  - _Requirements: 2.9, 7.1, 7.2, 7.3_

- [ ] 3.10 Create isolated test for PERFORMANCE column 10 (tracking_status)

  - Write test_performance_col_10_tracking_status() function
  - Load basic_ethereum_signal fixture
  - Validate status is "active", "completed", or "failed"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.10, 7.1, 7.2, 7.3_

- [ ] 3.11 Create isolated test for PERFORMANCE column 11 (day_7_price)

  - Write test_performance_col_11_day_7_price() function
  - Load early_peaker and missing_data fixtures
  - Validate day_7_price is positive decimal or "N/A"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.11, 7.1, 7.2, 7.3_

- [ ] 3.12 Create isolated test for PERFORMANCE column 12 (day_7_roi)

  - Write test_performance_col_12_day_7_roi() function
  - Load early_peaker and missing_data fixtures
  - Validate day_7_roi = day_7_price / initial_price or "N/A"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.12, 7.1, 7.2, 7.3_

- [ ] 3.13 Create isolated test for PERFORMANCE column 13 (day_30_price)

  - Write test_performance_col_13_day_30_price() function
  - Load late_peaker and missing_data fixtures
  - Validate day_30_price is positive decimal or "N/A"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.13, 7.1, 7.2, 7.3_

- [ ] 3.14 Create isolated test for PERFORMANCE column 14 (day_30_roi)

  - Write test_performance_col_14_day_30_roi() function
  - Load late_peaker and missing_data fixtures
  - Validate day_30_roi = day_30_price / initial_price or "N/A"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.14, 7.1, 7.2, 7.3_

- [ ] 3.15 Create isolated test for PERFORMANCE column 15 (days_to_ath)

  - Write test_performance_col_15_days_to_ath() function
  - Load early_peaker and late_peaker fixtures
  - Validate days_to_ath <= days_tracked
  - Assert validation passes with correct error reporting
  - _Requirements: 2.15, 7.1, 7.2, 7.3_

- [ ] 3.16 Create isolated test for PERFORMANCE column 16 (ath_timestamp)

  - Write test_performance_col_16_ath_timestamp() function
  - Load early_peaker fixture
  - Validate ath_timestamp is ISO 8601 format
  - Assert validation passes with correct error reporting
  - _Requirements: 2.16, 7.1, 7.2, 7.3_

- [ ] 3.17 Create isolated test for PERFORMANCE column 17 (trajectory)

  - Write test_performance_col_17_trajectory() function
  - Load crashed_token, stable_token fixtures
  - Validate trajectory is "improved", "crashed", or "stable"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.17, 7.1, 7.2, 7.3_

- [ ] 3.18 Create isolated test for PERFORMANCE column 18 (peak_timing)

  - Write test_performance_col_18_peak_timing() function
  - Load early_peaker, late_peaker, missing_data fixtures
  - Validate peak_timing is "early_peaker", "late_peaker", or "N/A"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.18, 7.1, 7.2, 7.3_

- [ ] 3.19 Create isolated test for PERFORMANCE column 19 (final_roi)

  - Write test_performance_col_19_final_roi() function
  - Load basic_ethereum_signal fixture with completed status
  - Validate final_roi is populated only when tracking_status is "completed"
  - Assert validation passes with correct error reporting
  - _Requirements: 2.19, 7.1, 7.2, 7.3_

- [ ] 4. Create OUTCOMES table unit tests (15 isolated tests)

- [ ] 4.1 Create isolated test for OUTCOMES column 1 (coin_symbol)

  - Write test_outcomes_col_01_coin_symbol() function
  - Load basic_ethereum_signal fixture
  - Validate coin_symbol matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.1, 7.1, 7.2, 7.3_

- [ ] 4.2 Create isolated test for OUTCOMES column 2 (contract_address)

  - Write test_outcomes_col_02_contract_address() function
  - Load basic_ethereum_signal fixture
  - Validate contract_address matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.2, 7.1, 7.2, 7.3_

- [ ] 4.3 Create isolated test for OUTCOMES column 3 (channel_name)

  - Write test_outcomes_col_03_channel_name() function
  - Load basic_ethereum_signal fixture
  - Validate channel_name matches MESSAGES table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.3, 7.1, 7.2, 7.3_

- [ ] 4.4 Create isolated test for OUTCOMES column 4 (signal_date)

  - Write test_outcomes_col_04_signal_date() function
  - Load basic_ethereum_signal fixture
  - Validate signal_date matches MESSAGES table timestamp
  - Assert validation passes with correct error reporting
  - _Requirements: 3.4, 7.1, 7.2, 7.3_

- [ ] 4.5 Create isolated test for OUTCOMES column 5 (initial_price)

  - Write test_outcomes_col_05_initial_price() function
  - Load basic_ethereum_signal fixture
  - Validate initial_price matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.5, 7.1, 7.2, 7.3_

- [ ] 4.6 Create isolated test for OUTCOMES column 6 (final_price)

  - Write test_outcomes_col_06_final_price() function
  - Load basic_ethereum_signal fixture
  - Validate final_price is positive decimal
  - Assert validation passes with correct error reporting
  - _Requirements: 3.6, 7.1, 7.2, 7.3_

- [ ] 4.7 Create isolated test for OUTCOMES column 7 (ath_price)

  - Write test_outcomes_col_07_ath_price() function
  - Load early_peaker fixture
  - Validate ath_price matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.7, 7.1, 7.2, 7.3_

- [ ] 4.8 Create isolated test for OUTCOMES column 8 (final_roi)

  - Write test_outcomes_col_08_final_roi() function
  - Load basic_ethereum_signal fixture
  - Validate final_roi = final_price / initial_price
  - Assert validation passes with correct error reporting
  - _Requirements: 3.8, 7.1, 7.2, 7.3_

- [ ] 4.9 Create isolated test for OUTCOMES column 9 (ath_roi)

  - Write test_outcomes_col_09_ath_roi() function
  - Load early_peaker fixture
  - Validate ath_roi matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.9, 7.1, 7.2, 7.3_

- [ ] 4.10 Create isolated test for OUTCOMES column 10 (days_to_ath)

  - Write test_outcomes_col_10_days_to_ath() function
  - Load early_peaker fixture
  - Validate days_to_ath matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.10, 7.1, 7.2, 7.3_

- [ ] 4.11 Create isolated test for OUTCOMES column 11 (outcome_classification)

  - Write test_outcomes_col_11_outcome_classification() function
  - Load basic_ethereum_signal fixture
  - Validate classification is "win", "loss", or "neutral"
  - Assert validation passes with correct error reporting
  - _Requirements: 3.11, 7.1, 7.2, 7.3_

- [ ] 4.12 Create isolated test for OUTCOMES column 12 (trajectory)

  - Write test_outcomes_col_12_trajectory() function
  - Load crashed_token fixture
  - Validate trajectory matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.12, 7.1, 7.2, 7.3_

- [ ] 4.13 Create isolated test for OUTCOMES column 13 (peak_timing)

  - Write test_outcomes_col_13_peak_timing() function
  - Load early_peaker, late_peaker fixtures
  - Validate peak_timing matches PERFORMANCE table entry
  - Assert validation passes with correct error reporting
  - _Requirements: 3.13, 7.1, 7.2, 7.3_

- [ ] 4.14 Create isolated test for OUTCOMES column 14 (tracking_duration)

  - Write test_outcomes_col_14_tracking_duration() function
  - Load basic_ethereum_signal fixture
  - Validate tracking_duration equals days_tracked from PERFORMANCE
  - Assert validation passes with correct error reporting
  - _Requirements: 3.14, 7.1, 7.2, 7.3_

- [ ] 4.15 Create isolated test for OUTCOMES column 15 (completion_timestamp)

  - Write test_outcomes_col_15_completion_timestamp() function
  - Load basic_ethereum_signal fixture
  - Validate completion_timestamp is ISO 8601 format
  - Assert validation passes with correct error reporting
  - _Requirements: 3.15, 7.1, 7.2, 7.3_

- [ ] 5. Create CHANNEL_REPUTATION table unit tests (14 isolated tests)
- [ ] 5.1 Create isolated test for CHANNEL_REPUTATION column 1 (channel_name)

  - Write test_channel_reputation_col_01_channel_name() function
  - Load basic_ethereum_signal fixture
  - Validate channel_name is unique identifier
  - Assert validation passes with correct error reporting
  - _Requirements: 4.1, 7.1, 7.2, 7.3_

- [ ] 5.2 Create isolated test for CHANNEL_REPUTATION column 2 (total_signals)

  - Write test_channel_reputation_col_02_total_signals() function
  - Load basic_ethereum_signal fixture
  - Validate total_signals equals count of OUTCOMES entries
  - Assert validation passes with correct error reporting
  - _Requirements: 4.2, 7.1, 7.2, 7.3_

- [ ] 5.3 Create isolated test for CHANNEL_REPUTATION column 3 (completed_signals)

  - Write test_channel_reputation_col_03_completed_signals() function
  - Load basic_ethereum_signal fixture
  - Validate completed_signals <= total_signals
  - Assert validation passes with correct error reporting
  - _Requirements: 4.3, 7.1, 7.2, 7.3_

- [ ] 5.4 Create isolated test for CHANNEL_REPUTATION column 4 (wins)

  - Write test_channel_reputation_col_04_wins() function
  - Load basic_ethereum_signal fixture
  - Validate wins match OUTCOMES "win" classification count
  - Assert validation passes with correct error reporting
  - _Requirements: 4.4, 7.1, 7.2, 7.3_

- [ ] 5.5 Create isolated test for CHANNEL_REPUTATION column 5 (losses)

  - Write test_channel_reputation_col_05_losses() function
  - Load basic_ethereum_signal fixture
  - Validate losses match OUTCOMES "loss" classification count
  - Assert validation passes with correct error reporting
  - _Requirements: 4.5, 7.1, 7.2, 7.3_

- [ ] 5.6 Create isolated test for CHANNEL_REPUTATION column 6 (win_rate)

  - Write test_channel_reputation_col_06_win_rate() function
  - Load basic_ethereum_signal fixture
  - Validate win_rate = (wins / completed_signals \* 100)
  - Assert validation passes with correct error reporting
  - _Requirements: 4.6, 7.1, 7.2, 7.3_

- [ ] 5.7 Create isolated test for CHANNEL_REPUTATION column 7 (avg_roi)

  - Write test_channel_reputation_col_07_avg_roi() function
  - Load basic_ethereum_signal fixture
  - Validate avg_roi equals mean of final_roi from OUTCOMES
  - Assert validation passes with correct error reporting
  - _Requirements: 4.7, 7.1, 7.2, 7.3_

- [ ] 5.8 Create isolated test for CHANNEL_REPUTATION column 8 (avg_ath_roi)

  - Write test_channel_reputation_col_08_avg_ath_roi() function
  - Load early_peaker fixture
  - Validate avg_ath_roi equals mean of ath_roi from OUTCOMES
  - Assert validation passes with correct error reporting
  - _Requirements: 4.8, 7.1, 7.2, 7.3_

- [ ] 5.9 Create isolated test for CHANNEL_REPUTATION column 9 (avg_days_to_ath)

  - Write test_channel_reputation_col_09_avg_days_to_ath() function
  - Load early_peaker fixture
  - Validate avg_days_to_ath equals mean of days_to_ath from OUTCOMES
  - Assert validation passes with correct error reporting
  - _Requirements: 4.9, 7.1, 7.2, 7.3_

- [ ] 5.10 Create isolated test for CHANNEL_REPUTATION column 10 (reputation_score)

  - Write test_channel_reputation_col_10_reputation_score() function
  - Load basic_ethereum_signal fixture
  - Validate reputation_score is decimal between 0.0 and 1.0
  - Assert validation passes with correct error reporting
  - _Requirements: 4.10, 7.1, 7.2, 7.3_

- [ ] 5.11 Create isolated test for CHANNEL_REPUTATION column 11 (early_peaker_rate)

  - Write test_channel_reputation_col_11_early_peaker_rate() function
  - Load early_peaker fixture
  - Validate early_peaker_rate equals percentage of "early_peaker" outcomes
  - Assert validation passes with correct error reporting
  - _Requirements: 4.11, 7.1, 7.2, 7.3_

- [ ] 5.12 Create isolated test for CHANNEL_REPUTATION column 12 (late_peaker_rate)

  - Write test_channel_reputation_col_12_late_peaker_rate() function
  - Load late_peaker fixture
  - Validate late_peaker_rate equals percentage of "late_peaker" outcomes
  - Assert validation passes with correct error reporting
  - _Requirements: 4.12, 7.1, 7.2, 7.3_

- [ ] 5.13 Create isolated test for CHANNEL_REPUTATION column 13 (crash_rate)

  - Write test_channel_reputation_col_13_crash_rate() function
  - Load crashed_token fixture
  - Validate crash_rate equals percentage of "crashed" trajectories
  - Assert validation passes with correct error reporting
  - _Requirements: 4.13, 7.1, 7.2, 7.3_

- [ ] 5.14 Create isolated test for CHANNEL_REPUTATION column 14 (last_updated)

  - Write test_channel_reputation_col_14_last_updated() function
  - Load basic_ethereum_signal fixture
  - Validate last_updated is within last 24 hours
  - Assert validation passes with correct error reporting
  - _Requirements: 4.14, 7.1, 7.2, 7.3_

- [ ] 6. Create remaining table unit tests (48 isolated tests)
- [ ] 6.1 Create MARKET_ANALYSIS table unit tests (12 tests)

  - Write test functions for all 12 MARKET_ANALYSIS columns
  - Validate each column against data type and range specifications
  - Use appropriate fixtures for each test
  - Assert validation passes with correct error reporting
  - _Requirements: 5.1, 7.1, 7.2, 7.3_

- [ ] 6.2 Create HDRB_SCORES table unit tests (10 tests)

  - Write test functions for all 10 HDRB_SCORES columns
  - Validate each column against calculation formulas
  - Use appropriate fixtures for each test
  - Assert validation passes with correct error reporting
  - _Requirements: 5.2, 7.1, 7.2, 7.3_

- [ ] 6.3 Create ACTIVE_TRACKING table unit tests (8 tests)

  - Write test functions for all 8 ACTIVE_TRACKING columns
  - Validate each column against current tracking state
  - Use appropriate fixtures for each test
  - Assert validation passes with correct error reporting
  - _Requirements: 5.3, 7.1, 7.2, 7.3_

- [ ] 6.4 Create SUMMARY_STATS table unit tests (18 tests)

  - Write test functions for all 18 SUMMARY_STATS columns
  - Validate each column against aggregated source data
  - Use appropriate fixtures for each test
  - Assert validation passes with correct error reporting
  - _Requirements: 5.4, 7.1, 7.2, 7.3_

- [ ] 7. Create cross-table integration tests
- [ ] 7.1 Create MESSAGES to PERFORMANCE synchronization test

  - Write test_messages_to_performance_sync() function
  - Load message and performance fixtures
  - Validate coin_symbol, contract_address, initial_price match across tables
  - Assert synchronization is correct
  - _Requirements: 6.1, 6.2, 7.5_

- [ ] 7.2 Create PERFORMANCE to OUTCOMES synchronization test

  - Write test_performance_to_outcomes_sync() function
  - Load performance and outcome fixtures
  - Validate ath_price, ath_roi, days_to_ath, trajectory, peak_timing match across tables
  - Assert synchronization is correct
  - _Requirements: 6.3, 6.5, 7.5_

- [ ] 7.3 Create OUTCOMES to CHANNEL_REPUTATION aggregation test

  - Write test_outcomes_to_reputation_aggregation() function
  - Load outcome and reputation fixtures
  - Validate total_signals, wins, losses, win_rate, avg_roi calculations
  - Assert aggregation is correct
  - _Requirements: 6.4, 7.5_

- [ ] 7.4 Create cross-table calculation consistency test

  - Write test_cross_table_calculations() function
  - Load all table fixtures
  - Validate ROI calculations are consistent across PERFORMANCE, OUTCOMES, CHANNEL_REPUTATION
  - Assert all calculations match
  - _Requirements: 5.5, 7.5_

- [ ] 7.5 Create time-based field synchronization test

  - Write test_time_based_field_sync() function
  - Load fixtures with day 7, day 30, ATH data
  - Validate timestamp consistency across tables
  - Assert time-based fields are synchronized
  - _Requirements: 6.5, 7.5_

- [ ] 8. Create end-to-end integration test
- [ ] 8.1 Create test environment setup and teardown

  - Write setup_test_environment() function to initialize test database/files
  - Write teardown_test_environment() function to clean up test data
  - Implement test isolation mechanisms
  - _Requirements: 8.1, 8.4_

- [ ] 8.2 Create message injection and processing test

  - Write inject_test_message() function
  - Implement wait_for_processing_completion() with timeout
  - Create collect_all_table_outputs() to gather results
  - _Requirements: 8.1, 8.2_

- [ ] 8.3 Create complete data flow validation

  - Write validate_complete_data_flow() function
  - Validate message appears in MESSAGES table
  - Validate performance tracking in PERFORMANCE table
  - Validate outcome recording in OUTCOMES table
  - Validate reputation update in CHANNEL_REPUTATION table
  - _Requirements: 8.2, 8.3_

- [ ] 8.4 Create end-to-end test orchestration

  - Write test_complete_system_data_flow() function
  - Execute full pipeline from message input to all table outputs
  - Validate all 8 tables are populated correctly
  - Validate all calculations are accurate
  - Generate comprehensive test report
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 9. Create test reporting system
- [ ] 9.1 Create unit test report generator

  - Write generate_unit_test_report() function
  - Include pass/fail counts per table
  - Include detailed failure information with column names
  - Export to JSON and HTML formats
  - _Requirements: 10.2, 10.3_

- [ ] 9.2 Create integration test report generator

  - Write generate_integration_test_report() function
  - Include cross-table validation results
  - Include synchronization check results
  - Export to JSON and HTML formats
  - _Requirements: 10.2, 10.3_

- [ ] 9.3 Create end-to-end test report generator

  - Write generate_end_to_end_report() function
  - Include complete system validation results
  - Include failure point identification
  - Export to JSON and HTML formats
  - _Requirements: 10.2, 10.3, 10.4_

- [ ] 9.4 Create summary report generator

  - Write generate_summary_report() function
  - Aggregate results from all test phases
  - Include overall pass/fail statistics
  - Include execution time metrics
  - Generate certification report for passing tests
  - Export to JSON and HTML formats
  - _Requirements: 10.1, 10.2, 10.4_

- [ ] 10. Create test execution runner
- [ ] 10.1 Create test suite orchestrator

  - Write run_all_tests() function
  - Execute unit tests first (parallel execution)
  - Execute integration tests second (sequential execution)
  - Execute end-to-end test last
  - Generate all reports
  - _Requirements: 10.1, 10.5_

- [ ] 10.2 Create CI/CD integration support
  - Write pytest configuration for test discovery
  - Implement test markers for unit/integration/e2e
  - Create test execution scripts for CI pipelines
  - Configure coverage reporting
  - _Requirements: 10.5_
