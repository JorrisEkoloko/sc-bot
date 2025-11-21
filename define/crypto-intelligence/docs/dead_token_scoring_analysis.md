# Dead Token Scoring Analysis for Channel Reputation

## Problem Statement

Dead tokens (tokens with 0 supply, no holders, abandoned LPs) are currently excluded from channel ROI calculations. This creates an unfair advantage for channels that call many dead/scam tokens, as these failures don't count against their reputation.

## Current State

From `domain/signal_outcome.py`:

```python
# Dead token tracking (for fair channel ROI)
is_dead_token: bool = False  # True if token is dead/inactive
dead_token_reason: str = ""  # Reason why token is dead
```

Dead tokens are flagged but **not currently counted** in channel reputation metrics.

## Reputation System Principles (from Wikipedia)

Key properties for effective reputation systems:

1. **Entities must have long lifetime** - Channels persist over time
2. **Capture and distribute feedback** - We track all signal outcomes
3. **Use feedback to guide trust** - Reputation scores influence user decisions

Critical insight: **"Without user feedback, reputation systems cannot sustain an environment of trust"**

## Analysis: How Should Dead Tokens Be Scored?

### Option 1: Count as Complete Failures (0x ROI)

**Approach:** Treat dead tokens as losing signals with 0x multiplier

**Pros:**

- Most accurate representation of reality
- Penalizes channels that call scams/dead projects
- Fair to channels that do proper research
- Aligns with reputation system principle: "capture feedback about prior interactions"

**Cons:**

- Harsh penalty for tokens that died after the call
- May not distinguish between "dead at call time" vs "died later"

**Implementation:**

```python
if signal.is_dead_token:
    signal.ath_multiplier = 0.0
    signal.day_30_multiplier = 0.0
    signal.is_winner = False
    signal.outcome_category = "dead_token_loss"
    signal.is_complete = True
    signal.completion_reason = f"dead_token: {signal.dead_token_reason}"
```

### Option 2: Count as Losing Signals (0.1x - 0.5x ROI)

**Approach:** Assign a small ROI multiplier based on how dead the token is

**Pros:**

- More nuanced than complete failure
- Can differentiate severity (0 supply = 0.1x, low supply = 0.3x, etc.)
- Still counts as a loss but not catastrophic

**Cons:**

- Arbitrary multiplier assignment
- May be too lenient on channels calling dead tokens

**Implementation:**

```python
DEAD_TOKEN_MULTIPLIERS = {
    "zero_supply": 0.0,
    "extremely_low_supply": 0.1,
    "dead_lp_token": 0.2,
    "no_holders": 0.1,
    "abandoned": 0.3
}

if signal.is_dead_token:
    # Parse reason to determine severity
    if "0 wei" in signal.dead_token_reason:
        signal.ath_multiplier = 0.0
    elif "low supply" in signal.dead_token_reason:
        signal.ath_multiplier = 0.1
    # ... etc
```

### Option 3: Exclude from ROI but Count in Total Signals

**Approach:** Track dead tokens separately, don't include in ROI calculations

**Pros:**

- Transparent about data quality issues
- Doesn't artificially inflate or deflate ROI
- Shows "X out of Y signals had data"

**Cons:**

- **Violates reputation system principles** - ignores negative feedback
- Allows channels to game the system by calling many dead tokens
- Not fair to users who need accurate channel performance

**Implementation:**

```python
# In ChannelReputation
total_signals: int = 0
signals_with_data: int = 0
dead_token_signals: int = 0
data_availability_rate: float = 0.0  # signals_with_data / total_signals
```

### Option 4: Time-Based Approach (Recommended)

**Approach:** Score based on WHEN the token died relative to the call

**Pros:**

- Most fair approach
- Distinguishes between calling dead tokens vs tokens that died later
- Aligns with 30-day tracking window
- Provides actionable feedback to channels

**Cons:**

