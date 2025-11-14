# Design Document - Part 8: Channel Reputation + Outcome Learning

## Overview

Part 8 implements an intelligent channel reputation system that transforms the crypto intelligence platform from passive monitoring to active learning. The system operates in two distinct phases:

**Phase 1: Historical Bootstrap** - Processes complete channel history (all messages from channel creation) to establish statistically significant baseline reputation scores before live monitoring begins.

**Phase 2: Live Monitoring** - Continues tracking new signals in real-time, updating reputations with each completed outcome using temporal difference learning.

This two-phase approach ensures that reputation scores are meaningful from day one, avoiding the "cold start problem" where new channels have no track record. The system tracks actual trading outcomes, calculates multi-dimensional reputation scores, and uses temporal difference learning to continuously improve predictions. This design enables traders to identify high-quality signal sources and make data-driven decisions about which channels to trust.

### Core Principle: ROI-Driven Reputation

**The entire reputation system is built around one fundamental metric: ROI (Return on Investment).**

Every aspect of channel reputation traces back to actual trading outcomes:

1. **Entry Point** → Channel mentions token at price X
2. **Tracking** → System monitors price performance over 30 days
3. **Outcome** → Token reaches ATH at price Y
4. **ROI Calculation** → ROI = (Y - X) / X
5. **Reputation Update** → Channel reputation adjusts based on ROI result

**The Holistic ROI Flow**:

```
Message: "Bought $AVICI at $1.47"
    ↓
Entry Price: $1.47 (confidence: 0.85)
    ↓
Track Performance: 1h, 4h, 24h, 3d, 7d, 30d checkpoints
    ↓
Calculate ROI at each checkpoint:
  - 1h: $1.52 → 3.4% ROI (1.034x)
  - 4h: $1.89 → 28.6% ROI (1.286x)
  - 24h: $4.78 → 225.2% ROI (3.252x) ← ATH
    ↓
Signal Complete: ATH = 3.252x (Winner! >2x threshold)
    ↓
Update Channel Reputation:
  - Win Rate: 10/15 = 66.7% (this was a win)
  - Average ROI: (old_avg * 14 + 3.252) / 15 = 1.85x
  - Sharpe Ratio: (1.85 - 1.0) / std_dev = 0.89
  - Speed Score: Reached ATH in 1 day (fast!)
    ↓
Calculate Reputation Score:
  - Win Rate (66.7%) × 30% = 20.0 points
  - Avg ROI (1.85x) × 25% = 10.6 points
  - Sharpe (0.89) × 20% = 8.9 points
  - Speed (78.5) × 15% = 11.8 points
  - Confidence (82%) × 10% = 8.2 points
  = 59.5 / 100 → "Average" tier
    ↓
TD Learning Update:
  - Predicted ROI: 1.50x
  - Actual ROI: 3.252x
  - Error: +1.752x (underestimated!)
  - New Prediction: 1.50 + 0.1 * 1.752 = 1.675x
    ↓
Output to Trader:
  - "Eric Cryptomans Journal: 59.5 score, Average tier"
  - "Win rate: 66.7%, Avg ROI: 1.85x (85% gain)"
  - "Expected next signal ROI: 1.675x (67.5% gain)"
```

**Why ROI is Central**:

- **Win Rate** = % of signals with ROI ≥ 2.0x (100% gain)
- **Average ROI** = Mean ROI multiplier across all signals
- **Sharpe Ratio** = (Avg ROI - 1.0) / ROI volatility
- **Speed Score** = How fast signals reach high ROI
- **TD Learning** = Predicts future ROI based on past ROI
- **Reputation Score** = Weighted composite of ROI-based metrics

**The Bottom Line**: A channel's reputation is the answer to one question:
_"If I follow this channel's signals, what ROI can I expect?"_

The system integrates with existing components (PerformanceTracker, MessageProcessor, DataOutput) while adding new intelligence capabilities for outcome-based learning and reputation scoring.

## Architecture

### System Components

```
crypto-intelligence/
├── intelligence/
│   ├── channel_reputation.py      # NEW: Reputation calculation & learning
│   ├── outcome_tracker.py         # NEW: Signal outcome tracking
│   ├── historical_bootstrap.py    # NEW: Historical data processing
│   └── market_analyzer.py         # EXISTING: Market cap analysis
├── core/
│   ├── historical_scraper.py      # EXISTING: Scrapes channel history
│   ├── performance_tracker.py     # MODIFIED: Add outcome callbacks
│   ├── message_processor.py       # MODIFIED: Add reputation lookup
│   └── data_output.py             # MODIFIED: Add reputation columns
├── data/
│   └── reputation/
│       ├── channels.json          # NEW: Channel reputation data
│       ├── signal_outcomes.json   # NEW: Historical + live signal outcomes
│       └── bootstrap_status.json  # NEW: Bootstrap progress tracking
└── config/
    └── settings.py                # MODIFIED: Add reputation config
```

### Data Flow

**Historical Bootstrap Flow:**

```
HistoricalScraper → Retrieve all channel messages
    ↓
MessageProcessor (batch mode) → Extract tokens, sentiment, HDRB
    ↓
HistoricalBootstrap → For each token mention:
    ↓
Twelve Data API → Get entry price at message timestamp
    ↓
Twelve Data API → Get 30 days of price data after mention
    ↓
Calculate ATH, ROI, days_to_ath → Create completed SignalOutcome
    ↓
ChannelReputation → Aggregate all outcomes
    ↓
Calculate initial reputation scores
    ↓
Save to channels.json + signal_outcomes.json
    ↓
Bootstrap complete → Ready for live monitoring
```

**Live Monitoring Flow:**

```
Message → MessageProcessor
    ↓
Extract Address + Channel
    ↓
Lookup Channel Reputation → Adjust confidence
    ↓
PerformanceTracker (track price)
    ↓
Price Updates → OutcomeTracker
    ↓
Checkpoint Reached → Calculate ROI
    ↓
Signal Complete → ChannelReputation
    ↓
Update Reputation (TD Learning)
    ↓
Save to channels.json
    ↓
DataOutput (add reputation columns)
```

## Components and Interfaces

### 1. HistoricalBootstrap (intelligence/historical_bootstrap.py)

**Purpose**: Process complete channel history to establish initial reputation scores before live monitoring begins.

**Key Classes**:

- `HistoricalBootstrap`: Main bootstrap orchestrator
- `HistoricalPriceRetriever`: Fetches historical price data from Twelve Data
- `BootstrapProgress`: Tracks bootstrap progress and status

**Interface**:

```python
@dataclass
class BootstrapProgress:
    channel_name: str
    total_messages: int
    processed_messages: int
    total_tokens: int
    processed_tokens: int
    successful_outcomes: int
    failed_outcomes: int
    api_calls_made: int
    start_time: datetime
    estimated_completion: datetime
    status: str  # "in_progress", "completed", "failed"

class HistoricalBootstrap:
    def __init__(self, config: Config,
                 historical_scraper: HistoricalScraper,
                 message_processor: MessageProcessor,
                 outcome_tracker: OutcomeTracker,
                 reputation_engine: ReputationEngine):
        self.config = config
        self.historical_scraper = historical_scraper
        self.message_processor = message_processor
        self.outcome_tracker = outcome_tracker
        self.reputation_engine = reputation_engine
        self.progress: dict[str, BootstrapProgress] = {}

    async def bootstrap_channel(self, channel_name: str) -> BootstrapProgress:
        """
        Bootstrap a single channel with complete history

        Process:
        1. Scrape all historical messages
        2. Process each message to extract tokens
        3. For each token, fetch historical prices
        4. Calculate outcomes and create SignalOutcomes
        5. Calculate initial reputation
        6. Save to JSON

        Returns:
            BootstrapProgress with final statistics
        """

    async def bootstrap_all_channels(self, channel_names: list[str]) -> dict[str, BootstrapProgress]:
        """Bootstrap all channels in parallel with rate limiting"""

    async def process_historical_message(self, message: TelegramMessage) -> list[SignalOutcome]:
        """
        Process a single historical message

        Steps:
        1. Extract tokens and addresses
        2. Get entry price at message timestamp
        3. Get 30 days of price data
        4. Calculate ATH and outcome
        5. Create completed SignalOutcome
        """

    async def get_historical_entry_price(self, address: str,
                                        timestamp: datetime) -> tuple[float, float, str]:
        """
        Get entry price for historical message

        Priority:
        1. Message text parsing (if available)
        2. Twelve Data at timestamp
        3. Skip if unavailable

        Returns:
            (entry_price, confidence, source)
        """

    async def get_historical_outcome(self, address: str,
                                    entry_price: float,
                                    start_date: datetime) -> SignalOutcome:
        """
        Calculate outcome from historical price data

        Steps:
        1. Query Twelve Data for 30 days of hourly OHLC data
        2. Find ATH price and date
        3. Calculate ROI and multiplier
        4. Determine checkpoints (1h, 4h, 24h, 3d, 7d, 30d)
        5. Classify outcome (winner/loser)
        6. Return completed SignalOutcome
        """

    def save_bootstrap_progress(self) -> None:
        """Save bootstrap progress to JSON for resumability"""

    def load_bootstrap_progress(self) -> None:
        """Load bootstrap progress to resume interrupted bootstrap"""

class HistoricalPriceRetriever:
    def __init__(self, twelve_data_api: TwelveDataAPI):
        self.api = twelve_data_api
        self.cache: dict[str, dict] = {}  # Cache historical data
        self.rate_limiter = RateLimiter(max_calls=800, window=86400)  # 800/day

    async def get_price_at_timestamp(self, address: str,
                                     timestamp: datetime) -> tuple[float, float]:
        """
        Get price at specific timestamp

        Returns:
            (price, confidence)
        """

    async def get_hourly_prices(self, address: str,
                               start_date: datetime,
                               days: int = 30) -> list[HourlyPrice]:
        """
        Get hourly OHLC prices for date range

        Uses hourly candles for accurate checkpoint tracking:
        - 30 days = 720 API calls per token
        - Provides precise 1h, 4h, 24h checkpoint data

        Returns:
            List of HourlyPrice objects with open, high, low, close
        """

    def get_from_cache(self, address: str, date: datetime) -> Optional[float]:
        """Check cache before making API call"""

    def save_to_cache(self, address: str, date: datetime, price: float) -> None:
        """Cache historical prices (they never change)"""

@dataclass
class HourlyPrice:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
```

**Bootstrap Strategy**:

1. **Batch Processing**: Process messages in batches of 100
2. **Parallel Tokens**: Process multiple tokens simultaneously (max 5 concurrent)
3. **Rate Limiting**: Respect Twelve Data API limits (800 calls/day)
4. **Caching**: Cache all historical prices (they never change)
5. **Resumability**: Save progress every 100 messages for crash recovery
6. **Error Handling**: Skip tokens with missing data, continue processing

**API Call Requirements**:

```python
# Example: 50 channels, 20 tokens per channel = 1000 tokens
# Hourly OHLC approach: 1000 tokens × 30 days × 24 hours = 720,000 API calls
# With caching: ~360,000 API calls (many tokens overlap across channels)
# Time estimate: 360,000 calls ÷ 800 calls/day = ~450 days (single API key)
# Parallel processing: Use 10 API keys to reduce to ~45 days
# Realistic approach: Use 20+ API keys to complete in ~20 days
```

**Bootstrap Progress Tracking**:

```json
{
  "Eric Cryptomans Journal": {
    "channel_name": "Eric Cryptomans Journal",
    "total_messages": 5234,
    "processed_messages": 5234,
    "total_tokens": 487,
    "processed_tokens": 487,
    "successful_outcomes": 452,
    "failed_outcomes": 35,
    "api_calls_made": 14610,
    "start_time": "2025-11-01T00:00:00Z",
    "completion_time": "2025-11-05T14:30:00Z",
    "status": "completed"
  }
}
```

### 2. OutcomeTracker (intelligence/outcome_tracker.py)

**Purpose**: Track signal outcomes from entry to completion, managing checkpoints and ROI calculations.

**Key Classes**:

- `SignalOutcome`: Data class for signal tracking
- `OutcomeTracker`: Main tracking component

**Interface**:

