# Part 8: Channel Reputation + Outcome Learning + ROI - Brainstorming & Research

## MCP Research Summary

### 1. Reputation Systems (Wikipedia)

✅ **Key Findings:**

- Reputation systems build trust through collective ratings
- Used successfully in eBay, Amazon, Stack Exchange
- Core principle: "computer-based technologies that manipulate an old and essential human trait" (gossip/trust)
- Goal: Gather collective opinion to build trust between users
- Different from collaborative filtering (which finds similarities)

### 2. Social Sentiment Indicators (Investopedia)

✅ **Key Findings:**

- Analyzes aggregated social media data
- Helps understand performance in eyes of consumers
- Provides early warning of reputation changes
- Can predict stock performance
- Tracks emotions: positive, negative, neutral
- Extracted from: Twitter/X, Facebook, blogs, forums

### 3. ROI Calculation (Investopedia)

✅ **Key Findings:**

- ROI = (Return - Cost) / Cost × 100%
- Measures efficiency/profitability of investment
- Can compare different investments (apples-to-apples)
- Key factors: initial investment, maintenance costs, cash flow
- Time-weighted ROI accounts for holding period

### 4. Sentiment Analysis (Wikipedia)

✅ **Key Findings:**

- Classifies text polarity: positive, negative, neutral
- Advanced: emotional states (enjoyment, anger, disgust, sadness, fear, surprise)
- Document-level, sentence-level, or aspect-level analysis
- Multi-way scales (3-star, 5-star ratings)

---

## Crypto Channel Reputation System Design

### Core Concept

**Track channel performance based on actual trading outcomes, not just engagement metrics.**

A Telegram crypto channel's reputation should be determined by:

1. **Signal Quality** - How accurate are their calls?
2. **ROI Performance** - What returns do their signals generate?
3. **Sentiment Consistency** - Do positive signals lead to positive outcomes?
4. **Risk-Adjusted Returns** - High returns with high risk vs. moderate returns with low risk
5. **Time-to-Target** - How quickly do signals reach profit targets?

### Key Metrics to Track

#### 1. **Outcome-Based Metrics** (Most Important)

