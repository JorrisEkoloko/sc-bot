# Design Document

## Overview

The table verification system provides comprehensive validation of all 110+ columns across 8 output tables in the crypto intelligence platform. The design follows a test pyramid approach with isolated unit tests at the base, integration tests in the middle, and a comprehensive end-to-end test at the top.

## Architecture

### Test Hierarchy

```
┌─────────────────────────────────────┐
│   End-to-End Integration Test       │  ← 1 comprehensive test
│   (Full system validation)          │
└─────────────────────────────────────┘
           ▲
           │
┌─────────────────────────────────────┐
│   Component Integration Tests       │  ← 8 table-level tests
│   (Cross-table validation)          │
└─────────────────────────────────────┘
           ▲
           │
┌─────────────────────────────────────┐
│   Isolated Column Unit Tests        │  ← 110+ individual tests
│   (Single column validation)        │
└─────────────────────────────────────┘
```

### Test Isolation Strategy

Each unit test operates in complete isolation:

- Uses mock data for dependencies
- Tests only one column's validation logic
- Has no side effects on other tests
- Can run in any order
- Provides precise failure reporting

## Components and Interfaces

### 1. Test Fixture Manager

**Purpose**: Provides predefined test data with known expected outputs

**Interface**:

```python
class TestFixtureManager:
    def get_message_fixture(scenario: str) -> MessageFixture
    def get_performance_fixture(scenario: str) -> PerformanceFixture
    def get_outcome_fixture(scenario: str) -> OutcomeFixture
    def get_channel_reputation_fixture(scenario: str) -> ChannelReputationFixture
    def get_all_fixtures() -> List[Fixture]
```

**Fixture Scenarios**:

- `basic_ethereum_signal`: Standard Ethereum token signal
- `basic_solana_signal`: Standard Solana token signal
- `early_peaker`: Token that peaks within 7 days
- `late_peaker`: Token that peaks after 7 days
- `crashed_token`: Token that crashes from ATH
- `stable_token`: Token with minimal price movement
- `high_market_cap`: Large cap token
- `micro_cap`: Micro cap token
- `missing_data`: Scenario with N/A values
- `edge_case_values`: Boundary condition testing

### 2. Column Validator

**Purpose**: Validates individual column values against specifications

**Interface**:

```python
class ColumnValidator:
    def validate_message_id(value: Any) -> ValidationResult
    def validate_timestamp(value: Any) -> ValidationResult
    def validate_channel_name(value: Any) -> ValidationResult
    def validate_coin_symbol(value: Any) -> ValidationResult
    def validate_chain(value: Any) -> ValidationResult
    def validate_contract_address(value: Any, chain: str) -> ValidationResult
    def validate_price(value: Any) -> ValidationResult
    def validate_market_cap(value: Any) -> ValidationResult
    def validate_market_cap_tier(value: Any) -> ValidationResult
    def validate_sentiment_score(value: Any) -> ValidationResult
    def validate_hdrb_score(value: Any) -> ValidationResult
    def validate_reputation_score(value: Any) -> ValidationResult
    def validate_win_rate(value: Any) -> ValidationResult
    def validate_roi(value: Any) -> ValidationResult
    def validate_signal_count(value: Any) -> ValidationResult
    def validate_days_tracked(value: Any) -> ValidationResult
    def validate_tracking_status(value: Any) -> ValidationResult
    def validate_trajectory(value: Any) -> ValidationResult
    def validate_peak_timing(value: Any) -> ValidationResult
    def validate_outcome_classification(value: Any) -> ValidationResult
```

**ValidationResult Structure**:

```python
@dataclass
class ValidationResult:
    is_valid: bool
    column_name: str
    expected: Any
    actual: Any
    error_message: Optional[str]
    validation_rule: str
```

### 3. Table Unit Test Suite

**Purpose**: Runs isolated tests for each column in each table

**Interface**:

```python
class TableUnitTestSuite:
    def test_messages_table() -> List[ValidationResult]
    def test_performance_table() -> List[ValidationResult]
    def test_outcomes_table() -> List[ValidationResult]
    def test_channel_reputation_table() -> List[ValidationResult]
    def test_market_analysis_table() -> List[ValidationResult]
    def test_hdrb_scores_table() -> List[ValidationResult]
    def test_active_tracking_table() -> List[ValidationResult]
    def test_summary_stats_table() -> List[ValidationResult]
    def run_all_unit_tests() -> TestReport
```

### 4. Cross-Table Validator

**Purpose**: Validates data consistency across related tables

**Interface**:

```python
class CrossTableValidator:
    def validate_messages_to_performance_sync(
        messages_data: List[Dict],
        performance_data: List[Dict]
    ) -> ValidationResult

    def validate_performance_to_outcomes_sync(
        performance_data: List[Dict],
        outcomes_data: List[Dict]
    ) -> ValidationResult

    def validate_outcomes_to_reputation_sync(
        outcomes_data: List[Dict],
        reputation_data: List[Dict]
    ) -> ValidationResult

    def validate_all_cross_table_relationships() -> List[ValidationResult]
```

### 5. End-to-End Test Orchestrator

**Purpose**: Executes complete system test from message input to all table outputs

**Interface**:

```python
class EndToEndTestOrchestrator:
    def setup_test_environment() -> TestEnvironment
    def inject_test_message(message: TestMessage) -> None
    def wait_for_processing_completion(timeout: int) -> bool
    def collect_all_table_outputs() -> Dict[str, List[Dict]]
    def validate_complete_data_flow() -> EndToEndTestReport
    def teardown_test_environment() -> None
```

### 6. Test Reporter

**Purpose**: Generates comprehensive test reports

**Interface**:

```python
class TestReporter:
    def generate_unit_test_report(results: List[ValidationResult]) -> str
    def generate_integration_test_report(results: List[ValidationResult]) -> str
    def generate_end_to_end_report(results: EndToEndTestReport) -> str
    def generate_summary_report(all_results: Dict[str, Any]) -> str
    def export_to_json(report: Any, filepath: str) -> None
    def export_to_html(report: Any, filepath: str) -> None
```

## Data Models

### Test Fixtures

```python
@dataclass
class MessageFixture:
    message_id: int
    timestamp: str
    channel_name: str
    message_text: str
    coin_symbol: str
    chain: str
    contract_address: str
    initial_price: float
    initial_market_cap: Union[int, str]
    market_cap_tier: str
    sentiment_score: float
    hdrb_score: float
    channel_reputation: float
    channel_win_rate: float
    channel_avg_roi: float
    channel_total_signals: int

@dataclass
class PerformanceFixture:
    coin_symbol: str
    contract_address: str
    initial_price: float
    current_price: float
    ath_price: float
    current_roi: float
    ath_roi: float
    days_tracked: int
    last_updated: str
    tracking_status: str
    day_7_price: Union[float, str]
    day_7_roi: Union[float, str]
    day_30_price: Union[float, str]
    day_30_roi: Union[float, str]
    days_to_ath: int
    ath_timestamp: str
    trajectory: str
    peak_timing: str
    final_roi: Union[float, str]

@dataclass
class OutcomeFixture:
    coin_symbol: str
    contract_address: str
    channel_name: str
    signal_date: str
    initial_price: float
    final_price: float
    ath_price: float
    final_roi: float
    ath_roi: float
    days_to_ath: int
    outcome_classification: str
    trajectory: str
    peak_timing: str
    tracking_duration: int
    completion_timestamp: str

@dataclass
class ChannelReputationFixture:
    channel_name: str
    total_signals: int
    completed_signals: int
    wins: int
    losses: int
    win_rate: float
    avg_roi: float
    avg_ath_roi: float
    avg_days_to_ath: float
    reputation_score: float
    early_peaker_rate: float
    late_peaker_rate: float
    crash_rate: float
    last_updated: str
```