```python
@dataclass
class SignalOutcome:
    message_id: int
    channel_id: str
    channel_name: str
    timestamp: datetime
    address: str
    symbol: str

    # Entry data
    entry_price: float
    entry_confidence: float  # 0.0-1.0
    entry_source: str  # "message_text", "twelve_data", "current_price"

    # Sentiment data
    sentiment: str  # positive, negative, neutral
    sentiment_score: float
    hdrb_score: float
    confidence: float

    # Checkpoint data
    checkpoints: dict[str, CheckpointData]  # "1h", "4h", "24h", "3d", "7d", "30d"

    # Outcome data
    ath_price: float
    ath_multiplier: float
    ath_timestamp: datetime
    days_to_ath: float
    current_multiplier: float

    # Market data
    market_tier: str  # micro, small, mid, large
    risk_level: str
    risk_score: float

    # Status
    status: str  # "completed" (historical), "in_progress" (live), "data_unavailable"
    is_complete: bool
    completion_reason: str  # "30d_elapsed", "90%_loss", "zero_volume", "historical"
    is_winner: bool  # ATH >= 2x
    outcome_category: str  # moon, great, good, break_even, loss

@dataclass
class CheckpointData:
    timestamp: datetime
    price: float
    roi_percentage: float
    roi_multiplier: float
    reached: bool

class OutcomeTracker:
    def __init__(self, config: Config):
        self.outcomes: dict[str, SignalOutcome] = {}
        self.load_outcomes()

    async def track_signal(self, message_id: int, channel_name: str,
                          address: str, entry_price: float,
                          entry_confidence: float, entry_source: str) -> None:
        """Start tracking a new signal"""

    async def update_price(self, address: str, current_price: float) -> None:
        """Update price and check checkpoints"""

    async def check_checkpoints(self, outcome: SignalOutcome,
                                current_price: float) -> list[str]:
        """Check which checkpoints have been reached"""

    def calculate_roi(self, entry_price: float, current_price: float) -> tuple[float, float]:
        """
        Calculate ROI percentage and multiplier

        Formula (validated by Investopedia):
        - ROI Percentage = ((current_price - entry_price) / entry_price) * 100
        - ROI Multiplier = current_price / entry_price

        Examples:
        - Entry $1.00, Current $2.00 → ROI = 100%, Multiplier = 2.0x
        - Entry $1.47, Current $4.78 → ROI = 225.2%, Multiplier = 3.252x
        - Entry $14.96, Current $13.94 → ROI = -6.8%, Multiplier = 0.932x

        Returns:
            tuple[float, float]: (roi_percentage, roi_multiplier)
        """

    async def check_stop_conditions(self, outcome: SignalOutcome) -> tuple[bool, str]:
        """Check if tracking should stop"""

    async def complete_signal(self, address: str, reason: str) -> SignalOutcome:
        """Mark signal as complete and return final outcome"""

    def save_outcomes(self) -> None:
        """Save outcomes to JSON"""
```

**Entry Price Logic**:

1. **Message Text Parsing** (Priority 1, Confidence 0.85-0.95):

   - Regex patterns: `r"bought at \$(\d+\.?\d*)"`, `r"entry \$(\d+\.?\d*)"`, `r"@\$(\d+\.?\d*)"`
   - Validate price is reasonable (> $0.000001, < $1,000,000)
   - Confidence based on pattern match quality

2. **Twelve Data API** (Priority 2, Confidence 0.70-0.85):

   - Query historical price at message timestamp
   - Handle API errors gracefully
   - Confidence based on data freshness

3. **Current Price Fallback** (Priority 3, Confidence 0.20-0.40):
   - Use current price from PriceEngine
   - Low confidence due to time gap
   - Better than no data

**Historical ROI Validation** (Pump-and-Dump Detection):

When a token is first tracked, query Twelve Data for the full day's price data:

```python
async def validate_entry_timing(self, address: str, entry_price: float,
                               message_timestamp: datetime) -> dict:
    """
    Validate entry price against historical data to detect pump-and-dump timing

    Returns:
        {
            "day_start_price": float,
            "day_high": float,
            "day_low": float,
            "entry_vs_start_roi": float,  # ROI from day start to entry
            "is_potential_pump": bool,
            "confidence_adjustment": float  # -0.2 if pump detected
        }
    """
    # Query Twelve Data for message date
    historical_data = await self.twelve_data.get_day_data(
        address,
        message_timestamp.date()
    )

    # Calculate ROI from day start to entry
    entry_vs_start_roi = (entry_price - historical_data.open) / historical_data.open

    # Detect pump: entry price >50% above day start
    is_potential_pump = entry_vs_start_roi > 0.50

    # Reduce confidence if pump detected
    confidence_adjustment = -0.2 if is_potential_pump else 0.0

    return {
        "day_start_price": historical_data.open,
        "day_high": historical_data.high,
        "day_low": historical_data.low,
        "entry_vs_start_roi": entry_vs_start_roi,
        "is_potential_pump": is_potential_pump,
        "confidence_adjustment": confidence_adjustment
    }
```

**Example Pump Detection**:

```
Message: "Bought $SCAM at $5.00" (timestamp: Nov 10, 2:00 PM)

Historical Data (Nov 10):
  - Day Start (12:00 AM): $2.00
  - Day High: $6.50
  - Day Low: $1.95
  - Entry Price: $5.00 (2:00 PM)

Analysis:
  - Entry vs Start ROI: ($5.00 - $2.00) / $2.00 = 150%
  - Is Potential Pump: YES (>50% threshold)
  - Confidence Adjustment: -0.2 (reduce from 0.85 to 0.65)
  - Flag: "⚠️ Signal came after 150% pump - caution advised"

Outcome Tracking:
  - If token dumps after entry → validates pump-and-dump pattern
  - If token continues up → false positive, but caution was warranted
  - Channel reputation adjusted based on actual outcome
```

**Why This Matters**:

1. **Detects Late Signals**: Channel calls token after it already pumped
2. **Protects Traders**: Warns about entering at inflated prices
3. **Reputation Accuracy**: Channels calling pumped tokens get lower scores
4. **Validates Timing**: Distinguishes early calls from late FOMO calls

**Checkpoint Management**:

```python
CHECKPOINTS = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30)
}

# At each checkpoint, calculate and store:
# 1. ROI Percentage = ((price - entry_price) / entry_price) * 100
# 2. ROI Multiplier = price / entry_price
# 3. Timestamp when checkpoint was reached
# 4. Price at checkpoint

# Example checkpoint data:
# Entry: $1.47
# 1h checkpoint: $1.52 → ROI = 3.4%, Multiplier = 1.034x
# 4h checkpoint: $1.89 → ROI = 28.6%, Multiplier = 1.286x
# 24h checkpoint: $4.78 → ROI = 225.2%, Multiplier = 3.252x (ATH)
```

**Stop Conditions**:

- 30 days elapsed (primary)
- 90% loss from ATH (dead token)
- Zero volume for 48 hours (inactive)

### 2. ChannelReputation (intelligence/channel_reputation.py)

**Purpose**: Calculate and maintain reputation scores for channels using temporal difference learning.

**Key Classes**:

- `ChannelReputation`: Reputation data container
- `ReputationEngine`: Calculation and learning engine

**Interface**:

```python
@dataclass
class ChannelReputation:
    channel_id: str
    channel_name: str

    # Outcome metrics
    total_signals: int
    winning_signals: int  # ATH >= 2x
    losing_signals: int  # < 1.0x
    neutral_signals: int  # 1.0x - 2.0x
    win_rate: float  # 0-1

    # ROI metrics (all in multiplier format)
    average_roi: float  # Mean ATH multiplier (e.g., 1.85 = 85% average gain)
    median_roi: float   # Median ATH multiplier (less affected by outliers)
    best_roi: float     # Best ATH multiplier (e.g., 4.78 = 378% gain)
    worst_roi: float    # Worst ATH multiplier (e.g., 0.93 = -7% loss)
    roi_std_dev: float  # Standard deviation of ROI (measures volatility)

    # Risk-adjusted metrics
    sharpe_ratio: float  # (avg_roi - 1.0) / std_dev (validated by Investopedia)
                         # Example: avg_roi=1.85, std_dev=0.95 → sharpe=0.89
                         # Higher sharpe = better risk-adjusted returns
    risk_adjusted_roi: float  # ROI weighted by risk level of tokens called

    # Time metrics
    avg_time_to_ath: float  # Days
    avg_time_to_2x: float  # Days (for winners only)
    speed_score: float  # 0-100, faster = higher

    # Confidence metrics
    avg_confidence: float  # Average entry price confidence
    avg_hdrb_score: float

    # Tier-specific performance
    tier_performance: dict[str, TierPerformance]  # micro, small, mid, large

    # Reputation score
    reputation_score: float  # 0-100
    reputation_tier: str  # Elite, Excellent, Good, Average, Poor, Unreliable, Unproven

    # Learning data (Temporal Difference Learning)
    expected_roi: float  # TD learning prediction (multiplier format)
                         # Example: 1.92 means system predicts 92% average gain
                         # Updated after each signal: new = old + 0.1 * (actual - old)
    prediction_error_history: list[float]  # Last 100 prediction errors
                                           # Example: [0.15, -0.08, 0.22, -0.05]
                                           # Positive = underestimated, Negative = overestimated

    # Metadata
    first_signal_date: datetime
    last_signal_date: datetime
    last_updated: datetime

@dataclass
class TierPerformance:
    total_calls: int
    winning_calls: int
    win_rate: float
    avg_roi: float
    sharpe_ratio: float

class ReputationEngine:
    def __init__(self, config: Config):
        self.reputations: dict[str, ChannelReputation] = {}
        self.learning_rate: float = 0.1  # alpha for TD learning
        self.recency_decay: float = 0.01  # lambda for exponential decay
        self.load_reputations()

    async def update_reputation(self, channel_name: str,
                               outcome: SignalOutcome) -> None:
        """Update reputation based on signal outcome"""

    def calculate_reputation_score(self, rep: ChannelReputation) -> float:
        """Calculate composite reputation score (0-100)"""

    def calculate_win_rate(self, rep: ChannelReputation) -> float:
        """Calculate win rate with recency weighting"""

    def calculate_sharpe_ratio(self, rep: ChannelReputation) -> float:
        """Calculate risk-adjusted returns"""

    def calculate_speed_score(self, rep: ChannelReputation) -> float:
        """Calculate speed score (0-100)"""

    def apply_td_learning(self, rep: ChannelReputation,
                         actual_roi: float) -> None:
        """Apply temporal difference learning"""

    def determine_tier(self, score: float, total_signals: int) -> str:
        """Determine reputation tier"""

    def get_reputation(self, channel_name: str) -> ChannelReputation:
        """Get reputation for channel"""

    def save_reputations(self) -> None:
        """Save reputations to JSON"""
```

**Reputation Score Formula**:

```python
def calculate_reputation_score(self, rep: ChannelReputation) -> float:
    """
    Weighted composite score:
    - Win Rate: 30%
    - Average ROI: 25%
    - Sharpe Ratio: 20%
    - Speed Score: 15%
    - Confidence: 10%
    """
    # Normalize components to 0-100 scale
    win_rate_score = rep.win_rate * 100

    # ROI score: normalize to 0-100 (2x = 50, 5x = 100)
    roi_score = min(100, (rep.average_roi - 1.0) * 50)

    # Sharpe score: normalize to 0-100 (sharpe of 2 = 100)
    sharpe_score = min(100, rep.sharpe_ratio * 50)

    # Speed score: already 0-100
    speed_score = rep.speed_score

    # Confidence score: already 0-100
    confidence_score = rep.avg_confidence * 100

    # Weighted composite
    score = (
        win_rate_score * 0.30 +
        roi_score * 0.25 +
        sharpe_score * 0.20 +
        speed_score * 0.15 +
        confidence_score * 0.10
    )

    return min(100, max(0, score))
```

**Temporal Difference Learning**:

```python
def apply_td_learning(self, rep: ChannelReputation, actual_roi: float) -> None:
    """
    TD Learning Formula: V(s) ← V(s) + α[R - V(s)]

    Where:
    - V(s) = expected_roi (current prediction)
    - α = learning_rate (0.1)
    - R = actual_roi (observed outcome)
    """
    prediction_error = actual_roi - rep.expected_roi
    rep.expected_roi += self.learning_rate * prediction_error
    rep.prediction_error_history.append(prediction_error)

    # Keep only last 100 errors
    if len(rep.prediction_error_history) > 100:
        rep.prediction_error_history = rep.prediction_error_history[-100:]
```

**Reputation Tiers**:

```python
REPUTATION_TIERS = {
    "Elite": (90, 100),      # Top 10% performers
    "Excellent": (75, 90),   # Strong performance
    "Good": (60, 75),        # Above average
    "Average": (40, 60),     # Mixed results
    "Poor": (20, 40),        # Below average
    "Unreliable": (0, 20),   # Consistently poor
    "Unproven": None         # < 10 signals
}
```

### 3. Integration with Existing Components

#### PerformanceTracker Integration

**Modifications to core/performance_tracker.py**:

```python
class PerformanceTracker:
    def __init__(self, config: Config, outcome_tracker: OutcomeTracker):
        self.outcome_tracker = outcome_tracker
        # ... existing code ...

    async def track_new_token(self, address: str, message_id: int,
                             channel_name: str, entry_price: float,
                             entry_confidence: float, entry_source: str):
        """Track new token and notify OutcomeTracker"""
        # Existing tracking logic
        await self.add_token(address, entry_price, message_id)

        # NEW: Notify OutcomeTracker
        await self.outcome_tracker.track_signal(
            message_id=message_id,
            channel_name=channel_name,
            address=address,
            entry_price=entry_price,
            entry_confidence=entry_confidence,
            entry_source=entry_source
        )

    async def update_prices(self):
        """Update prices and notify OutcomeTracker"""
        for address, data in self.tracked_tokens.items():
            current_price = await self.price_engine.get_price(address)

            # Existing update logic
            self.update_ath(address, current_price)

            # NEW: Notify OutcomeTracker
            await self.outcome_tracker.update_price(address, current_price)
```

#### MessageProcessor Integration

**Modifications to core/message_processor.py**:

```python
class MessageProcessor:
    def __init__(self, config: Config, reputation_engine: ReputationEngine):
        self.reputation_engine = reputation_engine
        # ... existing code ...

    async def process_message(self, message: TelegramMessage) -> ProcessedMessage:
        """Process message and add reputation data"""
        # Existing processing logic
        processed = await self.extract_and_score(message)

        # NEW: Add channel reputation
        reputation = self.reputation_engine.get_reputation(message.channel_name)
        processed.channel_reputation_score = reputation.reputation_score
        processed.channel_reputation_tier = reputation.reputation_tier
        processed.channel_win_rate = reputation.win_rate
        processed.channel_expected_roi = reputation.expected_roi

        # NEW: Adjust confidence based on reputation
        if reputation.total_signals >= 10:
            # Boost confidence for high-reputation channels
            reputation_factor = reputation.reputation_score / 100
            processed.confidence *= (0.7 + 0.3 * reputation_factor)

        return processed
```

#### DataOutput Integration

**Modifications to core/data_output.py**:

```python
class DataOutput:
    def __init__(self, config: Config, reputation_engine: ReputationEngine):
        self.reputation_engine = reputation_engine
        # ... existing code ...

    async def output_messages(self, messages: list[ProcessedMessage]):
        """Output messages with reputation columns"""
        # Add reputation columns to CSV
        df = pd.DataFrame([{
            # ... existing columns ...
            'channel_reputation_score': msg.channel_reputation_score,
            'channel_reputation_tier': msg.channel_reputation_tier,
            'channel_win_rate': msg.channel_win_rate,
            'channel_expected_roi': msg.channel_expected_roi,
        } for msg in messages])

        # Save to CSV
        df.to_csv('output/messages.csv', index=False)

        # Update Google Sheets
        await self.update_sheets(df)

    async def output_channel_reputation(self):
        """Output CHANNEL_REPUTATION table"""
        reputations = self.reputation_engine.reputations.values()

        df = pd.DataFrame([{
            'channel_name': rep.channel_name,
            'total_signals': rep.total_signals,
            'win_rate': f"{rep.win_rate:.1%}",
            'avg_roi': f"{rep.average_roi:.2f}x",
            'sharpe_ratio': f"{rep.sharpe_ratio:.2f}",
            'reputation_score': rep.reputation_score,
            'reputation_tier': rep.reputation_tier,
            'avg_time_to_ath': f"{rep.avg_time_to_ath:.1f} days",
            'last_updated': rep.last_updated.strftime('%Y-%m-%d %H:%M')
        } for rep in reputations])

        # Save to CSV
        df.to_csv('output/channel_reputation.csv', index=False)

        # Update Google Sheets with conditional formatting
        await self.update_reputation_sheet(df)
```

## Historical Bootstrap Workflow

### Bootstrap Execution Flow

**Step 1: Initialize Bootstrap**

```python
bootstrap = HistoricalBootstrap(config, scraper, processor, tracker, reputation)
channels = ["Eric Cryptomans Journal", "Crypto Signals Pro", ...]
results = await bootstrap.bootstrap_all_channels(channels)
```

**Step 2: For Each Channel**

```python
# 1. Scrape all historical messages
messages = await historical_scraper.scrape_channel(channel_name, from_beginning=True)
# Returns: 5,000+ messages spanning 2+ years

# 2. Process messages in batches
for batch in chunks(messages, 100):
    processed = await message_processor.process_batch(batch)

    # 3. Extract token mentions
    for msg in processed:
        if msg.addresses:
            # 4. Get historical entry price
            entry_price, confidence, source = await get_historical_entry_price(
                msg.addresses[0],
                msg.timestamp
            )

            # 5. Get 30 days of price data
            outcome = await get_historical_outcome(
                msg.addresses[0],
                entry_price,
                msg.timestamp
            )

            # 6. Store completed outcome
            await outcome_tracker.store_outcome(outcome)

    # 7. Update progress
    progress.processed_messages += len(batch)
    save_bootstrap_progress()

# 8. Calculate initial reputation
reputation = await reputation_engine.calculate_reputation(channel_name)
await reputation_engine.save_reputations()
```

**Step 3: Transition to Live Monitoring**

```python
# Bootstrap complete, reputation scores established
# Start live monitoring with pre-calculated reputations
await start_live_monitoring()
```

### Historical vs Live Data Comparison

| Aspect          | Historical Data               | Live Data                              |
| --------------- | ----------------------------- | -------------------------------------- |
| **Source**      | HistoricalScraper             | TelegramMonitor                        |
| **Processing**  | Batch (100s at once)          | Real-time (one at a time)              |
| **Entry Price** | Twelve Data at timestamp      | Message text or current price          |
| **Outcome**     | Known (can look back 30 days) | Unknown (tracking in progress)         |
| **Status**      | "completed"                   | "in_progress"                          |
| **API Calls**   | Daily OHLC (30 calls/token)   | 2-hour polling (360 calls/token/month) |
| **Purpose**     | Establish baseline reputation | Continue learning                      |
| **Timeline**    | Days to weeks (one-time)      | Ongoing (continuous)                   |

### Bootstrap Performance Estimates

**Single Channel Bootstrap**:

- Messages: 5,000
- Token mentions: 500
- API calls: 500 tokens × 30 days = 15,000 calls
- Time (800 calls/day limit): ~19 days
- Time (parallel with 5 API keys): ~4 days

**50 Channels Bootstrap**:

- Total messages: 250,000
- Total tokens: 25,000
- API calls (with caching): ~400,000 calls
- Time (single API key): ~500 days (not feasible)
- Time (5 API keys): ~100 days
- Time (10 API keys): ~50 days

**Optimization Strategies**:

1. **Prioritize Recent History**: Bootstrap last 90 days first (most relevant)
2. **Parallel Processing**: Use multiple API keys
3. **Incremental Bootstrap**: Bootstrap channels one at a time, start live monitoring as each completes
4. **Selective Bootstrap**: Only bootstrap top 20 channels initially
5. **Background Bootstrap**: Run bootstrap in background while live monitoring active channels

### Recommended Bootstrap Approach

**Phase 0: Quick Start (Day 1)**

- Bootstrap top 10 channels with last 30 days only
- ~3,000 API calls total
- Completes in 4 days with single API key
- Start live monitoring immediately with partial reputation

**Phase 1: Full Bootstrap (Weeks 1-4)**

- Bootstrap all 50 channels with complete history
- Run in background while live monitoring active
- Use 5 API keys for parallel processing
- Complete in ~20 days

**Phase 2: Continuous Operation (Ongoing)**

- Live monitoring with established reputations
- New channels bootstrap in background
- Reputation updates from live signals

## ROI Calculation Details