- **Win Rate**: % of signals that reached 2x+ ATH
- **Average ROI**: Mean ATH multiplier across all signals
- **Risk-Adjusted ROI**: ROI weighted by token risk level
- **Time-to-Peak**: Average days to reach ATH
- **Sustainability**: % of signals that maintained gains (didn't dump immediately)

#### 2. **Sentiment Correlation Metrics**

- **Sentiment Accuracy**: Do positive sentiments → positive outcomes?
- **Sentiment-ROI Correlation**: Correlation between sentiment score and actual ROI
- **False Positive Rate**: Bullish signals that failed
- **False Negative Rate**: Missed opportunities (neutral/negative that pumped)

#### 3. **Signal Quality Metrics**

- **HDRB Score Average**: Mean engagement score of signals
- **Confidence Score Average**: Mean confidence of signals
- **Signal Frequency**: Calls per week (too many = spam, too few = inactive)
- **Market Cap Focus**: Do they call micro-caps (risky) or large-caps (safer)?

#### 4. **Consistency Metrics**

- **Performance Trend**: Improving, stable, or declining over time
- **Volatility**: Consistency of returns (stable vs. erratic)
- **Recent Performance**: Last 30 days vs. all-time (weight recent more)

---

## Reputation Scoring Formula

### Proposed Multi-Factor Reputation Score (0-100)

```
Reputation Score =
  (Win Rate × 30%) +           // 30% - Most important
  (Avg ROI × 25%) +            // 25% - Actual returns
  (Sentiment Accuracy × 20%) + // 20% - Signal quality
  (Risk-Adjusted ROI × 15%) +  // 15% - Smart risk management
  (Consistency × 10%)          // 10% - Reliability over time
```

### Tier Classification

- **Elite** (90-100): Consistently high ROI, accurate signals, low risk
- **Excellent** (75-89): Strong performance, reliable signals
- **Good** (60-74): Above average, worth following
- **Average** (40-59): Mixed results, use caution
- **Poor** (20-39): Below average, many failed signals
- **Unreliable** (0-19): Consistently poor performance

---

## Data Structure Design

### Channel Reputation Data

```python
@dataclass
class ChannelReputation:
    channel_id: str
    channel_name: str

    # Outcome metrics
    total_signals: int
    winning_signals: int  # ATH >= 2x
    win_rate: float  # 0-1
    average_roi: float  # Mean ATH multiplier
    best_roi: float  # Best ATH multiplier
    worst_roi: float  # Worst ATH multiplier

    # Sentiment metrics
    sentiment_accuracy: float  # 0-1
    positive_signals: int
    positive_wins: int
    negative_signals: int
    negative_wins: int

    # Risk metrics
    risk_adjusted_roi: float
    avg_risk_score: float
    high_risk_signals: int
    high_risk_wins: int

    # Time metrics
    avg_time_to_ath: float  # Days
    avg_time_to_2x: float  # Days

    # Consistency metrics
    performance_trend: str  # improving, stable, declining
    volatility: float  # Std dev of ROI
    recent_win_rate: float  # Last 30 days

    # Reputation score
    reputation_score: float  # 0-100
    reputation_tier: str  # elite, excellent, good, average, poor, unreliable

    # Metadata
    first_signal_date: datetime
    last_signal_date: datetime
    last_updated: datetime
```

### Signal Outcome Data

```python
@dataclass
class SignalOutcome:
    message_id: int
    channel_id: str
    channel_name: str
    timestamp: datetime

    # Signal data
    address: str
    symbol: str
    start_price: float
    sentiment: str  # positive, negative, neutral
    sentiment_score: float
    confidence: float
    hdrb_score: float

    # Outcome data
    ath_price: float
    ath_multiplier: float
    ath_time: datetime
    days_to_ath: float
    current_multiplier: float

    # Risk data
    market_tier: str
    risk_level: str
    risk_score: float

    # Outcome classification
    is_winner: bool  # ATH >= 2x
    outcome_category: str  # moon (5x+), great (3-5x), good (2-3x), break-even (1-2x), loss (<1x)
```

---

## Implementation Strategy

### Phase 1: Data Collection (Week 1)

1. Create `intelligence/channel_reputation.py`
2. Create `data/reputation/` directory
3. Link signals to outcomes via `performance_tracker.py`
4. Store signal outcomes in JSON

### Phase 2: Reputation Calculation (Week 1)

1. Implement reputation scoring algorithm
2. Calculate win rates, ROI, sentiment accuracy
3. Compute risk-adjusted metrics
4. Determine reputation tier

### Phase 3: Persistence & Updates (Week 2)

1. Save reputation data to `data/reputation/channels.json`
2. Update reputation after each signal outcome
3. Recalculate scores daily
4. Track historical reputation changes

### Phase 4: Output Integration (Week 2)

1. Add CHANNEL_REPUTATION table (CSV + Sheets)
2. Add reputation columns to MESSAGES table
3. Create reputation dashboard view
4. Add reputation filtering

---

## Advanced Features (Future)

### 1. **Comparative Analysis**

- Rank channels by reputation
- Compare channels side-by-side
- Identify best performers by market cap tier

### 2. **Predictive Scoring**

- Use historical reputation to predict signal success
- Weight signals from high-reputation channels more
- Alert when high-reputation channel makes call

### 3. **Reputation Decay**

- Recent performance weighted more heavily
- Old signals decay over time
- Prevents "resting on laurels"

### 4. **Market Condition Adjustment**

- Adjust reputation based on market conditions
- Bull market vs. bear market performance
- Volatility-adjusted scoring

### 5. **Multi-Channel Consensus**

- Track when multiple high-reputation channels call same token
- Consensus signals = higher confidence
- Divergence signals = caution

---

## Key Questions to Answer

### Technical Questions

1. ✅ How to link messages to outcomes? → Use `first_message_id` in PerformanceTracker
2. ✅ When to update reputation? → After each ATH update, daily recalculation
3. ✅ How to handle new channels? → Start with neutral score, require minimum signals
4. ✅ How to weight recent vs. old signals? → Exponential decay (recent = 2x weight)

### Business Questions

1. ✅ What's a "winning" signal? → ATH >= 2x (100% gain)
2. ✅ How long to track? → 7 days (matches performance tracker)
3. ✅ Minimum signals for reputation? → 10 signals minimum
4. ✅ How to handle sentiment? → Positive sentiment + positive outcome = accuracy boost

### User Questions

1. ✅ How to display reputation? → Tier badge + score + win rate
2. ✅ How to filter by reputation? → Add reputation threshold to queries
3. ✅ How to compare channels? → Reputation leaderboard table
4. ✅ How to track changes? → Historical reputation graph

---

## Success Metrics

### System Success

- ✅ Reputation scores correlate with actual performance
- ✅ High-reputation channels have >60% win rate
- ✅ Low-reputation channels have <40% win rate
- ✅ Sentiment accuracy >70% for elite channels

### User Success

- ✅ Users can identify best channels quickly
- ✅ Users can filter signals by channel reputation
- ✅ Users can track reputation changes over time
- ✅ Users can make informed decisions based on reputation

---

## Next Steps

1. **Review & Validate** - Get user feedback on design
2. **Create Spec** - Formal requirements and design document
3. **Implement** - Build channel_reputation.py
4. **Test** - Validate with historical data
5. **Deploy** - Integrate into pipeline

---

**Research Date**: 2025-11-11
**MCP Sources**: Wikipedia (Reputation Systems, Sentiment Analysis), Investopedia (Social Sentiment, ROI)
**Status**: ✅ RESEARCH COMPLETE - Ready for spec creation
