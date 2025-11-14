# Requirements Document - Part 2: Message Processing + HDRB Scoring

## Introduction

Part 2 adds intelligence to the crypto monitoring system by implementing message processing with research-based HDRB scoring and crypto relevance detection. The goal is to analyze incoming Telegram messages, calculate engagement scores using the IEEE research-compliant formula, detect cryptocurrency mentions, and display enriched message data with scores in the console. This transforms raw messages into actionable intelligence.

## Glossary

- **Message Processor**: Component that analyzes message content and calculates scores
- **HDRB Score**: Research-based engagement score calculated from message metrics using IEEE-compliant formula
- **Engagement Metrics**: Message statistics including forwards, likes/reactions, and replies
- **Crypto Detection**: Pattern matching to identify cryptocurrency mentions and contract addresses
- **Sentiment Analysis**: Classification of message tone as positive, negative, or neutral
- **Confidence Score**: Calculated value (0.0-1.0) indicating message relevance and quality
- **Error Handler**: Component that manages retry logic and error recovery
- **Circuit Breaker**: Pattern that prevents repeated failures by temporarily disabling operations
- **Processed Message**: Message object enriched with HDRB score, crypto detection, and sentiment

## Requirements

### Requirement 1: Error Handler with Retry Logic

**User Story:** As a system operator, I want robust error handling with automatic retries, so that transient failures don't disrupt message processing.

#### Acceptance Criteria

1. WHEN an operation fails, THE Error Handler SHALL retry the operation with exponential backoff
2. WHEN retry attempts are exhausted, THE Error Handler SHALL log the failure and return error status
3. WHERE retry delay is calculated, THE Error Handler SHALL use exponential backoff with jitter (1s, 2s, 4s, 8s)
4. WHEN multiple failures occur for the same operation type, THE Error Handler SHALL implement circuit breaker pattern
5. WHILE circuit is open, THE Error Handler SHALL reject operations immediately without attempting execution

### Requirement 2: HDRB Score Calculation

**User Story:** As a system operator, I want messages scored using the HDRB model, so that I can identify high-engagement signals.

#### Acceptance Criteria

1. WHEN a message is received, THE Message Processor SHALL extract engagement metrics (forwards, reactions, replies)
2. WHEN engagement metrics are extracted, THE Message Processor SHALL calculate HDRB score using formula: IC = forwards + (2 × reactions) + (0.5 × replies)
3. WHERE engagement metrics are missing, THE Message Processor SHALL use zero as default value
4. WHEN HDRB score is calculated, THE Message Processor SHALL normalize score to 0-100 range
5. WHEN score calculation fails, THE Message Processor SHALL log error and return score of 0

### Requirement 3: Crypto Relevance Detection

**User Story:** As a system operator, I want automatic detection of cryptocurrency mentions, so that I can filter relevant signals from noise.

#### Acceptance Criteria

1. WHEN a message is processed, THE Message Processor SHALL scan text for cryptocurrency ticker symbols (BTC, ETH, SOL, etc.)
2. WHEN scanning message text, THE Message Processor SHALL detect Ethereum contract addresses (0x followed by 40 hex characters)
3. WHEN scanning message text, THE Message Processor SHALL detect Solana contract addresses (base58 encoded, 32-44 characters)
4. WHEN crypto patterns are found, THE Message Processor SHALL extract all unique mentions into a list
5. WHEN no crypto patterns are found, THE Message Processor SHALL mark message as non-crypto-relevant

### Requirement 4: Sentiment Analysis

**User Story:** As a system operator, I want sentiment analysis on messages, so that I can understand the tone of crypto signals.

#### Acceptance Criteria

1. WHEN a message is processed, THE Message Processor SHALL analyze text sentiment using pattern matching
2. WHEN sentiment is analyzed, THE Message Processor SHALL classify as positive, negative, or neutral
3. WHERE positive indicators are detected (moon, bullish, pump, breakout), THE Message Processor SHALL classify as positive
4. WHERE negative indicators are detected (dump, bearish, crash, rug), THE Message Processor SHALL classify as negative
5. WHEN sentiment is ambiguous or no indicators found, THE Message Processor SHALL classify as neutral