### ROI Formula (Validated by Investopedia)

**Basic Formula**:

```
ROI Percentage = ((Current Value - Cost) / Cost) × 100%
ROI Multiplier = Current Value / Cost
```

**Our Implementation**:

```python
def calculate_roi(entry_price: float, current_price: float) -> tuple[float, float]:
    """
    Calculate ROI in both percentage and multiplier formats

    Args:
        entry_price: Price when token was first mentioned
        current_price: Current or checkpoint price

    Returns:
        (roi_percentage, roi_multiplier)

    Examples:
        Entry $1.00, Current $2.00:
            ROI% = ((2.00 - 1.00) / 1.00) × 100 = 100%
            Multiplier = 2.00 / 1.00 = 2.0x

        Entry $1.47, Current $4.78:
            ROI% = ((4.78 - 1.47) / 1.47) × 100 = 225.2%
            Multiplier = 4.78 / 1.47 = 3.252x

        Entry $14.96, Current $13.94:
            ROI% = ((13.94 - 14.96) / 14.96) × 100 = -6.8%
            Multiplier = 13.94 / 14.96 = 0.932x
    """
    roi_percentage = ((current_price - entry_price) / entry_price) * 100
    roi_multiplier = current_price / entry_price
    return (roi_percentage, roi_multiplier)
```

### ROI Storage Format

We store ROI in **both formats** for flexibility:

1. **Percentage Format** (e.g., 225.2%):

   - Human-readable
   - Used in output displays
   - Easier to understand gains/losses

2. **Multiplier Format** (e.g., 3.252x):
   - Used in calculations
   - Easier to compare (2x vs 3x)
   - Standard in crypto community

### ROI at Checkpoints

At each checkpoint (1h, 4h, 24h, 3d, 7d, 30d), we calculate and store:

```python
checkpoint_data = {
    "timestamp": datetime.now(),
    "price": current_price,
    "roi_percentage": ((current_price - entry_price) / entry_price) * 100,
    "roi_multiplier": current_price / entry_price,
    "reached": True
}
```

**Example Timeline** (AVICI token):

```
Entry: $1.47 (Nov 10, 10:30 AM)

1h checkpoint (11:30 AM):
  Price: $1.52
  ROI: 3.4% / 1.034x

4h checkpoint (2:30 PM):
  Price: $1.89
  ROI: 28.6% / 1.286x

24h checkpoint (Nov 11, 10:30 AM):
  Price: $4.78 (ATH)
  ROI: 225.2% / 3.252x ← This is the ATH ROI

Current (Nov 11, 10:00 PM):
  Price: $4.29
  ROI: 191.8% / 2.918x
```

### ATH ROI vs Current ROI

- **ATH ROI**: Best ROI achieved since mention (used for reputation)
- **Current ROI**: Current ROI (may be lower than ATH)

```python
# ATH ROI (used for channel reputation)
ath_roi_percentage = ((ath_price - entry_price) / entry_price) * 100
ath_roi_multiplier = ath_price / entry_price

# Current ROI (for tracking)
current_roi_percentage = ((current_price - entry_price) / entry_price) * 100
current_roi_multiplier = current_price / entry_price
```

### Win/Loss Classification by ROI

```python
def classify_outcome(ath_multiplier: float) -> tuple[bool, str]:
    """
    Classify signal outcome based on ATH ROI multiplier

    Returns:
        (is_winner, outcome_category)
    """
    if ath_multiplier >= 5.0:
        return (True, "moon")        # 5x+ = 400%+ gain
    elif ath_multiplier >= 3.0:
        return (True, "great")       # 3-5x = 200-400% gain
    elif ath_multiplier >= 2.0:
        return (True, "good")        # 2-3x = 100-200% gain
    elif ath_multiplier >= 1.0:
        return (False, "break_even") # 1-2x = 0-100% gain
    else:
        return (False, "loss")       # <1x = negative ROI
```

### Average ROI Calculation

```python
def calculate_average_roi(outcomes: list[SignalOutcome]) -> float:
    """
    Calculate average ROI across all signals
    Uses ATH multiplier for each signal

    Example:
        Signal 1: 3.252x (AVICI)
        Signal 2: 0.932x (NKP)
        Signal 3: 2.150x (TOKEN3)

        Average = (3.252 + 0.932 + 2.150) / 3 = 2.111x
        This means 111% average gain across all signals
    """
    if not outcomes:
        return 1.0  # No signals = no gain/loss

    total_roi = sum(outcome.ath_multiplier for outcome in outcomes)
    return total_roi / len(outcomes)
```

## Data Models

### Signal Outcome Model

```python
@dataclass
class SignalOutcome:
    # Identity
    message_id: int
    channel_id: str
    channel_name: str
    timestamp: datetime
    address: str
    symbol: str

    # Entry data
    entry_price: float
    entry_confidence: float
    entry_source: str

    # Signal quality
    sentiment: str
    sentiment_score: float
    hdrb_score: float
    confidence: float

    # Checkpoints
    checkpoints: dict[str, CheckpointData]

    # Outcome
    ath_price: float
    ath_multiplier: float
    ath_timestamp: datetime
    days_to_ath: float
    current_multiplier: float

    # Market context
    market_tier: str
    risk_level: str
    risk_score: float

    # Status
    is_complete: bool
    completion_reason: str
    is_winner: bool
    outcome_category: str
```

### Channel Reputation Model

```python
@dataclass
class ChannelReputation:
    # Identity
    channel_id: str
    channel_name: str

    # Outcome metrics
    total_signals: int
    winning_signals: int
    losing_signals: int
    neutral_signals: int
    win_rate: float

    # ROI metrics
    average_roi: float
    median_roi: float
    best_roi: float
    worst_roi: float
    roi_std_dev: float

    # Risk-adjusted
    sharpe_ratio: float
    risk_adjusted_roi: float

    # Time metrics
    avg_time_to_ath: float
    avg_time_to_2x: float
    speed_score: float

    # Confidence
    avg_confidence: float
    avg_hdrb_score: float

    # Tier-specific
    tier_performance: dict[str, TierPerformance]

    # Reputation
    reputation_score: float
    reputation_tier: str

    # Learning
    expected_roi: float
    prediction_error_history: list[float]

    # Metadata
    first_signal_date: datetime
    last_signal_date: datetime
    last_updated: datetime
```

### JSON Storage Format

**data/reputation/channels.json**:

```json
{
  "Eric Cryptomans Journal": {
    "channel_id": "eric_cryptomans",
    "channel_name": "Eric Cryptomans Journal",
    "total_signals": 15,
    "winning_signals": 10,
    "losing_signals": 3,
    "neutral_signals": 2,
    "win_rate": 0.667,
    "average_roi": 1.85,
    "median_roi": 1.65,
    "best_roi": 4.78,
    "worst_roi": 0.93,
    "roi_std_dev": 0.95,
    "sharpe_ratio": 0.89,
    "risk_adjusted_roi": 1.72,
    "avg_time_to_ath": 2.3,
    "avg_time_to_2x": 1.8,
    "speed_score": 78.5,
    "avg_confidence": 0.82,
    "avg_hdrb_score": 65.3,
    "tier_performance": {
      "micro": {
        "total_calls": 8,
        "winning_calls": 6,
        "win_rate": 0.75,
        "avg_roi": 2.1,
        "sharpe_ratio": 0.95
      },
      "small": {
        "total_calls": 5,
        "winning_calls": 3,
        "win_rate": 0.6,
        "avg_roi": 1.5,
        "sharpe_ratio": 0.78
      },
      "mid": {
        "total_calls": 2,
        "winning_calls": 1,
        "win_rate": 0.5,
        "avg_roi": 1.2,
        "sharpe_ratio": 0.45
      }
    },
    "reputation_score": 78.5,
    "reputation_tier": "Excellent",
    "expected_roi": 1.92,
    "prediction_error_history": [0.15, -0.08, 0.22, -0.05],
    "first_signal_date": "2025-10-15T10:30:00Z",
    "last_signal_date": "2025-11-10T14:22:00Z",
    "last_updated": "2025-11-11T09:15:00Z"
  }
}
```

**data/reputation/signal_outcomes.json**:

```json
{
  "5gb4...": {
    "message_id": 12345,
    "channel_name": "Eric Cryptomans Journal",
    "timestamp": "2025-11-10T10:30:00Z",
    "address": "5gb4...",
    "symbol": "AVICI",
    "entry_price": 1.47,
    "entry_confidence": 0.85,
    "entry_source": "message_text",
    "sentiment": "positive",
    "sentiment_score": 0.78,
    "hdrb_score": 68.5,
    "confidence": 0.82,
    "checkpoints": {
      "1h": {
        "timestamp": "2025-11-10T11:30:00Z",
        "price": 1.52,
        "roi_percentage": 3.4,
        "roi_multiplier": 1.034,
        "reached": true
      },
      "4h": {
        "timestamp": "2025-11-10T14:30:00Z",
        "price": 1.89,
        "roi_percentage": 28.6,
        "roi_multiplier": 1.286,
        "reached": true
      },
      "24h": {
        "timestamp": "2025-11-11T10:30:00Z",
        "price": 4.78,
        "roi_percentage": 225.2,
        "roi_multiplier": 3.252,
        "reached": true
      }
    },
    "ath_price": 4.78,
    "ath_multiplier": 3.252,
    "ath_timestamp": "2025-11-11T10:30:00Z",
    "days_to_ath": 1.0,
    "current_multiplier": 2.918,
    "market_tier": "small",
    "risk_level": "high",
    "risk_score": 0.75,
    "is_complete": false,
    "completion_reason": null,
    "is_winner": true,
    "outcome_category": "great"
  }
}
```

## Error Handling

### Entry Price Errors

- **Message parsing fails**: Fall back to Twelve Data API
- **Twelve Data unavailable**: Fall back to current price with low confidence
- **All sources fail**: Log error, skip signal tracking
- **Price discrepancy >10%**: Flag for review, use highest confidence source

### Checkpoint Errors

- **Price API fails**: Retry 3 times with exponential backoff
- **Checkpoint missed**: Mark as "not reached", continue tracking
- **Time drift**: Use actual timestamp, adjust checkpoint window ±10%

### Reputation Calculation Errors

- **Insufficient data**: Return "Unproven" tier, score = 50.0
- **Division by zero**: Handle gracefully (e.g., std_dev = 0 → sharpe = 0)
- **Invalid ROI values**: Clamp to reasonable range (0.01x - 100x)
- **JSON corruption**: Log error, initialize with empty data

### Learning Errors

- **Prediction error too large**: Cap at ±10x to prevent instability
- **Learning rate issues**: Use fixed alpha = 0.1, no dynamic adjustment
- **History overflow**: Keep only last 100 errors per channel

## Testing Strategy

### Unit Tests

**OutcomeTracker Tests**:

- Test entry price extraction from message text
- Test checkpoint detection and ROI calculation
- Test stop condition logic (30d, 90% loss, zero volume)
- Test outcome completion and categorization

**ReputationEngine Tests**:

- Test reputation score calculation with known inputs
- Test TD learning updates
- Test tier classification
- Test recency weighting

**Integration Tests**:

- Test PerformanceTracker → OutcomeTracker flow
- Test OutcomeTracker → ReputationEngine flow
- Test MessageProcessor reputation lookup
- Test DataOutput reputation columns

### Manual Verification Tests

1. **Entry Price Accuracy Test**:

   - Create test message: "Bought $AVICI at $1.47"
   - Verify entry_price = 1.47, confidence = 0.85-0.95
   - Test Twelve Data fallback with unavailable message price
   - Test current price fallback with both unavailable

2. **Checkpoint Tracking Test**:

   - Track token for 24 hours
   - Verify checkpoints: 1h, 4h, 24h reached
   - Verify ROI calculations at each checkpoint
   - Verify ATH tracking

3. **Reputation Calculation Test**:

   - Create channel with 10 signals (7 winners, 3 losers)
   - Verify win_rate = 0.7
   - Verify reputation_score calculation
   - Verify tier = "Good" or "Excellent"

4. **TD Learning Test**:

   - Initialize channel with expected_roi = 1.5
   - Complete signal with actual_roi = 2.0
   - Verify expected_roi updated: 1.5 + 0.1 \* (2.0 - 1.5) = 1.55
   - Verify prediction_error_history updated

5. **Output Integration Test**:
   - Process messages with reputation data
   - Verify CSV has reputation columns
   - Verify Google Sheets CHANNEL_REPUTATION table
   - Verify conditional formatting (green >75, yellow 40-75, red <40)

### Pipeline Verification

**Success Criteria**:

- Signal outcomes tracked from entry to completion
- Checkpoints reached and ROI calculated correctly
- Channel reputation updated after each signal
- Reputation scores reflect actual performance
- TD learning improves predictions over time
- Output includes reputation data
- System runs stable for 7+ days

## Performance Considerations

### Computational Performance

**OutcomeTracker**:

- Memory: ~1KB per tracked signal
- 100 active signals = ~100KB memory
- Checkpoint checks: O(n) where n = active signals
- Target: < 100ms per price update cycle

**ReputationEngine**:

- Memory: ~5KB per channel
- 50 channels = ~250KB memory
- Reputation calculation: O(1) per channel
- Target: < 50ms per reputation update

