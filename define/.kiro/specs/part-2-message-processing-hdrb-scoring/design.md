# Design Document - Part 2: Message Processing + HDRB Scoring

## Overview

Part 2 adds intelligence to the crypto monitoring system by implementing message processing with HDRB scoring and crypto detection. The design focuses on creating a clean, efficient processing pipeline that analyzes messages in real-time, calculates engagement scores using the research-based HDRB formula, detects cryptocurrency mentions, and enriches console output with actionable intelligence.

## Architecture

### System Components

```
crypto-intelligence/
├── core/
│   ├── telegram_monitor.py       # Existing - message source
│   └── message_processor.py      # NEW - HDRB scoring & analysis
├── utils/
│   ├── logger.py                 # Existing - logging
│   └── error_handler.py          # NEW - retry logic & circuit breaker
├── config/
│   └── settings.py               # Update - add processing config
├── main.py                       # Update - integrate processor
└── requirements.txt              # Update - add dependencies
```

### Data Flow

```
Telegram Message Event
    ↓
Message Processor
    ├─→ Extract Engagement Metrics
    ├─→ Calculate HDRB Score (IC formula)
    ├─→ Detect Crypto Mentions
    ├─→ Analyze Sentiment
    └─→ Calculate Confidence Score
    ↓
Processed Message Object
    ↓
Enhanced Console Output
```

## Components and Interfaces

### 1. Error Handler (utils/error_handler.py)

**Purpose**: Provide robust error handling with retry logic and circuit breaker pattern.

**Key Classes**:

- `RetryConfig`: Configuration for retry behavior
- `CircuitBreaker`: Circuit breaker state management
- `ErrorHandler`: Main error handling coordinator

**Interface**:

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0)

    def call(self, func: Callable, *args, **kwargs) -> Any

    def is_open(self) -> bool

    def reset(self) -> None

class ErrorHandler:
    def __init__(self, retry_config: RetryConfig)

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        error_types: tuple = (Exception,),
        **kwargs
    ) -> Any

    def get_error_stats(self) -> dict
```

**Retry Logic**:

- Exponential backoff: delay = base_delay \* (exponential_base ^ attempt)
- Jitter: Add random 0-20% variation to prevent thundering herd
- Max attempts: 3 (configurable)
- Delay sequence: 1s, 2s, 4s (with jitter)

**Circuit Breaker**:

- States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
- Failure threshold: 5 consecutive failures
- Timeout: 60 seconds before attempting recovery
- Automatic reset on success in HALF_OPEN state

**Error Tracking**:

```python
{
    'total_errors': int,
    'retry_attempts': int,
    'circuit_breaker_trips': int,
    'error_types': dict[str, int],
    'last_error': Optional[str]
}
```

### 2. Message Processor (core/message_processor.py)

**Purpose**: Analyze messages using HDRB model, detect crypto mentions, and calculate confidence scores.

**Key Classes**:

- `HDRBScorer`: HDRB score calculation (research-compliant)
- `CryptoDetector`: Cryptocurrency mention detection
- `SentimentAnalyzer`: Sentiment classification
- `MessageProcessor`: Main processing coordinator
- `ProcessedMessage`: Enriched message data container

**Interface**:

```python
@dataclass
class ProcessedMessage:
    # Original message data
    channel_id: str
    channel_name: str
    message_id: int
    message_text: str
    timestamp: datetime

    # Engagement metrics
    forwards: int
    reactions: int
    replies: int
    views: int

    # HDRB scoring
    hdrb_score: float          # 0-100 normalized
    hdrb_raw: float            # Raw IC value

    # Crypto detection
    crypto_mentions: list[str]  # ['BTC', 'ETH', '0x123...']
    is_crypto_relevant: bool

    # Sentiment analysis
    sentiment: str             # 'positive', 'negative', 'neutral'
    sentiment_score: float     # -1.0 to 1.0

    # Confidence
    confidence: float          # 0.0 to 1.0
    is_high_confidence: bool   # confidence >= threshold

    # Processing metadata
    processing_time_ms: float
    error: Optional[str]

class HDRBScorer:
    def calculate_ic(self, forwards: int, reactions: int, replies: int) -> float:
        """Calculate Importance Coefficient using research formula"""
        # IC = forwards + (2 × reactions) + (0.5 × replies)
        return forwards + (2.0 * reactions) + (0.5 * replies)

    def normalize_score(self, ic: float, max_ic: float = 1000.0) -> float:
        """Normalize IC to 0-100 range"""
        return min(100.0, (ic / max_ic) * 100.0)

