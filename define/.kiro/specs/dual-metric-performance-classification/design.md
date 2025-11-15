# Design Document - Time-Based Performance Classification System

## Overview

The time-based performance classification system enhances the crypto intelligence platform by evaluating signals at two critical checkpoints: **Day 7** (short-term) and **Day 30** (long-term). This provides traders with actionable intelligence about optimal exit timing while maintaining fair channel reputation scoring based on peak opportunity (ATH) rather than post-peak crashes.

### The Problem

**Current System**: Single classification at 30-day completion

- Traders don't know if they should exit at day 7 or hold longer
- No visibility into whether peaks come early or late
- Can't distinguish between "peaked early then crashed" vs "peaked late and held"

**The Solution**: Dual checkpoint system

- Day 7: "Should I take profits now?"
- Day 30: "Was my strategy correct?"
- Trajectory: "Did it improve or crash after day 7?"
- Peak timing: "When do this channel's calls typically peak?"

### Core Principle: ATH + Time = Complete Intelligence

**The system tracks**:

1. **ATH (0-30 days)** → Peak opportunity (for channel reputation)
2. **Day 7 price** → Short-term exit decision
3. **Day 30 price** → Long-term outcome
4. **Trajectory** → Performance trend
5. **Peak timing** → When ATH occurred

**The Complete Flow**:

```
Day 0: Entry $1.00
  ↓
Days 1-7: Active tracking (2-hour updates)
  Day 2: ATH $5.00 (5.0x)
  ↓
Day 7: Checkpoint
  ATH: $5.00 (5.0x)
  Current: $2.00 (2.0x)
  Classification: MOON 🌙
  Decision: "Take profits or hold?"
  ↓
Days 8-30: OHLC monitoring (daily checks)
  Day 15: ATH $8.00 (8.0x) ← New peak!
  ↓
Day 30: Final checkpoint
  ATH: $8.00 (8.0x)
  Final: $1.00 (1.0x)
  Classification: MOON 🌙
  Trajectory: Crashed (2.0x → 1.0x)
  Insight: "Peak came late (day 15), but crashed by day 30"
```

## Architecture

### System Components

```
crypto-intelligence/
├── domain/
│   └── signal_outcome.py          # MODIFIED: Add time-based fields
├── utils/
│   └── roi_calculator.py          # MODIFIED: Add trajectory analysis
├── services/
│   ├── tracking/
│   │   ├── performance_tracker.py # MODIFIED: Extend PERFORMANCE columns
│   │   └── outcome_tracker.py     # MODIFIED: Capture checkpoints
│   └── reputation/
│       └── reputation_calculator.py # MODIFIED: Add timing metrics
└── infrastructure/
    └── output/
        └── data_output.py         # MODIFIED: Update PERFORMANCE table
```

### Data Flow

```
Message → Start Tracking (Day 0)
    ↓
Days 1-7: Real-time price updates
    → Update ATH if price exceeds
    → Track continuously
    ↓
Day 7: Checkpoint Event
    → Capture day_7_price from checkpoints["7d"]
    → Classify based on current ATH
    → Store day_7_classification
    → Continue tracking
    ↓
Days 8-30: OHLC monitoring
    → Update ATH from daily highs
    → Track continuously
    ↓
Day 30: Final Checkpoint Event
    → Capture day_30_price from checkpoints["30d"]
    → Classify based on final ATH
    → Store day_30_classification
    → Calculate trajectory
    → Determine peak_timing
    → Stop tracking
    ↓
Output: Complete time-based analysis
```

## Components and Interfaces

### 1. SignalOutcome Data Model (domain/signal_outcome.py)

**Purpose**: Store time-based performance data at both checkpoints.

**New Fields Added**:

```python
@dataclass
class SignalOutcome:
    # ... existing fields ...

    # Time-based performance (NEW)
    day_7_price: float = 0.0           # Price at day 7 checkpoint
    day_7_multiplier: float = 0.0      # ROI at day 7
    day_7_classification: str = ""     # Classification at day 7

    day_30_price: float = 0.0          # Price at day 30 checkpoint
    day_30_multiplier: float = 0.0     # ROI at day 30
    day_30_classification: str = ""    # Final classification

    trajectory: str = ""               # "improved" or "crashed"
    peak_timing: str = ""              # "early_peaker" or "late_peaker"
```

**Integration with Existing Checkpoints**:

```python
# Day 7 data comes from existing checkpoint
day_7_checkpoint = outcome.checkpoints["7d"]
outcome.day_7_price = day_7_checkpoint.price
outcome.day_7_multiplier = day_7_checkpoint.roi_multiplier

# Day 30 data comes from existing checkpoint
day_30_checkpoint = outcome.checkpoints["30d"]
outcome.day_30_price = day_30_checkpoint.price
outcome.day_30_multiplier = day_30_checkpoint.roi_multiplier
```

