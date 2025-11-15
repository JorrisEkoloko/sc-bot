# Dual-Metric Performance System - Implementation Analysis

## Executive Summary

Analysis of codebase to determine where dual-metric performance evaluation (ATH + Final) needs to be implemented for the recommended classification system.

**Date**: November 14, 2025  
**Status**: Ready for Spec Creation

---

## Recommended Classification System

### Performance Categories

| Category          | Criteria                    | Emoji | Description                     |
| ----------------- | --------------------------- | ----- | ------------------------------- |
| **MOON** 🌙       | ATH ≥ 5.0x                  | 🌙    | Exceptional performance         |
| **WINNER** ✅     | ATH ≥ 2.0x AND Final ≥ 1.0x | ✅    | Profitable with sustained gains |
| **GOOD** 👍       | ATH ≥ 1.5x AND Final ≥ 0.9x | 👍    | Decent performance              |
| **BREAK-EVEN** ⚖️ | ATH ≥ 1.0x AND Final ≥ 0.9x | ⚖️    | No significant loss             |
| **LOSER** ❌      | Final < 0.9x                | ❌    | Lost money                      |
| **CRASH** 💥      | Final < 0.5x                | 💥    | Major loss/rug pull             |

### Key Insights

- **ATH captures opportunity**: Shows peak potential (for traders who took profit)
- **Final captures reality**: Shows actual outcome (for holders)
- **Gap identifies risk**: Large ATH-Final gap = pump & dump pattern
- **Fair to channels**: Rewards both peak opportunity AND sustainable performance

---

## Current System Analysis

### 1. Performance Tracking (`services/tracking/performance_tracker.py`)

**Current Implementation**:

```python
# Tracks ATH since mention
'ath_since_mention': initial_price,
'ath_time': now.isoformat(),
'current_price': initial_price,
'last_update': now.isoformat()
```

**What's Missing**:

- ❌ No final price capture at 7-day completion
- ❌ No dual-metric classification
- ❌ No performance gap calculation
- ❌ No category assignment (MOON/WINNER/etc.)

**What's Good**:

- ✅ Already tracks ATH price and time
- ✅ Already tracks current price
- ✅ Already calculates ATH multiplier
- ✅ Already has 7-day tracking window

---

### 2. ROI Calculator (`utils/roi_calculator.py`)

**Current Implementation**:

```python
@staticmethod
def categorize_outcome(ath_multiplier: float) -> Tuple[bool, str]:
    """Single-metric categorization based on ATH only"""
    if ath_multiplier >= 5.0:
        category = "moon"
    elif ath_multiplier >= 3.0:
        category = "great"
    # ... etc
```

**What's Missing**:

- ❌ No final price consideration
- ❌ No dual-metric logic (ATH + Final)
- ❌ No crash detection (Final < 0.5x)
- ❌ No performance gap calculation

**What's Good**:

- ✅ Already has categorization framework
- ✅ Already calculates ROI multipliers
- ✅ Already has is_winner logic

---

### 3. Signal Outcome (`domain/signal_outcome.py`)

**Current Implementation**:

```python
@dataclass
class SignalOutcome:
    # Outcome data (ATH = All-Time High)
    ath_price: float = 0.0
    ath_multiplier: float = 0.0
    current_price: float = 0.0
    current_multiplier: float = 0.0

    # Status
    is_winner: bool = False
    outcome_category: str = ""  # moon, great, good, moderate, break_even, loss
```

**What's Missing**:

- ❌ No final_price field (distinct from current_price)
- ❌ No final_multiplier field
- ❌ No performance_gap field
- ❌ No dual-metric category

**What's Good**:

- ✅ Already has ATH fields
- ✅ Already has outcome_category field
- ✅ Already has is_winner field
- ✅ Already has checkpoints system

---

### 4. Reputation Calculator (`services/reputation/reputation_calculator.py`)

**Current Implementation**:

```python
@staticmethod
def calculate_win_rate(outcomes: List[SignalOutcome]) -> tuple:
    """Uses is_winner field (market-tier aware)"""
    winners = sum(1 for o in outcomes if o.is_winner)
```

**What's Missing**:

- ❌ No dual-metric win rate calculation
- ❌ No crash rate tracking
- ❌ No performance gap analysis
- ❌ No category distribution metrics