class CryptoDetector:
    def __init__(self):
        self.ticker_pattern: re.Pattern
        self.eth_address_pattern: re.Pattern
        self.sol_address_pattern: re.Pattern

    def detect_mentions(self, text: str) -> list[str]:
        """Detect all crypto mentions in text"""
        pass

    def is_crypto_relevant(self, mentions: list[str]) -> bool:
        """Determine if message is crypto-relevant"""
        return len(mentions) > 0

class SentimentAnalyzer:
    def __init__(self):
        self.positive_patterns: list[str]
        self.negative_patterns: list[str]

    def analyze(self, text: str) -> tuple[str, float]:
        """Return (sentiment_label, sentiment_score)"""
        pass

class MessageProcessor:
    def __init__(self, config: Config, error_handler: ErrorHandler):
        self.hdrb_scorer = HDRBScorer()
        self.crypto_detector = CryptoDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.error_handler = error_handler
        self.confidence_threshold = config.confidence_threshold
        self.logger = get_logger('MessageProcessor')

    async def process_message(
        self,
        channel_name: str,
        message_text: str,
        timestamp: datetime,
        message_id: int,
        message_obj: Any  # Telethon message object
    ) -> ProcessedMessage:
        """Process message through complete pipeline"""
        pass

    def _extract_engagement_metrics(self, message_obj: Any) -> dict:
        """Extract forwards, reactions, replies, views from Telegram message"""
        pass

    def _calculate_confidence(
        self,
        hdrb_score: float,
        crypto_mentions: list[str],
        sentiment_score: float,
        message_length: int
    ) -> float:
        """Calculate holistic confidence score"""
        # Weights: HDRB (40%), crypto relevance (30%), sentiment (20%), length (10%)
        pass
```

### 3. Configuration Updates (config/settings.py)

**Purpose**: Add processing-related configuration parameters.

**New Configuration**:

```python
@dataclass
class ProcessingConfig:
    confidence_threshold: float = 0.7
    hdrb_max_ic: float = 1000.0
    min_message_length: int = 10
    max_processing_time_ms: float = 100.0

@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    exponential_base: float = 2.0
    jitter: bool = True

class Config:
    # ... existing fields ...
    processing: ProcessingConfig
    retry: RetryConfig

    @classmethod
    def load(cls, env_file: str = '.env') -> 'Config':
        # Load existing config
        # Add processing config from env or defaults
        pass
```

**Environment Variables**:

```
# Existing
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_PHONE=...
LOG_LEVEL=INFO

# New for Part 2
CONFIDENCE_THRESHOLD=0.7
HDRB_MAX_IC=1000.0
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
```

### 4. Main Orchestration Updates (main.py)

**Purpose**: Integrate message processor into the pipeline.

**Updated Flow**:

```python
async def handle_message(event):
    """Enhanced message handler with processing"""
    try:
        # Extract message data
        message_obj = event.message
        channel = await event.get_chat()

        # Process message through pipeline
        processed = await message_processor.process_message(
            channel_name=channel.title,
            message_text=message_obj.text or '',
            timestamp=message_obj.date,
            message_id=message_obj.id,
            message_obj=message_obj
        )

        # Display enriched output
        display_processed_message(processed)

    except Exception as e:
        logger.error(f"Error handling message: {e}")

def display_processed_message(msg: ProcessedMessage):
    """Display message with HDRB scores and analysis"""
    print(f"\n{'='*80}")
    print(f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{msg.channel_name}] (ID: {msg.message_id})")
    print(f"{'='*80}")

    # HDRB Score
    print(f"📊 HDRB Score: {msg.hdrb_score:.1f}/100 (IC: {msg.hdrb_raw:.1f})")
    print(f"   Engagement: {msg.forwards} forwards, {msg.reactions} reactions, {msg.replies} replies")

    # Crypto Detection
    if msg.is_crypto_relevant:
        print(f"💰 Crypto Mentions: {', '.join(msg.crypto_mentions)}")
    else:
        print(f"💰 Crypto Mentions: None")

    # Sentiment
    sentiment_emoji = {'positive': '📈', 'negative': '📉', 'neutral': '➡️'}
    print(f"{sentiment_emoji[msg.sentiment]} Sentiment: {msg.sentiment.capitalize()} ({msg.sentiment_score:+.2f})")

    # Confidence
    conf_indicator = "🟢 HIGH" if msg.is_high_confidence else "🟡 LOW"
    print(f"🎯 Confidence: {conf_indicator} ({msg.confidence:.2f})")

    # Message text
    print(f"\n{msg.message_text}")
    print(f"{'='*80}\n")