### 2. ROICalculator Time-Based Methods (utils/roi_calculator.py)

**Purpose**: Calculate trajectory and peak timing analysis.

**New Methods**:

```python
@staticmethod
def analyze_trajectory(day_7_multiplier: float, day_30_multiplier: float) -> Tuple[str, float]:
    """
    Analyze performance trajectory from day 7 to day 30.

    Args:
        day_7_multiplier: ROI multiplier at day 7
        day_30_multiplier: ROI multiplier at day 30

    Returns:
        Tuple[str, float]: (trajectory, crash_severity_percentage)

    Examples:
        >>> analyze_trajectory(2.0, 1.0)
        ("crashed", 50.0)

        >>> analyze_trajectory(2.0, 3.0)
        ("improved", 0.0)
    """
    if day_30_multiplier < day_7_multiplier:
        crash_severity = ((day_7_multiplier - day_30_multiplier) / day_7_multiplier) * 100
        return ("crashed", crash_severity)
    else:
        return ("improved", 0.0)

@staticmethod
def determine_peak_timing(days_to_ath: float) -> str:
    """
    Determine if peak came early or late.

    Args:
        days_to_ath: Days from entry to ATH

    Returns:
        str: "early_peaker" or "late_peaker"
    """
    if days_to_ath <= 7:
        return "early_peaker"
    else:
        return "late_peaker"

@staticmethod
def calculate_optimal_exit_window(days_to_ath: float) -> Tuple[int, int]:
    """
    Calculate optimal exit window around ATH.

    Args:
        days_to_ath: Days from entry to ATH

    Returns:
        Tuple[int, int]: (start_day, end_day) for optimal exit
    """
    start_day = max(0, int(days_to_ath) - 2)
    end_day = int(days_to_ath) + 2
    return (start_day, end_day)
```

### 3. OutcomeTracker Checkpoint Handling (services/tracking/outcome_tracker.py)

**Purpose**: Capture and process day 7 and day 30 checkpoints.

**Modified Methods**:

```python
async def update_price(self, address: str, current_price: float):
    """Update price and check for checkpoint events."""
    # ... existing price update logic ...

    # Check if checkpoints reached
    reached_checkpoints = ROICalculator.check_checkpoints(outcome, current_price)

    # Handle day 7 checkpoint
    if "7d" in reached_checkpoints:
        await self._process_day_7_checkpoint(outcome)

    # Handle day 30 checkpoint
    if "30d" in reached_checkpoints:
        await self._process_day_30_checkpoint(outcome)

async def _process_day_7_checkpoint(self, outcome: SignalOutcome):
    """Process day 7 checkpoint."""
    # Extract from existing checkpoint data
    day_7_checkpoint = outcome.checkpoints["7d"]
    outcome.day_7_price = day_7_checkpoint.price
    outcome.day_7_multiplier = day_7_checkpoint.roi_multiplier

    # Classify based on current ATH
    _, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
    outcome.day_7_classification = category

    self.logger.info(
        f"Day 7 checkpoint: {outcome.symbol} - "
        f"ATH {outcome.ath_multiplier:.2f}x, "
        f"Current {outcome.day_7_multiplier:.2f}x, "
        f"Classification: {category}"
    )

    # Save checkpoint data
    await self.repository.save_outcome(outcome)

async def _process_day_30_checkpoint(self, outcome: SignalOutcome):
    """Process day 30 final checkpoint."""
    # Extract from existing checkpoint data
    day_30_checkpoint = outcome.checkpoints["30d"]
    outcome.day_30_price = day_30_checkpoint.price
    outcome.day_30_multiplier = day_30_checkpoint.roi_multiplier

    # Classify based on final ATH
    _, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
    outcome.day_30_classification = category

    # Analyze trajectory
    trajectory, crash_severity = ROICalculator.analyze_trajectory(
        outcome.day_7_multiplier,
        outcome.day_30_multiplier
    )
    outcome.trajectory = trajectory

    # Determine peak timing
    outcome.peak_timing = ROICalculator.determine_peak_timing(outcome.days_to_ath)

    # Mark as complete
    outcome.is_complete = True
    outcome.status = "completed"
    outcome.completion_reason = "30d_elapsed"

    self.logger.info(
        f"Day 30 final: {outcome.symbol} - "
        f"ATH {outcome.ath_multiplier:.2f}x (day {outcome.days_to_ath:.0f}), "
        f"Final {outcome.day_30_multiplier:.2f}x, "
        f"Trajectory: {trajectory}"
    )

    if trajectory == "crashed" and crash_severity > 50:
        self.logger.warning(
            f"Severe crash: {outcome.symbol} dropped {crash_severity:.0f}% from day 7"
        )

    # Save final outcome
    await self.repository.save_outcome(outcome)
```