**What's Good**:

- ✅ Already processes outcomes list
- ✅ Already calculates win rates
- ✅ Already has tier-specific logic
- ✅ Already calculates composite scores

---

## Implementation Requirements

### Phase 1: Data Model Updates

**File**: `domain/signal_outcome.py`

**Add Fields**:

```python
@dataclass
class SignalOutcome:
    # ... existing fields ...

    # Dual-metric performance (NEW)
    final_price: float = 0.0  # Price at 7-day completion
    final_multiplier: float = 0.0  # Final ROI multiplier
    performance_gap: float = 0.0  # ATH - Final (drawdown from peak)

    # Enhanced categorization (UPDATED)
    outcome_category: str = ""  # MOON, WINNER, GOOD, BREAK-EVEN, LOSER, CRASH
    category_emoji: str = ""  # 🌙, ✅, 👍, ⚖️, ❌, 💥
```

---

### Phase 2: ROI Calculator Updates

**File**: `utils/roi_calculator.py`

**Replace Method**:

```python
@staticmethod
def categorize_outcome_dual_metric(
    ath_multiplier: float,
    final_multiplier: float
) -> Tuple[bool, str, str, float]:
    """
    Dual-metric categorization (ATH + Final).

    Returns:
        Tuple[bool, str, str, float]: (is_winner, category, emoji, gap)
    """
    gap = ath_multiplier - final_multiplier

    # CRASH: Major loss (rug pull pattern)
    if final_multiplier < 0.5:
        return (False, "CRASH", "💥", gap)

    # LOSER: Lost money
    if final_multiplier < 0.9:
        return (False, "LOSER", "❌", gap)

    # MOON: Exceptional performance
    if ath_multiplier >= 5.0:
        return (True, "MOON", "🌙", gap)

    # WINNER: Profitable with sustained gains
    if ath_multiplier >= 2.0 and final_multiplier >= 1.0:
        return (True, "WINNER", "✅", gap)

    # GOOD: Decent performance
    if ath_multiplier >= 1.5 and final_multiplier >= 0.9:
        return (True, "GOOD", "👍", gap)

    # BREAK-EVEN: No significant loss
    if ath_multiplier >= 1.0 and final_multiplier >= 0.9:
        return (False, "BREAK-EVEN", "⚖️", gap)

    # Default to LOSER
    return (False, "LOSER", "❌", gap)
```

---

### Phase 3: Performance Tracker Updates

**File**: `services/tracking/performance_tracker.py`

**Add Method**:

```python
async def complete_tracking(self, address: str, final_price: float) -> dict:
    """
    Complete 7-day tracking and calculate final metrics.

    Args:
        address: Token contract address
        final_price: Final price at 7-day completion

    Returns:
        dict: Complete performance metrics with dual-metric classification
    """
    if address not in self.tracking_data:
        return None

    entry = self.tracking_data[address]

    # Calculate final metrics
    final_multiplier = final_price / entry['start_price']
    ath_multiplier = entry['ath_since_mention'] / entry['start_price']
    performance_gap = ath_multiplier - final_multiplier

    # Dual-metric categorization
    is_winner, category, emoji, gap = ROICalculator.categorize_outcome_dual_metric(
        ath_multiplier, final_multiplier
    )

    return {
        'address': address,
        'start_price': entry['start_price'],
        'ath_price': entry['ath_since_mention'],
        'final_price': final_price,
        'ath_multiplier': ath_multiplier,
        'final_multiplier': final_multiplier,
        'performance_gap': performance_gap,
        'is_winner': is_winner,
        'category': category,
        'emoji': emoji,
        'days_tracked': (datetime.now() - datetime.fromisoformat(entry['start_time'])).days
    }
```

---

### Phase 4: Outcome Tracker Updates

**File**: `services/tracking/outcome_tracker.py`

**Update Completion Logic**:

```python
async def complete_signal(self, outcome: SignalOutcome, final_price: float):
    """
    Complete signal tracking with dual-metric classification.

    Args:
        outcome: Signal outcome to complete
        final_price: Final price at completion
    """
    # Calculate final metrics
    outcome.final_price = final_price
    _, outcome.final_multiplier = ROICalculator.calculate_roi(
        outcome.entry_price, final_price
    )

    # Calculate performance gap
    outcome.performance_gap = outcome.ath_multiplier - outcome.final_multiplier

    # Dual-metric categorization
    is_winner, category, emoji, gap = ROICalculator.categorize_outcome_dual_metric(
        outcome.ath_multiplier, outcome.final_multiplier
    )

    outcome.is_winner = is_winner
    outcome.outcome_category = category
    outcome.category_emoji = emoji

    # Mark as complete
    outcome.is_complete = True
    outcome.status = "completed"

    # Save to repository
    await self.repository.save_outcome(outcome)
```

---

### Phase 5: Reputation Calculator Updates

**File**: `services/reputation/reputation_calculator.py`

**Add Methods**:

```python
@staticmethod
def calculate_category_distribution(outcomes: List[SignalOutcome]) -> dict:
    """
    Calculate distribution of outcome categories.

    Returns:
        dict: Count and percentage for each category
    """
    if not outcomes:
        return {}

    categories = {}
    for outcome in outcomes:
        cat = outcome.outcome_category
        categories[cat] = categories.get(cat, 0) + 1

    total = len(outcomes)
    return {
        cat: {
            'count': count,
            'percentage': (count / total) * 100
        }
        for cat, count in categories.items()
    }

@staticmethod
def calculate_crash_rate(outcomes: List[SignalOutcome]) -> tuple[int, float]:
    """
    Calculate crash rate (Final < 0.5x).

    Returns:
        tuple[int, float]: (crash_count, crash_rate_percentage)
    """
    if not outcomes:
        return (0, 0.0)

    crashes = sum(1 for o in outcomes if o.outcome_category == "CRASH")
    crash_rate = (crashes / len(outcomes)) * 100

    return (crashes, crash_rate)

@staticmethod
def calculate_average_gap(outcomes: List[SignalOutcome]) -> tuple[float, float, float]:
    """
    Calculate performance gap statistics (ATH - Final).

    Returns:
        tuple[float, float, float]: (avg_gap, max_gap, median_gap)
    """
    if not outcomes:
        return (0.0, 0.0, 0.0)

    gaps = [o.performance_gap for o in outcomes if hasattr(o, 'performance_gap')]

    if not gaps:
        return (0.0, 0.0, 0.0)

    avg_gap = statistics.mean(gaps)
    max_gap = max(gaps)
    median_gap = statistics.median(gaps)

    return (avg_gap, max_gap, median_gap)
```

---

### Phase 6: CSV Output Updates

**File**: `repositories/writers/csv_writer.py`

**Update Performance Table Columns**:

```python
PERFORMANCE_COLUMNS = [
    'address', 'chain', 'first_message_id',
    'start_price', 'start_time',
    'ath_price', 'ath_time', 'ath_multiplier',
    'final_price', 'final_multiplier',  # NEW
    'performance_gap',  # NEW
    'category', 'emoji',  # NEW
    'days_tracked'
]
```

---

## Integration Points

### 1. Message Processing Flow

```
Message Received
    ↓
Address Extracted
    ↓
Performance Tracker: start_tracking()
    ↓
[7 days of price updates]
    ↓
Performance Tracker: complete_tracking()  ← DUAL-METRIC CLASSIFICATION
    ↓
Outcome Tracker: complete_signal()  ← SAVE WITH CATEGORY
    ↓
Reputation Engine: update_reputation()  ← USE NEW METRICS
```

### 2. Data Flow

```
PerformanceTracker
    ├─ Tracks: ATH price, current price
    ├─ Calculates: ATH multiplier
    └─ On completion: final_price, final_multiplier, gap
        ↓
ROICalculator
    ├─ Input: ath_multiplier, final_multiplier
    └─ Output: category, emoji, is_winner, gap
        ↓
SignalOutcome
    ├─ Stores: All metrics
    └─ Persists: To JSON repository
        ↓
ReputationCalculator
    ├─ Analyzes: Category distribution
    ├─ Calculates: Crash rate, gap statistics
    └─ Updates: Channel reputation scores
```

---

## Testing Requirements

### Unit Tests

1. **ROI Calculator Tests**

   - Test all 6 categories (MOON, WINNER, GOOD, BREAK-EVEN, LOSER, CRASH)
   - Test edge cases (ATH = Final, Final > ATH)
   - Test gap calculation accuracy