```

## Data Models

### Engagement Metrics

```python
@dataclass
class EngagementMetrics:
    forwards: int = 0      # Telegram forwards count
    reactions: int = 0     # Telegram reactions count
    replies: int = 0       # Telegram replies count
    views: int = 0         # Telegram views count
```

### HDRB Score Components

```python
@dataclass
class HDRBScore:
    raw_ic: float          # Raw Importance Coefficient
    normalized: float      # 0-100 normalized score
    forwards: int
    reactions: int
    replies: int
```

### Crypto Detection Result

```python
@dataclass
class CryptoDetectionResult:
    mentions: list[str]           # All detected mentions
    tickers: list[str]            # Ticker symbols (BTC, ETH)
    eth_addresses: list[str]      # Ethereum addresses
    sol_addresses: list[str]      # Solana addresses
    is_relevant: bool             # Has crypto content
```

### Sentiment Result

```python
@dataclass
class SentimentResult:
    label: str                    # 'positive', 'negative', 'neutral'
    score: float                  # -1.0 to 1.0
    positive_indicators: list[str]
    negative_indicators: list[str]
```

## Error Handling

### Processing Errors

**Engagement Metric Extraction Failure**:

- Fallback: Use zeros for all metrics
- Log: Warning with message ID
- Continue: Process with zero engagement

**HDRB Calculation Error**:

- Fallback: Return score of 0
- Log: Error with calculation details
- Continue: Mark as low confidence

**Crypto Detection Error**:

- Fallback: Empty mentions list, not relevant
- Log: Warning with text snippet
- Continue: Process without crypto data

**Sentiment Analysis Error**:

- Fallback: 'neutral' sentiment, score 0.0
- Log: Warning with error details
- Continue: Process with neutral sentiment

**Confidence Calculation Error**:

- Fallback: Confidence 0.0, not high confidence
- Log: Error with component scores
- Continue: Display with low confidence

### Circuit Breaker Scenarios

**When to Open Circuit**:

- 5 consecutive processing failures
- Repeated timeout errors
- Persistent data extraction errors

**Recovery Strategy**:

- Wait 60 seconds
- Attempt single message processing
- If successful: close circuit, resume normal operation
- If failed: remain open, wait another 60 seconds

## Testing Strategy

### Unit Tests

**Error Handler Tests**:

- Retry logic with exponential backoff
- Jitter calculation
- Circuit breaker state transitions
- Error statistics tracking

**HDRB Scorer Tests**:

- IC calculation with known values
- Normalization edge cases (0, max, overflow)
- Missing metric handling

**Crypto Detector Tests**:

- Ticker symbol detection (BTC, ETH, SOL, etc.)
- Ethereum address validation (0x + 40 hex)
- Solana address validation (base58, 32-44 chars)
- False positive prevention

**Sentiment Analyzer Tests**:

- Positive pattern matching
- Negative pattern matching
- Neutral classification
- Mixed sentiment handling

**Confidence Calculator Tests**:

- Weight distribution (40%, 30%, 20%, 10%)
- Threshold comparison
- Edge cases (all zeros, all max)

### Integration Tests

**End-to-End Processing**:

- Mock Telegram message → ProcessedMessage
- Verify all fields populated
- Verify processing time < 100ms

**Error Recovery**:

- Simulate failures → verify retry
- Simulate persistent failures → verify circuit breaker
- Verify graceful degradation

**Pipeline Integration**:

- Telegram event → processed output
- Verify console display format
- Verify logging output

### Manual Verification

**Test Messages**:

1. **High Engagement Crypto Message**:

   - Text: "BTC breaking out! 🚀 Target $100k"
   - Forwards: 50, Reactions: 100, Replies: 25
   - Expected: High HDRB, crypto relevant, positive sentiment, high confidence

2. **Low Engagement Non-Crypto**:

   - Text: "Good morning everyone"
   - Forwards: 0, Reactions: 2, Replies: 0
   - Expected: Low HDRB, not crypto relevant, neutral sentiment, low confidence

3. **Contract Address Message**:

   - Text: "New token: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
   - Forwards: 10, Reactions: 20, Replies: 5
   - Expected: Medium HDRB, crypto relevant (ETH address), neutral, medium confidence

4. **Negative Sentiment**:
   - Text: "SOL dumping hard, exit now!"
   - Forwards: 30, Reactions: 60, Replies: 15
   - Expected: Medium HDRB, crypto relevant, negative sentiment, medium confidence

## Performance Considerations

### Processing Performance

**Target Metrics**:

- Message processing: < 100ms per message
- HDRB calculation: < 10ms
- Crypto detection: < 20ms (regex matching)
- Sentiment analysis: < 20ms (pattern matching)
- Confidence calculation: < 5ms

**Optimization Strategies**:

- Compile regex patterns once at initialization
- Use simple pattern matching (no ML models)
- Avoid external API calls
- Minimize string operations
- Cache compiled patterns

### Memory Management

**Memory Targets**:

- Error handler: < 1MB (error stats)
- Message processor: < 5MB (patterns, state)
- Processed messages: Not retained (immediate display)

**Memory Optimization**:

- No message history storage
- Limited error statistics (last 100 errors)
- Efficient regex pattern compilation

### Concurrency

**Async Processing**:

- Non-blocking message processing
- Concurrent message handling
- Async error handler operations

**Thread Safety**:

- Circuit breaker state protection
- Error statistics thread-safe updates
- Logger thread-safe by design

## Security Considerations

### Input Validation

**Message Text**:

- Length limits (prevent DoS)
- Encoding validation (UTF-8)
- Malicious pattern detection

**Engagement Metrics**:

- Type validation (integers)
- Range validation (non-negative)
- Overflow prevention

### Pattern Matching Safety

**Regex DoS Prevention**:

- Simple, non-backtracking patterns
- Input length limits
- Timeout on pattern matching

**Address Validation**:

- Format validation only (no blockchain queries)
- Length limits
- Character set validation

## Dependencies

### New Python Packages

```
# requirements.txt additions
# (No new dependencies - using built-in libraries)
```

**Built-in Libraries Used**:

- `re`: Regular expressions for pattern matching
- `dataclasses`: Data models
- `asyncio`: Async operations
- `time`: Timing and delays
- `random`: Jitter calculation
- `typing`: Type hints

## Future Extensibility

This design supports future enhancements:

1. **Advanced Sentiment Analysis**: Replace pattern matching with ML models
2. **Historical Tracking**: Add message storage for trend analysis
3. **Real-time Alerts**: Add notification system for high-confidence signals
4. **API Integration**: Add price data enrichment
5. **Channel Reputation**: Add channel scoring based on signal quality

The modular design ensures these additions can be integrated without modifying core processing logic.

## Crypto Detection Patterns

### Ticker Symbols

```python
MAJOR_TICKERS = [
    'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK',
    'UNI', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'APE', 'SAND', 'MANA'
]

