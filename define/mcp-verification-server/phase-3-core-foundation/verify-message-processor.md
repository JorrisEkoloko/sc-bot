# Verify MessageProcessor - Phase 3.2

## Component Focus

**MessageProcessor** - HDRB-compliant message processing with intelligence integration

## Endpoints to Verify

### 1. HDRB Scoring

```python
def calculate_importance_coefficient(message_data: Dict) -> float
```

**Verify**:

- ✓ Uses exact formula: IC = retweet + (2 × favorite) + (0.5 × reply)
- ✓ Handles fallback mapping: retweets→forwards, favorites→likes/reactions, replies→comments
- ✓ Returns 0 for missing metrics (Telegram reality)
- ✓ Logs calculation details

**Check Against Current**:

- Compare with `src/scoring/research_based_scorer.py` line 593-620
- Verify exact weights: 1.0, 2.0, 0.5
- Confirm fallback logic preserved

**Critical**:

```python
retweets = message_data.get('retweets', message_data.get('forwards', 0))
favorites = message_data.get('favorites', message_data.get('likes', message_data.get('reactions', 0)))
replies = message_data.get('replies', message_data.get('comments', 0))
ic = (retweets * 1.0) + (favorites * 2.0) + (replies * 0.5)
```

### 2. Crypto Detection

```python
async def is_crypto_relevant(text: str) -> bool
```

**Verify**:

- ✓ Detects major cryptocurrencies (Bitcoin, Ethereum, etc.)
- ✓ Identifies contract addresses (0x... for Ethereum)
- ✓ Recognizes trading signals (buy, sell, long, short)
- ✓ Returns True if crypto-related

**Check Against Current**:

- Compare with `src/filtering/message_filter.py` line 88-140
- Verify same crypto patterns preserved

### 3. Sentiment Analysis

```python
def calculate_compound_sentiment(text: str) -> float
```

**Verify**:

- ✓ Returns sentiment score -1 to +1
- ✓ Handles aspect-based analysis
- ✓ Identifies bullish/bearish signals
- ✓ Normalizes to research range

**Check Against Current**:

- Compare with `src/scoring/research_based_scorer.py` line 400-450
- Verify sentiment methodology preserved

### 4. Integrated Confidence

```python
async def process_message(message_data: Dict) -> Dict
```

**Verify**:

- ✓ Combines HDRB score + intelligence
- ✓ Calculates holistic confidence (0-1)
- ✓ Returns processing decision (should_process: bool)
- ✓ Includes all scoring components

**Check Against Current**:

- Compare with `src/main.py` line 792-850
- Verify same processing pipeline

## Logic to Validate

### HDRB Formula Compliance

```
Research Formula (IEEE Paper):
IC = retweet + (2 × favorite) + (0.5 × reply)

Weights:
- Engagement: 40%
- Crypto Relevance: 25%
- Signal Strength: 20%
- Timing Factor: 15%

Total Score = (0.40 × engagement) + (0.25 × relevance) +
              (0.20 × signal) + (0.15 × timing)
```

**Verify**: Exact match with `src/scoring/research_compliant_scorer.py`

### Telegram Message Handling

```
Telegram Reality:
- Only provides: id, text, date, views, sender_id
- Missing: forwards, favorites, replies

Fallback Behavior:
- retweets = forwards (defaults to 0)
- favorites = likes/reactions (defaults to 0)
- replies = comments (defaults to 0)

Result: IC = 0 for most Telegram messages
```

**Verify**: Matches actual behavior in `src/scoring/research_based_scorer.py` line 593-620

### Processing Pipeline

```
1. Check crypto relevance
2. If not relevant → return None
3. Calculate HDRB score
4. Get intelligence context
5. Calculate integrated confidence
6. If confidence > threshold → process
7. Return result with all scores
```

**Verify**: Matches `src/main.py` line 792-850

## Integration Points

### With TelegramMonitor

- ✓ Receives message_data from queue
- ✓ Expects format: {id, text, date, views, sender_id}
- ✓ No direct coupling (data-driven)

### With Intelligence Layer

- ✓ Integrates market cap intelligence
- ✓ Integrates channel reputation
- ✓ Calculates holistic confidence
- ✓ Provides intelligence context

### With AddressExtractor

- ✓ Passes processed messages
- ✓ Provides confidence scores
- ✓ Includes intelligence context

## Success Criteria

### Functional Requirements

- [ ] HDRB formula exactly matches research
- [ ] Crypto detection works accurately
- [ ] Sentiment analysis functional
- [ ] Integrated confidence calculated
- [ ] Processing decision correct

### Preservation Requirements

- [ ] Exact IC formula: retweet + (2 × favorite) + (0.5 × reply)
- [ ] Same fallback mapping logic
- [ ] Same crypto detection patterns
- [ ] Same sentiment methodology
- [ ] Same weight distribution (40/25/20/15)

### Performance Requirements

- [ ] Processing time < 100ms per message
- [ ] Crypto detection accuracy > 90%
- [ ] Sentiment correlation > 70%
- [ ] Memory usage < 50MB

## Verification Commands

### Test HDRB Formula

```python
from core.message_processor import MessageProcessor

processor = MessageProcessor(config.processing)

# Test with known values
message_data = {
    'retweets': 100,
    'favorites': 500,
    'replies': 50
}

ic = processor.calculate_importance_coefficient(message_data)
expected = 100 + (2 * 500) + (0.5 * 50)  # = 1125
assert ic == expected, f"IC mismatch: {ic} != {expected}"
```

### Test Telegram Fallback

```python
# Telegram message (only views)
telegram_message = {
    'id': 123,
    'text': 'Bitcoin to the moon!',
    'date': datetime.now(),
    'views': 1000,
    'sender_id': 456
}

ic = processor.calculate_importance_coefficient(telegram_message)
# Should be 0 (no forwards/favorites/replies)
assert ic == 0, f"Telegram IC should be 0, got {ic}"
```

### Test Crypto Detection

```python
crypto_text = "Bitcoin just broke $50k! Ethereum following. Buy signal confirmed."
is_crypto = await processor.is_crypto_relevant(crypto_text)
assert is_crypto == True, "Failed to detect crypto content"

non_crypto_text = "Good morning everyone! Have a great day!"
is_crypto = await processor.is_crypto_relevant(non_crypto_text)
assert is_crypto == False, "False positive on non-crypto content"
```

### Test Complete Processing

```python
result = await processor.process_message(telegram_message)
assert 'hdrb_score' in result, "Missing HDRB score"
assert 'confidence' in result, "Missing confidence"
assert 'should_process' in result, "Missing processing decision"
assert 0 <= result['confidence'] <= 1, "Confidence out of range"
```

## Common Issues

### Issue 1: IC Always Zero

**Symptom**: All messages have IC = 0
**Check**: Telegram messages don't have forwards/favorites/replies
**Expected**: This is correct behavior for Telegram
**Note**: Document this reality vs documentation claim

### Issue 2: Crypto Detection Fails

**Symptom**: Missing obvious crypto content
**Check**:

- Crypto patterns loaded correctly
- Text preprocessing working
- Case-insensitive matching
  **Fix**: Verify pattern list matches current implementation

### Issue 3: Confidence Always Low

**Symptom**: No messages pass threshold
**Check**:

- Intelligence integration working
- Weights configured correctly
- Threshold not too high (default 0.6)
  **Fix**: Verify intelligence components initialized

## Phase Completion

✅ **Ready for Phase 3.3** when:

- HDRB formula verified exact
- Telegram fallback behavior confirmed
- Crypto detection tested
- Sentiment analysis working
- Integration with intelligence validated
- All tests passing