2. **Performance Tracker Tests**

   - Test completion with various price scenarios
   - Test dual-metric calculation
   - Test category assignment

3. **Reputation Calculator Tests**
   - Test category distribution calculation
   - Test crash rate calculation
   - Test gap statistics

### Integration Tests

1. **End-to-End Flow**

   - Track signal from start to completion
   - Verify dual-metric classification
   - Verify reputation update

2. **Real Data Validation**
   - Test with TRUMP example (ATH 5.0x, Final 0.03x = CRASH)
   - Test with successful signal (ATH 3.0x, Final 2.5x = WINNER)
   - Test with pump & dump (ATH 10x, Final 0.8x = LOSER)

---

## Migration Strategy

### Backward Compatibility

**Existing Data**:

- Current `signal_outcomes.json` has ATH data
- Missing: final_price, final_multiplier, performance_gap
- Solution: Add migration script to populate missing fields

**Migration Script**:

```python
def migrate_existing_outcomes():
    """Add dual-metric fields to existing outcomes."""
    for outcome in existing_outcomes:
        if not hasattr(outcome, 'final_price'):
            # Use current_price as final_price for completed signals
            outcome.final_price = outcome.current_price
            outcome.final_multiplier = outcome.current_multiplier
            outcome.performance_gap = outcome.ath_multiplier - outcome.final_multiplier

            # Recalculate category with dual-metric
            is_winner, category, emoji, gap = ROICalculator.categorize_outcome_dual_metric(
                outcome.ath_multiplier, outcome.final_multiplier
            )
            outcome.outcome_category = category
            outcome.category_emoji = emoji
```

---

## Performance Impact

### Computational Cost

- **Minimal**: Only adds 3 calculations per signal completion
  - final_multiplier = final_price / entry_price
  - performance_gap = ath_multiplier - final_multiplier
  - category = categorize_outcome_dual_metric()

### Storage Cost

- **Minimal**: Adds 4 fields per signal outcome
  - final_price (float): 8 bytes
  - final_multiplier (float): 8 bytes
  - performance_gap (float): 8 bytes
  - category_emoji (str): ~4 bytes
  - **Total**: ~28 bytes per signal

### API Impact

- **None**: No additional API calls required
- Uses existing price data from tracking

---

## Success Metrics

### Implementation Success

- ✅ All 6 categories correctly assigned
- ✅ Performance gap accurately calculated
- ✅ Backward compatibility maintained
- ✅ CSV output includes new columns
- ✅ Reputation metrics use dual-metric logic

### Business Success

- ✅ Identifies pump & dump patterns (large gap)
- ✅ Rewards sustainable performance (WINNER vs LOSER)
- ✅ Fair channel reputation scoring
- ✅ Clear signal quality classification

---

## Files to Modify

### Core Changes (Required)

1. ✅ `domain/signal_outcome.py` - Add dual-metric fields
2. ✅ `utils/roi_calculator.py` - Update categorization logic
3. ✅ `services/tracking/performance_tracker.py` - Add completion method
4. ✅ `services/tracking/outcome_tracker.py` - Update completion logic
5. ✅ `services/reputation/reputation_calculator.py` - Add new metrics

### Supporting Changes (Optional)

6. ⚠️ `repositories/writers/csv_writer.py` - Update columns
7. ⚠️ `infrastructure/output/data_output.py` - Update output format
8. ⚠️ `scripts/migrate_outcomes.py` - Create migration script

### Documentation Updates

9. 📝 Update implementation guides
10. 📝 Update API documentation
11. 📝 Update user guides

---

## Next Steps

1. **Create Spec**: Formal specification document
2. **Review & Approve**: Stakeholder review
3. **Implementation**: Phase-by-phase development
4. **Testing**: Unit + integration tests
5. **Migration**: Update existing data
6. **Deployment**: Production rollout
7. **Monitoring**: Track new metrics

---

## Conclusion

The dual-metric performance evaluation system is:

- ✅ **Validated**: Industry-standard approach
- ✅ **Feasible**: Minimal code changes required
- ✅ **Valuable**: Better signal quality assessment
- ✅ **Ready**: Clear implementation path

**Recommendation**: PROCEED WITH SPEC CREATION

---

**Document Version**: 1.0  
**Last Updated**: November 14, 2025  
**Status**: ✅ READY FOR SPEC