# Pattern: Word boundary + ticker + word boundary (case insensitive)
ticker_pattern = r'\b(' + '|'.join(MAJOR_TICKERS) + r')\b'
```

### Ethereum Addresses

```python
# Pattern: 0x followed by 40 hexadecimal characters
eth_pattern = r'0x[a-fA-F0-9]{40}'
```

### Solana Addresses

```python
# Pattern: Base58 encoded, 32-44 characters, no 0OIl characters
sol_pattern = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'
```

### Sentiment Patterns

```python
POSITIVE_PATTERNS = [
    'moon', 'bullish', 'pump', 'breakout', 'rally', 'surge',
    'rocket', '🚀', '📈', 'buy', 'long', 'calls', 'gem'
]

NEGATIVE_PATTERNS = [
    'dump', 'bearish', 'crash', 'rug', 'scam', 'exit', 'sell',
    'short', '📉', 'warning', 'avoid', 'dead', 'rekt'
]
```

## Configuration Defaults

```python
DEFAULT_CONFIG = {
    'confidence_threshold': 0.7,
    'hdrb_max_ic': 1000.0,
    'min_message_length': 10,
    'max_processing_time_ms': 100.0,
    'retry_max_attempts': 3,
    'retry_base_delay': 1.0,
    'retry_exponential_base': 2.0,
    'retry_jitter': True,
    'circuit_breaker_threshold': 5,
    'circuit_breaker_timeout': 60.0
}
```