### Test Reports

```python
@dataclass
class TestReport:
    test_type: str  # "unit", "integration", "end_to_end"
    total_tests: int
    passed: int
    failed: int
    skipped: int
    execution_time: float
    results: List[ValidationResult]
    summary: str

@dataclass
class EndToEndTestReport:
    scenario_name: str
    message_processed: bool
    tables_updated: Dict[str, bool]
    data_consistency_checks: List[ValidationResult]
    calculation_validations: List[ValidationResult]
    overall_status: str  # "PASS", "FAIL", "PARTIAL"
    failure_points: List[str]
    execution_time: float
```

## Error Handling

### Validation Error Types

1. **Type Mismatch**: Value is wrong data type
2. **Range Violation**: Value outside acceptable range
3. **Format Error**: Value doesn't match required format
4. **Consistency Error**: Value inconsistent with related data
5. **Missing Data**: Required value is None or empty
6. **Calculation Error**: Derived value doesn't match formula

### Error Reporting Strategy

- Each validation error includes:
  - Column name and table
  - Expected value/range
  - Actual value
  - Validation rule violated
  - Suggested fix (when applicable)

### Test Failure Handling

- Unit test failures don't block other unit tests
- Integration test failures are logged with context
- End-to-end test failures trigger detailed diagnostic collection
- All failures are aggregated in final report

## Testing Strategy

### Phase 1: Isolated Unit Tests (110+ tests)

**Execution Order**: Can run in parallel or any order

**Test Structure**:

```python
def test_messages_column_01_message_id():
    # Arrange
    fixture = TestFixtureManager.get_message_fixture("basic_ethereum_signal")
    validator = ColumnValidator()

    # Act
    result = validator.validate_message_id(fixture.message_id)

    # Assert
    assert result.is_valid == True
    assert result.actual > 0
    assert isinstance(result.actual, int)
```

**Coverage**:

- MESSAGES table: 16 column tests
- PERFORMANCE table: 19 column tests
- OUTCOMES table: 15 column tests
- CHANNEL_REPUTATION table: 14 column tests
- MARKET_ANALYSIS table: 12 column tests
- HDRB_SCORES table: 10 column tests
- ACTIVE_TRACKING table: 8 column tests
- SUMMARY_STATS table: 18 column tests

### Phase 2: Integration Tests (8 tests)

**Execution Order**: Sequential, after unit tests pass

**Test Structure**:

```python
def test_messages_to_performance_integration():
    # Arrange
    message_fixture = TestFixtureManager.get_message_fixture("basic_ethereum_signal")
    performance_fixture = TestFixtureManager.get_performance_fixture("basic_ethereum_signal")
    validator = CrossTableValidator()

    # Act
    result = validator.validate_messages_to_performance_sync(
        [message_fixture.to_dict()],
        [performance_fixture.to_dict()]
    )

    # Assert
    assert result.is_valid == True
    assert message_fixture.coin_symbol == performance_fixture.coin_symbol
    assert message_fixture.contract_address == performance_fixture.contract_address
```

**Coverage**:

- MESSAGES → PERFORMANCE synchronization
- PERFORMANCE → OUTCOMES synchronization
- OUTCOMES → CHANNEL_REPUTATION aggregation
- Cross-table calculation consistency
- Time-based field synchronization

### Phase 3: End-to-End Test (1 comprehensive test)

**Execution Order**: Final test, after all others pass

**Test Structure**:

```python
def test_complete_system_data_flow():
    # Arrange
    orchestrator = EndToEndTestOrchestrator()
    test_env = orchestrator.setup_test_environment()
    test_message = TestFixtureManager.get_message_fixture("basic_ethereum_signal")

    # Act
    orchestrator.inject_test_message(test_message)
    processing_complete = orchestrator.wait_for_processing_completion(timeout=300)
    all_outputs = orchestrator.collect_all_table_outputs()

    # Assert
    assert processing_complete == True
    assert len(all_outputs["messages"]) == 1
    assert len(all_outputs["performance"]) == 1

    # Validate complete data flow
    report = orchestrator.validate_complete_data_flow()
    assert report.overall_status == "PASS"

    # Cleanup
    orchestrator.teardown_test_environment()
```

