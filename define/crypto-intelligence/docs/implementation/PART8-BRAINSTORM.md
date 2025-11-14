# Part 8: Channel Reputation + Outcome Learning - Brainstorm & Design

## MCP Research Summary

### Reputation Systems (Wikipedia)

- **Core Concept**: Collect ratings to build trust through reputation
- **Key Difference from Collaborative Filtering**: Gather collective opinion vs finding similarities
- **Trust Building**: Use historical behavior to predict future reliability
- **Social Function**: Like gossip - "who to trust, who other people trust"

### Reinforcement Learning (Wikipedia)

- **Core Concept**: Agent learns from rewards/penalties based on outcomes
- **Feedback Loop**: Action → Environment → Reward → Learning
- **Temporal Difference**: Learn from difference between predicted and actual outcomes
- **Q-Learning**: Learn quality of actions in given states

## Current Data Available

### From MESSAGES table:

- `message_id` - Unique identifier
- `channel_name` - Source channel (e.g., "Eric Cryptomans Journal")
- `hdrb_score` - Message quality score
- `confidence` - Signal confidence
- `sentiment` - Positive/negative/neutral
- `crypto_mentions` - Tokens mentioned

### From PERFORMANCE table:

- `address` - Token address
- `first_message_id` - Links to message that mentioned it
- `start_price` - Price when mentioned
- `ath_since_mention` - Best price achieved
- `ath_multiplier` - ROI multiplier (e.g., 1.22x = 22% gain)
- `current_multiplier` - Current ROI
- `days_tracked` - Time since mention

## Proposed Channel Reputation System

### 1. Reputation Metrics

#### A. **Success Rate** (Binary Outcomes)

- **Win**: Token achieved 2x+ (100% gain)
- **Loss**: Token dropped below start price
- **Neutral**: Between 0.9x - 2.0x
- Formula: `success_rate = wins / total_calls`

#### B. **Average ROI** (Continuous Outcomes)

- Average of all `ath_multiplier` values
- Weighted by recency (recent calls matter more)
- Formula: `avg_roi = sum(ath_multiplier * recency_weight) / total_calls`

#### C. **Risk-Adjusted Returns** (Sharpe-like Ratio)

- Consider volatility and consistency
- Formula: `sharpe = (avg_roi - 1.0) / std_dev(roi)`
- Higher = more consistent returns

#### D. **Hit Rate by Tier**

- Track success rate per market cap tier
- "Good at micro-caps" vs "Good at large-caps"
- Separate scores for: large, mid, small, micro

#### E. **Time to Target**

- How fast do their calls reach 2x?
- Average days to ATH
- Faster = better for short-term trading

#### F. **Decay Factor** (Recency Bias)

- Recent performance matters more than old
- Exponential decay: `weight = e^(-λ * days_ago)`
- λ = 0.1 means 10% decay per day

### 2. Reputation Score Formula

**Weighted Composite Score (0-100):**

```python
reputation_score = (
    success_rate * 30 +           # 30% - Win rate
    (avg_roi - 1.0) * 100 * 25 +  # 25% - Average returns
    sharpe_ratio * 10 * 20 +      # 20% - Consistency
    speed_score * 15 +            # 15% - Time to target
    confidence_score * 10         # 10% - Signal confidence
)
```

### 3. Outcome-Based Learning (Reinforcement Learning)

#### Temporal Difference Learning:

```python
# Update reputation when outcome is known
predicted_roi = channel_reputation.expected_roi
actual_roi = ath_multiplier

# Learning rate (how fast to adapt)
alpha = 0.1

# Update rule (TD learning)
error = actual_roi - predicted_roi
new_reputation = old_reputation + alpha * error
```

#### State-Action-Reward Framework:

- **State**: Channel + Token tier + Market conditions
- **Action**: Follow signal or ignore
- **Reward**: Actual ROI achieved
- **Learn**: Which channels to trust in which conditions

### 4. Data Structure

#### ChannelReputation Object:

```python
@dataclass
class ChannelReputation:
    channel_name: str
    total_calls: int
    successful_calls: int  # 2x+ achieved
    failed_calls: int      # Lost money

    # ROI metrics
    avg_roi: float
    median_roi: float
    best_roi: float
    worst_roi: float

    # Risk metrics
    roi_std_dev: float
    sharpe_ratio: float

    # Tier-specific
    large_cap_success_rate: float
    mid_cap_success_rate: float
    small_cap_success_rate: float
    micro_cap_success_rate: float

    # Time metrics
    avg_days_to_ath: float
    avg_days_to_2x: float

    # Confidence
    avg_confidence: float
    avg_hdrb_score: float

    # Reputation score
    reputation_score: float  # 0-100
    reputation_tier: str     # elite, trusted, average, poor

    # Metadata
    first_call_date: datetime
    last_call_date: datetime
    last_updated: datetime
```

#### Persistence (JSON):