### 4. Performance Table Output (infrastructure/output/data_output.py)

**Purpose**: Display time-based performance in CSV and Google Sheets.

**Updated PERFORMANCE_COLUMNS**:

```python
PERFORMANCE_COLUMNS = [
    # Existing (10 columns)
    'address', 'chain', 'first_message_id', 'start_price', 'start_time',
    'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked',

    # NEW: Time-based analysis (8 columns)
    'days_to_ath',           # Speed metric (already exists in outcome)
    'peak_timing',           # "early_peaker" or "late_peaker"
    'day_7_price',           # Price at day 7
    'day_7_multiplier',      # ROI at day 7
    'day_7_classification',  # Category at day 7
    'day_30_price',          # Final price
    'day_30_multiplier',     # Final ROI
    'trajectory'             # "improved" or "crashed"
]
```

**Example CSV Row**:

```csv
5gb4...,solana,12345,1.00,2025-11-10T10:00:00Z,
8.00,2025-11-25T14:00:00Z,8.0,1.0,30,
15.0,late_peaker,2.00,2.0,WINNER,1.00,1.0,crashed
```

**Human-Readable**:

```
Address: 5gb4...
Entry: $1.00
ATH: $8.00 (8.0x) on day 15
Day 7: $2.00 (2.0x) - WINNER
Day 30: $1.00 (1.0x) - MOON
Peak timing: Late peaker (day 15)
Trajectory: Crashed (2.0x → 1.0x)
```

## Real-World Scenarios

### Scenario 1: Early Peaker with Crash (TRUMP Pattern)

```
Day 0: Entry $1.00
Day 1: Price $5.00 → ATH $5.00 (5.0x)
Day 7: Price $2.00 → ATH stays $5.00

📊 Day 7 Checkpoint:
  ATH: 5.0x (day 1)
  Current: 2.0x
  Classification: MOON 🌙
  Peak timing: Early peaker
  Recommendation: "Peaked early, consider taking profits"

Day 15: Price $0.50 → ATH stays $5.00
Day 30: Price $0.03 → ATH stays $5.00

📊 Day 30 Final:
  ATH: 5.0x (day 1) ← Same as day 7
  Final: 0.03x
  Classification: MOON 🌙 ← Channel gets credit!
  Trajectory: Crashed (2.0x → 0.03x = 98.5% drop)
  Peak timing: Early peaker
  Insight: "Peak was day 1, crashed hard after day 7"

Channel Impact:
  ✅ MOON classification (5.0x ATH)
  ✅ Win rate increases
  ✅ Average ROI increases
  ℹ️ Pattern: Early peaker, high crash rate
```

### Scenario 2: Late Peaker with Improvement

```
Day 0: Entry $1.00
Day 2: Price $1.50 → ATH $1.50 (1.5x)
Day 7: Price $1.20 → ATH stays $1.50

📊 Day 7 Checkpoint:
  ATH: 1.5x (day 2)
  Current: 1.2x
  Classification: GOOD 👍
  Peak timing: Early peaker (so far)
  Recommendation: "Modest gains, consider holding"

Day 15: Price $8.00 → ATH $8.00 (8.0x) ← Big spike!
Day 20: Price $7.00 → ATH stays $8.00
Day 30: Price $6.00 → ATH stays $8.00

📊 Day 30 Final:
  ATH: 8.0x (day 15) ← Much higher than day 7!
  Final: 6.0x
  Classification: MOON 🌙 ← Upgraded from GOOD!
  Trajectory: Improved (1.2x → 6.0x = 400% gain)
  Peak timing: Late peaker
  Insight: "Peak came late (day 15), holding paid off!"

Channel Impact:
  ✅ MOON classification (8.0x ATH)
  ✅ Win rate increases
  ✅ Average ROI increases
  ℹ️ Pattern: Late peaker, rewards patience
```

### Scenario 3: Pure Loser (Never Spiked)

```
Day 0: Entry $1.00
Day 2: Price $0.90 → ATH $1.00 (no change)
Day 7: Price $0.70 → ATH stays $1.00

📊 Day 7 Checkpoint:
  ATH: 1.0x (never exceeded entry)
  Current: 0.7x
  Classification: LOSER ❌
  Peak timing: N/A
  Recommendation: "No spike, consider cutting losses"

Day 15: Price $0.60 → ATH stays $1.00
Day 30: Price $0.50 → ATH stays $1.00

📊 Day 30 Final:
  ATH: 1.0x (never spiked)
  Final: 0.5x
  Classification: LOSER ❌
  Trajectory: Crashed (0.7x → 0.5x)
  Peak timing: N/A
  Insight: "Never spiked, only losses"

Channel Impact:
  ❌ LOSER classification
  ❌ Win rate decreases
  ❌ Average ROI decreases
  ❌ Bad call, hurts reputation
```