- Requires OHLC data to determine death timing
- More complex implementation

**Implementation:**

```python
if signal.is_dead_token:
    # Try to get OHLC data to see if token had any life
    ohlc_data = await get_ohlc_for_dead_token(signal.address, signal.entry_timestamp)

    if ohlc_data and ohlc_data.had_trading_activity:
        # Token died AFTER the call - track normally with actual ROI
        signal.ath_multiplier = ohlc_data.ath_multiplier
        signal.outcome_category = "died_after_call"
    else:
        # Token was dead AT call time - complete failure
        signal.ath_multiplier = 0.0
        signal.outcome_category = "dead_at_call"
        signal.is_winner = False
```

## Recommended Approach: Hybrid Time-Based + Severity

### Scoring Logic:

1. **Dead at call time (no OHLC data):** 0.0x multiplier

   - Reason: Channel called a token that never had trading activity
   - Impact: Counts as losing signal, hurts win rate and average ROI

2. **Died within 7 days:** Use actual ATH multiplier (likely < 1.0x)

   - Reason: Token had brief life, channel gets credit/blame for actual performance
   - Impact: Counts as normal signal with real ROI

3. **Died after 7 days:** Use day 7 multiplier as final ROI

   - Reason: Token performed for a week, then died
   - Impact: Channel gets credit for the 7-day performance

4. **Dead LP tokens (abandoned pools):** 0.2x multiplier
   - Reason: These are infrastructure tokens, not investment opportunities
   - Impact: Mild penalty, not catastrophic

### Implementation in Channel Reputation:

```python
def update_with_dead_token(self, signal: SignalOutcome):
    """Update channel reputation with dead token signal."""

    self.total_signals += 1

    # Determine ROI based on death timing
    if signal.ath_multiplier == 0.0:
        # Dead at call time
        roi_multiplier = 0.0
        self.losing_signals += 1
    elif signal.day_7_multiplier > 0:
        # Had some life, use actual performance
        roi_multiplier = signal.ath_multiplier
        if roi_multiplier >= 1.5:
            self.winning_signals += 1
        elif roi_multiplier < 1.0:
            self.losing_signals += 1
        else:
            self.neutral_signals += 1
    else:
        # Dead LP or abandoned, small penalty
        roi_multiplier = 0.2
        self.losing_signals += 1

    # Update average ROI (includes dead tokens)
    self._update_roi_metrics(roi_multiplier)
```

## Impact on Channel Metrics

### Before (excluding dead tokens):

```
Channel: CryptoGems
Total Signals: 50
Winning: 30 (60%)
Average ROI: 2.5x
Reputation: "Excellent"
```

### After (including dead tokens):

```
Channel: CryptoGems
Total Signals: 65 (50 live + 15 dead)
Winning: 30 (46%)
Losing: 20 (15 dead + 5 live losses)
Average ROI: 1.9x
Reputation: "Good"
```

## Validation Against Reputation System Principles

✅ **Captures all feedback:** Dead tokens are negative feedback that must be counted
✅ **Builds trust:** Users can trust that reputation reflects ALL calls, not just successful ones
✅ **Guides decisions:** Accurate reputation helps users choose reliable channels
✅ **Long-term entities:** Channels persist, their reputation should reflect complete history
✅ **Fair scoring:** Distinguishes between calling dead tokens vs tokens that died later

## Conclusion

**Recommended:** Implement **Hybrid Time-Based + Severity** approach (Option 4)

This approach:

- Counts dead tokens in channel reputation (fair)
- Distinguishes between dead-at-call vs died-later (nuanced)
- Uses actual OHLC data when available (accurate)
- Applies appropriate penalties based on severity (balanced)
- Aligns with reputation system best practices (validated)

## Next Steps

1. Update `SignalOutcome` to track death timing
2. Modify channel reputation update logic to include dead tokens
3. Add dead token metrics to reputation dashboard
4. Test with real channel data to validate fairness