**Coverage**:

- Complete message processing pipeline
- All 8 tables populated correctly
- All calculations accurate
- All cross-table relationships valid
- System performance within acceptable limits

## Test Execution Flow

```
1. Load Test Fixtures
   ↓
2. Run Unit Tests (parallel)
   ├─ MESSAGES table (16 tests)
   ├─ PERFORMANCE table (19 tests)
   ├─ OUTCOMES table (15 tests)
   ├─ CHANNEL_REPUTATION table (14 tests)
   ├─ MARKET_ANALYSIS table (12 tests)
   ├─ HDRB_SCORES table (10 tests)
   ├─ ACTIVE_TRACKING table (8 tests)
   └─ SUMMARY_STATS table (18 tests)
   ↓
3. Generate Unit Test Report
   ↓
4. Run Integration Tests (sequential)
   ├─ MESSAGES ↔ PERFORMANCE
   ├─ PERFORMANCE ↔ OUTCOMES
   ├─ OUTCOMES ↔ CHANNEL_REPUTATION
   └─ Cross-table calculations
   ↓
5. Generate Integration Test Report
   ↓
6. Run End-to-End Test
   ├─ Setup test environment
   ├─ Inject test message
   ├─ Wait for processing
   ├─ Collect all outputs
   ├─ Validate complete flow
   └─ Teardown environment
   ↓
7. Generate End-to-End Report
   ↓
8. Generate Summary Report
   ↓
9. Export Reports (JSON + HTML)
```

## Performance Considerations

- Unit tests should complete in < 1 second each
- Integration tests should complete in < 5 seconds each
- End-to-end test should complete in < 5 minutes
- Total test suite execution: < 10 minutes
- Parallel execution of unit tests for speed
- Minimal test data to reduce overhead
- Mock external API calls
- Use in-memory data structures

## Validation Rules Reference

### Data Type Rules

- **Integer**: Whole numbers only, no decimals
- **Float**: Decimal numbers with precision
- **String**: Text values, properly escaped
- **ISO 8601**: YYYY-MM-DDTHH:MM:SSZ format
- **Enum**: One of predefined values

### Range Rules

- **Positive**: > 0
- **Non-negative**: >= 0
- **Percentage**: 0.0 to 100.0
- **Score**: 0.0 to 1.0
- **Sentiment**: -1.0 to 1.0
- **Days**: 0 to 30

### Format Rules

- **Ethereum Address**: 0x followed by 40 hex characters
- **Solana Address**: 32-44 base58 characters
- **Coin Symbol**: Uppercase alphanumeric
- **Channel Name**: Configured identifier

### Calculation Rules

- **ROI**: current_price / initial_price
- **Win Rate**: (wins / completed_signals) \* 100
- **Average**: sum(values) / count(values)
- **Percentage**: (count / total) \* 100

## Continuous Integration Support

The test suite integrates with CI/CD pipelines:

```yaml
# Example CI configuration
test:
  script:
    - python -m pytest tests/unit/ --parallel
    - python -m pytest tests/integration/ --sequential
    - python -m pytest tests/e2e/ --verbose
  artifacts:
    reports:
      - test_reports/*.json
      - test_reports/*.html
  coverage:
    threshold: 95%
```

## Future Enhancements

1. **Performance Benchmarking**: Track test execution time trends
2. **Mutation Testing**: Verify test quality by introducing bugs
3. **Property-Based Testing**: Generate random valid inputs
4. **Regression Testing**: Compare results against baseline
5. **Load Testing**: Validate with high-volume data
6. **Chaos Testing**: Introduce random failures