### Scenario 4: Gradual Grower (Steady Improvement)

```
Day 0: Entry $1.00
Day 3: Price $1.50 → ATH $1.50 (1.5x)
Day 7: Price $1.80 → ATH $1.80 (1.8x)

📊 Day 7 Checkpoint:
  ATH: 1.8x (day 7)
  Current: 1.8x (at ATH)
  Classification: GOOD 👍
  Peak timing: Early peaker (so far)
  Recommendation: "Steady growth, monitor for continuation"

Day 12: Price $2.50 → ATH $2.50 (2.5x)
Day 20: Price $3.00 → ATH $3.00 (3.0x)
Day 30: Price $2.80 → ATH stays $3.00

📊 Day 30 Final:
  ATH: 3.0x (day 20)
  Final: 2.8x
  Classification: WINNER ✅ ← Upgraded!
  Trajectory: Improved (1.8x → 2.8x = 56% gain)
  Peak timing: Late peaker
  Insight: "Steady growth, peak day 20, held value"

Channel Impact:
  ✅ WINNER classification (3.0x ATH)
  ✅ Win rate increases
  ✅ Average ROI increases
  ℹ️ Pattern: Gradual grower, low risk
```

## Data Models

### SignalOutcome JSON Format

```json
{
  "message_id": 12345,
  "channel_name": "Crypto Signals Pro",
  "address": "5gb4...",
  "symbol": "TOKEN",
  "entry_price": 1.00,
  "entry_timestamp": "2025-11-10T10:00:00Z",
  
  "checkpoints": {
    "7d": {
      "timestamp": "2025-11-17T10:00:00Z",
      "price": 2.00,
      "roi_percentage": 100.0,
      "roi_multiplier": 2.0,
      "reached": true
    },
    "30d": {
      "timestamp": "2025-12-10T10:00:00Z",
      "price": 1.00,
      "roi_percentage": 0.0,
      "roi_multiplier": 1.0,
      "reached": true
    }
  },
  
  "ath_price": 8.00,
  "ath_multiplier": 8.0,
  "ath_timestamp": "2025-11-25T14:00:00Z",
  "days_to_ath": 15.0,
  
  "day_7_price": 2.00,
  "day_7_multiplier": 2.0,
  "day_7_classification": "WINNER",
  
  "day_30_price": 1.00,
  "day_30_multiplier": 1.0,
  "day_30_classification": "MOON",
  
  "trajectory": "crashed",
  "peak_timing": "late_peaker",
  
  "is_winner": true,
  "outcome_category": "MOON"
}
```

## Testing Strategy

### Unit Tests

**ROICalculator Tests**:
```python
def test_analyze_trajectory_crashed():
    trajectory, severity = analyze_trajectory(2.0, 1.0)
    assert trajectory == "crashed"
    assert severity == 50.0

def test_analyze_trajectory_improved():
    trajectory, severity = analyze_trajectory(2.0, 3.0)
    assert trajectory == "improved"
    assert severity == 0.0

def test_determine_peak_timing_early():
    timing = determine_peak_timing(5.0)
    assert timing == "early_peaker"

def test_determine_peak_timing_late():
    timing = determine_peak_timing(15.0)
    assert timing == "late_peaker"
```

### Integration Tests

**Complete Flow Test**:
```python
async def test_time_based_classification():
    # Start tracking
    outcome = tracker.track_signal(...)
    
    # Simulate day 7
    await tracker.update_price(address, 2.00)
    # Verify day 7 checkpoint captured
    assert outcome.day_7_price == 2.00
    assert outcome.day_7_classification == "WINNER"
    
    # Simulate day 30
    await tracker.update_price(address, 1.00)
    # Verify day 30 checkpoint captured
    assert outcome.day_30_price == 1.00
    assert outcome.trajectory == "crashed"
```

## Performance Considerations

**Computational Cost**:
- Day 7 checkpoint: < 10ms
- Day 30 checkpoint: < 10ms
- Trajectory calculation: < 1ms

**Storage Cost**:
- 8 new fields × 8 bytes = 64 bytes per signal
- 1000 signals = 64 KB additional

**API Impact**: None (uses existing checkpoint data)

## Summary

The time-based performance classification system provides traders with actionable intelligence at two critical decision points while maintaining fair channel reputation scoring. The system leverages existing checkpoint infrastructure and requires minimal code changes to deliver significant value.

✅ **Day 7 checkpoint** - Short-term trading decisions
✅ **Day 30 checkpoint** - Complete performance analysis  
✅ **ATH tracking** - Continuous 0-30 days (captures peaks anytime)
✅ **Trajectory analysis** - Understand timing patterns
✅ **Channel reputation** - Based on ATH only (fair scoring)
✅ **Trader intelligence** - Know when 