### Requirement 5: Confidence Score Calculation

**User Story:** As a system operator, I want confidence scores for messages, so that I can prioritize high-quality signals.

#### Acceptance Criteria

1. WHEN a message is processed, THE Message Processor SHALL calculate confidence score from multiple factors
2. WHEN calculating confidence, THE Message Processor SHALL weight HDRB score (40%), crypto relevance (30%), sentiment clarity (20%), and message length (10%)
3. WHERE confidence score exceeds threshold (0.7), THE Message Processor SHALL mark message as high-confidence
4. WHEN confidence score is below threshold, THE Message Processor SHALL mark message as low-confidence
5. WHEN confidence calculation completes, THE Message Processor SHALL return normalized score (0.0-1.0)

### Requirement 6: Message Processing Pipeline Integration

**User Story:** As a system operator, I want message processing integrated into the main pipeline, so that all messages are automatically analyzed.

#### Acceptance Criteria

1. WHEN a message event is received from Telegram Monitor, THE System SHALL pass message to Message Processor
2. WHEN Message Processor completes analysis, THE System SHALL receive processed message with all scores
3. IF processing fails, THEN THE System SHALL log error and display original message without scores
4. WHEN processed message is received, THE System SHALL format output with HDRB score, crypto mentions, sentiment, and confidence
5. WHILE system is running, THE System SHALL process all messages through the pipeline without blocking

### Requirement 7: Enhanced Console Output

**User Story:** As a system operator, I want to see enriched message data in console, so that I can quickly assess signal quality.

#### Acceptance Criteria

1. WHEN displaying a processed message, THE System SHALL show HDRB score prominently
2. WHEN displaying a processed message, THE System SHALL list detected crypto mentions
3. WHEN displaying a processed message, THE System SHALL show sentiment classification
4. WHEN displaying a processed message, THE System SHALL show confidence score with visual indicator
5. WHERE message is high-confidence, THE System SHALL highlight output with visual marker

### Requirement 8: Configuration for Processing Parameters

**User Story:** As a system operator, I want configurable processing parameters, so that I can tune the system without code changes.

#### Acceptance Criteria

1. WHEN System starts, THE Configuration Manager SHALL load confidence threshold from environment (default: 0.7)
2. WHEN System starts, THE Configuration Manager SHALL load retry configuration (max attempts, backoff multiplier)
3. WHERE configuration values are invalid, THE Configuration Manager SHALL use safe defaults and log warning
4. WHEN processing messages, THE Message Processor SHALL use configured thresholds for all calculations
5. WHEN configuration changes, THE System SHALL apply new values without restart (future enhancement marker)

### Requirement 9: Processing Performance

**User Story:** As a system operator, I want fast message processing, so that the system can handle high-volume channels.

#### Acceptance Criteria

1. WHEN a message is received, THE Message Processor SHALL complete analysis within 100ms
2. WHEN processing multiple messages concurrently, THE System SHALL maintain throughput of 10+ messages per second
3. WHERE processing exceeds time limit, THE Message Processor SHALL log performance warning
4. WHEN system is idle, THE Message Processor SHALL consume minimal CPU resources
5. WHILE processing messages, THE System SHALL not accumulate memory leaks over extended operation

### Requirement 10: Error Tracking and Reporting

**User Story:** As a system operator, I want visibility into processing errors, so that I can identify and fix issues.

#### Acceptance Criteria

1. WHEN an error occurs during processing, THE Error Handler SHALL log error with full context (message ID, channel, error type)
2. WHEN errors are logged, THE Error Handler SHALL include stack trace for debugging
3. WHERE errors are recoverable, THE Error Handler SHALL indicate retry status in logs
4. WHEN circuit breaker opens, THE Error Handler SHALL log circuit state change with reason
5. WHEN system runs for extended period, THE Error Handler SHALL provide error summary statistics in logs