**Overall Impact**:

- Additional memory: < 1MB for 100 signals + 50 channels
- Additional CPU: < 5% during price updates
- No impact on message processing latency

### API Usage

**Twelve Data API** (for entry price):

- Only called when message text parsing fails
- Estimated: 20% of signals = 10 calls/day
- Well within free tier limits

**Price API** (existing):

- No additional calls (reuse PerformanceTracker data)
- Hybrid polling already optimized

### Storage Performance

**JSON Files**:

- channels.json: ~5KB per channel, 50 channels = ~250KB
- signal_outcomes.json: ~1KB per signal, 1000 signals = ~1MB
- Write frequency: After each signal completion (~10/day)
- Read frequency: On startup only

**Optimization**:

- Lazy loading: Load only active signals
- Periodic cleanup: Archive completed signals >90 days old
- Compression: Use gzip for archived data

## Security Considerations

### Data Integrity

- **Reputation tampering**: JSON files are read-only during runtime
- **Price manipulation**: Use multiple price sources with confidence scoring
- **Entry price fraud**: Cross-validate message text with Twelve Data
- **Checkpoint manipulation**: Timestamps are immutable once set

### Privacy

- **Channel data**: No personal information stored
- **Message content**: Only prices and addresses extracted
- **User data**: No user-specific tracking

### Validation

- **Input validation**: All prices validated (> 0, < $1M)
- **ROI bounds**: Clamp to 0.01x - 100x range
- **Confidence bounds**: Clamp to 0.0 - 1.0 range
- **Timestamp validation**: Reject future timestamps

## Dependencies

### New Python Packages

```
# No new packages required!
# Uses existing: pandas, asyncio, json, datetime
```

### External APIs

- **Twelve Data API** (optional, for entry price fallback):
  - Free tier: 800 calls/day
  - Used only when message parsing fails
  - Graceful degradation if unavailable

### System Requirements

- Python 3.8+
- Existing dependencies from Parts 1-7
- ~2MB additional disk space for reputation data

## Future Extensibility

### Phase 2 Enhancements

1. **Comparative Analysis**:

   - Rank channels by reputation
   - Side-by-side channel comparison
   - Best performers by market tier

2. **Predictive Scoring**:

   - Use reputation to predict signal success
   - Weight signals from high-reputation channels
   - Alert on high-reputation channel calls

3. **Reputation Decay**:

   - Time-based decay for inactive channels
   - Prevent "resting on laurels"
   - Require recent activity for high tiers

4. **Market Condition Adjustment**:

   - Bull market vs bear market performance
   - Volatility-adjusted scoring
   - Macro trend correlation

5. **Multi-Channel Consensus**:
   - Track when multiple channels call same token
   - Consensus signals = higher confidence
   - Divergence signals = caution flag

### Integration Points

- **Alert System**: Notify on high-reputation channel calls
- **Portfolio Optimizer**: Weight positions by channel reputation
- **Risk Manager**: Adjust position size based on channel tier
- **Backtesting**: Historical reputation analysis

## Design Decisions

### 1. Why Temporal Difference Learning?

**Alternatives Considered**:

- Simple moving average (too slow to adapt)
- Exponential moving average (no prediction error feedback)
- Q-learning (too complex for this use case)

**Decision**: TD learning provides:

- Fast adaptation to changing channel quality
- Prediction error feedback loop
- Simple implementation (one-line update)
- Proven in reinforcement learning literature

### 2. Why 30-Day Tracking Window?

**Alternatives Considered**:

- 7 days (too short, misses delayed pumps)
- 60 days (too long, wastes resources)
- 90 days (excessive for meme coins)

**Decision**: 30 days because:

- Captures full pump-dump cycle (validated by MCP research)
- Allows for delayed pumps (some take 2 weeks)
- Not too long (most meme coins dead by 30 days)
- Can extend to 90 days for sustained growth

### 3. Why 90% Loss Stop Condition?

**Alternatives Considered**:

- 95% loss (too lenient, rare recovery)
- 99% loss (essentially dead already)
- 80% loss (too aggressive, some recover)

**Decision**: 90% loss because:

- Conservative enough to catch most deaths
- Rare for 90% loss to recover (validated by research)
- Protects against wasting resources
- Can restart tracking if recovery occurs

### 4. Why Weighted Reputation Formula?

**Alternatives Considered**:

- Equal weights (doesn't reflect trader priorities)
- Win rate only (ignores ROI magnitude)
- ROI only (ignores consistency)

**Decision**: Weighted formula (30/25/20/15/10) because:

- Win rate most important psychologically (30%)
- ROI magnitude matters financially (25%)
- Risk-adjusted returns show consistency (20%)
- Speed matters for meme coins (15%)
- Signal quality provides confidence (10%)
- Validated against trading psychology research

### 5. Why Message Text as Primary Entry Price?

**Alternatives Considered**:

- Current price (too inaccurate, time gap)
- Twelve Data only (API dependency, rate limits)
- Average of all sources (dilutes accuracy)

**Decision**: Message text > Twelve Data > Current because:

- Channels state their EXACT entry price
- More accurate than API historical (which may have gaps)
- Confidence scoring handles uncertainty
- Cross-validation flags discrepancies
- Validated by MCP research on reputation systems

### 6. Why Full Historical Bootstrap?

**Alternatives Considered**:

- No bootstrap (start with neutral scores) - Cold start problem, no initial trust signals
- Last 30 days only - Insufficient data for statistical significance
- Last 90 days - Better but still limited sample size
- Full history - Complete track record

**Decision**: Full historical bootstrap because:

- **Statistical Significance**: 100s of signals per channel vs 10-20 from recent data
- **Immediate Value**: Reputation scores meaningful from day one
- **No Cold Start**: Avoid "Unproven" tier for established channels
- **Trend Analysis**: Can see if channel improving/declining over time
- **Fair Comparison**: All channels evaluated on complete history
- **One-Time Cost**: Bootstrap runs once, benefits last forever

**Implementation Strategy**:

- Incremental bootstrap: Process channels one at a time
- Background processing: Bootstrap while live monitoring active
- Prioritize recent data: Last 90 days first for quick value
- Cache aggressively: Historical data never changes
- Parallel processing: Multiple API keys to reduce time

**Trade-offs Accepted**:

- Initial setup time: 9-219 days depending on scope and parallelization
- API call volume: 72K-9M calls depending on history depth (requires many API keys)
- Storage: ~500MB for complete historical outcomes with hourly data (acceptable)
- Complexity: Additional bootstrap component (worth the value)
- Cost: 50-100 Twelve Data API keys required for reasonable completion time
- Pragmatic approach: Start with 30-90 day windows, expand selectively based on value