```json
{
  "Eric Cryptomans Journal": {
    "total_calls": 15,
    "successful_calls": 10,
    "avg_roi": 1.85,
    "reputation_score": 78.5,
    "reputation_tier": "trusted",
    "tier_performance": {
      "micro": { "calls": 8, "success_rate": 0.75, "avg_roi": 2.1 },
      "small": { "calls": 5, "success_rate": 0.6, "avg_roi": 1.5 },
      "mid": { "calls": 2, "success_rate": 0.5, "avg_roi": 1.2 }
    },
    "recent_calls": [
      { "address": "5gb4...", "roi": 1.22, "days": 1, "tier": "small" },
      { "address": "0xba1...", "roi": 0.93, "days": 1, "tier": "small" }
    ]
  }
}
```

### 5. Integration Points

#### A. **PerformanceTracker Integration**

- When ATH updates, notify ChannelReputation
- Pass: `(channel_name, address, ath_multiplier, days_tracked)`
- Update channel stats in real-time

#### B. **MessageProcessor Integration**

- When processing message, lookup channel reputation
- Add reputation score to ProcessedMessage
- Use reputation to adjust confidence score

#### C. **DataOutput Integration**

- Add CHANNEL_REPUTATION table (new table)
- Add `channel_reputation_score` to MESSAGES table
- Add `channel_success_rate` to MESSAGES table

### 6. Advanced Features

#### A. **Conditional Reputation**

- "Good at micro-caps during bull markets"
- "Good at large-caps during bear markets"
- Context-aware reputation scoring

#### B. **Ensemble Learning**

- Combine multiple channels' signals
- Weight by reputation
- "3 trusted channels mentioned this = strong signal"

#### C. **Anomaly Detection**

- Detect when channel behavior changes
- "Usually 70% success rate, now 30% - something changed"
- Alert user to reputation decay

#### D. **Reputation Tiers**

```python
REPUTATION_TIERS = {
    "elite": (80, 100),      # Top performers
    "trusted": (60, 80),     # Reliable
    "average": (40, 60),     # Hit or miss
    "poor": (20, 40),        # Below average
    "unproven": (0, 20)      # Not enough data
}
```

## Implementation Plan

### Phase 1: Core Reputation System

1. Create `intelligence/channel_reputation.py`
2. Implement ChannelReputation dataclass
3. Implement reputation calculation logic
4. Add JSON persistence (`data/reputation/channels.json`)

### Phase 2: Outcome Learning

5. Integrate with PerformanceTracker
6. Implement TD learning updates
7. Add recency weighting

### Phase 3: Data Output

8. Create CHANNEL_REPUTATION table
9. Add reputation columns to MESSAGES table
10. Update Google Sheets with reputation data

### Phase 4: Advanced Features

11. Tier-specific reputation
12. Time-based metrics
13. Reputation decay for inactive channels

## Key Design Decisions

### 1. **When to Update Reputation?**

- **Option A**: Real-time (every price update)
  - Pro: Always current
  - Con: Expensive, lots of writes
- **Option B**: Daily batch (end of day)
  - Pro: Efficient
  - Con: Delayed updates
- **Option C**: On significant events (2x achieved, 7 days passed)
  - Pro: Balanced
  - Con: More complex
- **RECOMMENDATION**: Option C - Event-driven updates

### 2. **How Much History to Keep?**

- **Option A**: All history forever
  - Pro: Complete record
  - Con: Old data may not be relevant
- **Option B**: Rolling window (last 90 days)
  - Pro: Focuses on recent performance
  - Con: Loses long-term trends
- **Option C**: Exponential decay (all data, weighted by recency)
  - Pro: Best of both worlds
  - Con: More complex math
- **RECOMMENDATION**: Option C - Exponential decay with λ=0.01 (1% daily decay)

### 3. **Minimum Calls for Reputation?**

- Need enough data to be statistically significant
- **RECOMMENDATION**: Minimum 5 calls to show reputation
- Below 5 calls: Show "Unproven" tier

### 4. **Success Threshold?**

- What counts as "success"?
- **Option A**: Any profit (>1.0x)
- **Option B**: 2x or better (>2.0x)
- **Option C**: Beats market average
- **RECOMMENDATION**: Option B - 2x threshold (aligns with crypto expectations)

## Expected Outcomes

### User Benefits:

1. **Trust Signals**: Know which channels to follow
2. **Risk Management**: Avoid channels with poor track record
3. **Strategy Optimization**: Follow different channels for different tiers
4. **Performance Attribution**: "This channel made me 50% this month"

### System Benefits:

1. **Adaptive Confidence**: Adjust signal confidence based on channel reputation
2. **Quality Filter**: Ignore low-reputation channels
3. **Learning System**: Gets smarter over time
4. **Competitive Analysis**: Compare channels objectively

## Next Steps

1. **Review & Validate**: Get feedback on this design
2. **Create Spec**: Formalize into requirements.md and tasks.md
3. **Implement**: Build the system
4. **Test**: Validate with historical data
5. **Deploy**: Integrate into production pipeline

---

**Status**: 📋 BRAINSTORM COMPLETE - Ready for spec creation
**MCP Verified**: Reputation systems & reinforcement learning concepts
**Data Available**: Messages + Performance tracking already in place
