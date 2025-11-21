# Design Document: NLP-Enhanced Sentiment Analysis

## Overview

This design implements a hybrid sentiment analysis system that combines fast pattern matching with transformer-based NLP models. The architecture is based on research from Google's BERT paper (Devlin et al., 2018) and Cardiff NLP's Twitter-RoBERTa model (Camacho-Collados et al., 2022), which demonstrates state-of-the-art performance on social media sentiment analysis.

### Key Design Principles

1. **Hybrid Approach**: Use fast pattern matching for 80% of clear cases, NLP for 20% ambiguous cases
2. **Graceful Degradation**: System continues operating if NLP components fail
3. **Minimal Code Changes**: ~200 lines of new code, existing interface unchanged
4. **Research-Backed**: Based on proven transformer architectures (RoBERTa trained on 124M tweets)
5. **Crypto-Optimized**: Fine-tuned vocabulary and patterns for cryptocurrency domain

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Message Processor                         │
│                  (existing, unchanged)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Enhanced Sentiment Analyzer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Pattern Matcher (existing)                       │  │
│  │     - Regex-based keyword matching                   │  │
│  │     - Fast: ~1-5ms per message                       │  │
│  │     - Returns: (label, score, confidence)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. Confidence Evaluator (new)                       │  │
│  │     - Checks if confidence > threshold (0.7)         │  │
│  │     - Detects conflicting signals                    │  │
│  │     - Routes to NLP if needed                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│                    ┌────┴────┐                              │
│                    │         │                              │
│         High Conf  │         │  Low Conf                    │
│                    ▼         ▼                              │
│         ┌──────────┐    ┌──────────────────────┐           │
│         │  Return  │    │  3. NLP Analyzer     │           │
│         │  Result  │    │     (new)            │           │
│         └──────────┘    │  - RoBERTa model     │           │
│                         │  - Context-aware     │           │
│                         │  - 50-200ms          │           │
│                         └──────────────────────┘           │
│                                  │                          │
│                                  ▼                          │
│                         ┌──────────────────┐               │
│                         │  4. Result       │               │
│                         │     Merger       │               │
│                         │     (new)        │               │
│                         └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Pattern Matcher (Existing - Enhanced)

**Purpose**: Fast keyword-based sentiment classification

**Enhancements**:

- Add crypto-specific vocabulary (50+ terms)
- Return confidence score based on match strength
- Detect conflicting signals (positive + negative keywords)

**Algorithm**:

```
1. Scan text for positive patterns (25 existing + 15 new crypto terms)
2. Scan text for negative patterns (24 existing + 15 new crypto terms)
3. Calculate raw score based on match counts
4. Calculate confidence based on:
   - Match strength (number of matches)
   - Signal clarity (ratio of positive to negative)
   - Text length (longer text = more context)
5. Return (label, score, confidence)
```

**Confidence Calculation**:

```
confidence = min(1.0, (dominant_count / total_count) * (1 + log(match_count)))
```

#### 2. Confidence Evaluator (New)

**Purpose**: Decide whether to use pattern result or invoke NLP

**Decision Logic**:

```python
def should_use_nlp(pattern_result, text):
    label, score, confidence = pattern_result

    # High confidence pattern match - use it
    if confidence > 0.7 and abs(score) > 0.5:
        return False

    # Conflicting signals - use NLP
    if has_conflicting_signals(text):
        return True

    # Contains negation - use NLP
    if contains_negation(text):
        return True

    # Contains sarcasm indicators - use NLP
    if contains_sarcasm_indicators(text):
        return True

    # Low confidence - use NLP
    if confidence <= 0.7:
        return True

    return False
```

**Negation Detection**:

- Keywords: not, don't, doesn't, didn't, never, no, neither, nor
- Context window: 3 words after negation

**Sarcasm Indicators**:

- Quotes around positive words: "guaranteed", "definitely"
- Eye-roll emoji: 🙄
- Excessive punctuation: !!!, ???
- Contradictory emoji: positive words + 🤡

#### 3. NLP Analyzer (New)

**Purpose**: Context-aware sentiment analysis using transformer model

**Model Selection** (Research-Backed):

**Primary Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest`

- **Training Data**: 124M tweets (Jan 2018 - Dec 2021)
- **Architecture**: RoBERTa-base (125M parameters)
- **Performance**: State-of-the-art on TweetEval benchmark
- **Inference Speed**: ~50-200ms per message
- **Labels**: 0=Negative, 1=Neutral, 2=Positive
- **Research**: Camacho-Collados et al., 2022 (TimeLMs paper)

**Why RoBERTa over BERT**:

1. Trained on social media text (similar to Telegram)
2. Better handling of informal language
3. Robust to typos and slang
4. Pre-trained on massive tweet corpus

**Alternative Models** (Configurable):

- `finiteautomata/bertweet-base-sentiment-analysis` (58M tweets)
- `distilbert-base-uncased-finetuned-sst-2-english` (faster, less accurate)

**Implementation**:

```python
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

class NLPSentimentAnalyzer:
    def __init__(self, model_name, device='cpu'):
        self.model_name = model_name
        self.device = device
        self.pipeline = None
        self.tokenizer = None
        self.model = None

    def load_model(self):
        """Lazy load model on first use"""
        if self.pipeline is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == 'gpu' else -1
            )

    def analyze(self, text):
        """Run NLP inference"""
        self.load_model()

        # Preprocess (handle @mentions, links)
        text = self.preprocess(text)

        # Run inference
        result = self.pipeline(text)[0]

        # Convert to our format
        label = result['label'].lower()
        confidence = result['score']

        # Map to score (-1 to +1)
        score_map = {'negative': -0.8, 'neutral': 0.0, 'positive': 0.8}
        score = score_map[label] * confidence

        return (label, score, confidence)
```

**Preprocessing**:

```python
def preprocess(self, text):
    """Preprocess text for NLP model"""
    # Replace @mentions with @user token
    text = re.sub(r'@\w+', '@user', text)

    # Replace URLs with http token
    text = re.sub(r'http\S+', 'http', text)

    # Normalize whitespace
    text = ' '.join(text.split())

    # Truncate to model max length (512 tokens)
    tokens = self.tokenizer.encode(text, truncation=True, max_length=512)
    text = self.tokenizer.decode(tokens, skip_special_tokens=True)

    return text
```

#### 4. Result Merger (New)

**Purpose**: Combine pattern and NLP results with metadata

**Output Format**:

```python
{
    'label': str,              # 'positive', 'negative', 'neutral'
    'score': float,            # -1.0 to +1.0
    'confidence': float,       # 0.0 to 1.0
    'method': str,             # 'pattern' or 'nlp'
    'pattern_result': dict,    # Original pattern result
    'nlp_result': dict,        # NLP result if used
    'processing_time_ms': float
}
```

**Backward Compatibility**:

```python
def analyze(self, text):
    """Main entry point - maintains existing interface"""
    result = self._analyze_enhanced(text)

    # Return simple tuple for backward compatibility
    return (result['label'], result['score'])

def analyze_detailed(self, text):
    """New method for detailed results"""
    return self._analyze_enhanced(text)
```

## Data Models

### SentimentResult

```python
@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    label: str                    # 'positive', 'negative', 'neutral'
    score: float                  # -1.0 to +1.0
    confidence: float             # 0.0 to 1.0
    method: str                   # 'pattern', 'nlp', 'fallback'
    processing_time_ms: float
    pattern_confidence: float     # Pattern matcher confidence
    nlp_confidence: Optional[float] = None
    has_negation: bool = False
    has_sarcasm: bool = False
    crypto_terms: List[str] = field(default_factory=list)
```

### Configuration

```python
@dataclass
class SentimentConfig:
    """Sentiment analyzer configuration"""
    # NLP settings
    nlp_enabled: bool = True
    nlp_model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    nlp_device: str = "cpu"  # 'cpu' or 'gpu'
    nlp_confidence_threshold: float = 0.7

    # Pattern settings
    pattern_confidence_threshold: float = 0.7
    use_crypto_vocabulary: bool = True

    # Performance settings
    nlp_batch_size: int = 8
    model_cache_dir: str = "models/sentiment"
    max_text_length: int = 512

    # Fallback settings
    fallback_to_pattern: bool = True
    retry_on_error: bool = False
```

## Crypto-Specific Vocabulary

### Additional Positive Terms (15 new)

```python
CRYPTO_POSITIVE = [
    'wagmi',        # We're All Gonna Make It
    'gm',           # Good Morning (community greeting)
    'lfg',          # Let's F***ing Go
    'degen',        # Degenerate (positive in crypto)
    'ape',          # Aping in (buying aggressively)
    'diamond hands', # Strong holders
    'hodl',         # Hold On for Dear Life
    'alpha',        # Exclusive information
    'based',        # Authentic, good
    'ser',          # Sir (respectful)
    'fren',         # Friend
    'ngmi',         # Not Gonna Make It (ironic positive)
    'chad',         # Successful trader
    'whale',        # Large holder (neutral/positive)
    'moonshot'      # High potential
]
```

### Additional Negative Terms (15 new)

```python
CRYPTO_NEGATIVE = [
    'ngmi',         # Not Gonna Make It (negative context)
    'paper hands',  # Weak holders
    'rekt',         # Wrecked/destroyed
    'fud',          # Fear, Uncertainty, Doubt
    'jeet',         # Weak seller
    'rugged',       # Rug pulled
    'honeypot',     # Scam contract
    'bagholder',    # Stuck with losses
    'cope',         # Coping with losses
    'salty',        # Bitter about losses
    'exit liquidity', # Being used by whales
    'vaporware',    # Non-existent product
    'shitcoin',     # Low quality token
    'pump and dump',
    'wash trading'
]
```

### Context-Dependent Terms

```python
CONTEXT_DEPENDENT = {
    'degen': {
        'positive_context': ['play', 'move', 'opportunity'],
        'negative_context': ['trap', 'mistake', 'loss']
    },
    'ape': {
        'positive_context': ['in', 'into', 'early'],
        'negative_context': ['trap', 'top', 'late']
    },
    'moon': {
        'positive_context': ['to', 'going', 'will'],
        'negative_context': ['not', 'never', 'won\'t']
    }
}
```

## Error Handling

### Error Scenarios

1. **Model Download Failure**

   - Retry once with exponential backoff
   - Fall back to pattern-only mode
   - Log error with model name and URL

2. **Model Loading Failure**

   - Check disk space and permissions
   - Attempt to re-download if corrupted
   - Fall back to pattern-only mode

3. **Inference Failure**

   - Log error with input text (truncated)
   - Return pattern-based result
   - Increment error counter

4. **Out of Memory**

   - Reduce batch size
   - Clear model cache
   - Fall back to CPU if on GPU

5. **Timeout**
   - Set 5-second timeout for NLP inference
   - Return pattern result if timeout
   - Log slow inference warning

### Fallback Strategy

```python
def analyze_with_fallback(self, text):
    """Analyze with automatic fallback"""
    try:
        # Try pattern matching first
        pattern_result = self.pattern_analyzer.analyze(text)

        # Check if NLP needed
        if not self.should_use_nlp(pattern_result, text):
            return self._format_result(pattern_result, method='pattern')

        # Try NLP
        try:
            nlp_result = self.nlp_analyzer.analyze(text)
            return self._format_result(nlp_result, method='nlp')
        except Exception as e:
            self.logger.warning(f"NLP inference failed: {e}, using pattern result")
            return self._format_result(pattern_result, method='fallback')

    except Exception as e:
        self.logger.error(f"Sentiment analysis failed: {e}")
        return self._format_result(('neutral', 0.0, 0.0), method='error')
```

## Testing Strategy

### Unit Tests

1. **Pattern Matcher Tests** (30 tests)

   - Existing positive/negative/neutral cases
   - New crypto vocabulary tests
   - Confidence calculation tests
   - Conflicting signal detection

2. **NLP Analyzer Tests** (25 tests)

   - Model loading and caching
   - Preprocessing correctness
   - Inference accuracy on known cases
   - Error handling and fallback

3. **Confidence Evaluator Tests** (15 tests)

   - Threshold logic
   - Negation detection
   - Sarcasm detection
   - Routing decisions

4. **Integration Tests** (20 tests)
   - End-to-end sentiment analysis
   - Hybrid system behavior
   - Performance benchmarks
   - Backward compatibility

### Test Cases for Context Understanding

```python
CONTEXT_TEST_CASES = [
    # Negation
    ("Don't buy this pump", "negative", "pattern says positive, NLP corrects"),
    ("Not a scam, legit project", "positive", "negation reverses sentiment"),
    ("Never selling, diamond hands", "positive", "negation + positive = positive"),

    # Sarcasm
    ("Yeah sure, this will 'definitely' moon 🙄", "negative", "sarcasm detection"),
    ("Great, another rug pull 🤡", "negative", "ironic positive word"),

    # Conditional
    ("Bullish IF it breaks $1", "neutral", "conditional sentiment"),
    ("Will moon when BTC recovers", "neutral", "future conditional"),

    # Crypto slang
    ("WAGMI frens, apes together strong", "positive", "crypto community language"),
    ("Paper hands getting rekt", "negative", "crypto negative slang"),
    ("Degen play but could 100x", "positive", "context-dependent term"),

    # Mixed entity
    ("BTC pumping but alts dumping", "neutral", "mixed sentiment"),
    ("Love the project, hate the tokenomics", "neutral", "conflicting aspects")
]
```

### Performance Benchmarks

**Target Metrics**:

- Pattern-only: < 5ms per message
- NLP inference: < 200ms per message (CPU), < 50ms (GPU)
- Hybrid average: < 50ms per message (80% pattern, 20% NLP)
- Accuracy improvement: +15% on ambiguous cases
- Pattern match rate: > 80%

### Accuracy Validation

**Test Dataset**:

- 500 manually labeled crypto messages
- 200 clear positive (pattern should handle)
- 200 clear negative (pattern should handle)
- 100 ambiguous (NLP should improve)

**Success Criteria**:

- Pattern-only accuracy: 70% overall, 85% on clear cases
- Hybrid accuracy: 85% overall, 95% on clear cases, 70% on ambiguous
- No regression on clear cases

## Deployment Strategy

### Phase 1: Development (Week 1)

- Implement confidence evaluator
- Integrate NLP model
- Add crypto vocabulary
- Unit tests

### Phase 2: Testing (Week 2)

- Integration testing
- Performance benchmarking
- Accuracy validation
- Error handling verification

### Phase 3: Staging (Week 3)

- Deploy to staging environment
- Monitor performance metrics
- A/B test against pattern-only
- Collect accuracy feedback

### Phase 4: Production (Week 4)

- Gradual rollout (10% → 50% → 100%)
- Monitor error rates and performance
- Collect user feedback
- Optimize based on real-world data

## Monitoring and Metrics

### Key Metrics

1. **Performance Metrics**

   - Average inference time (pattern vs NLP)
   - 95th percentile latency
   - NLP invocation rate
   - Model loading time

2. **Accuracy Metrics**

   - Sentiment distribution (positive/negative/neutral)
   - Confidence score distribution
   - Fallback rate
   - Error rate

3. **Resource Metrics**
   - Memory usage (with/without model loaded)
   - CPU/GPU utilization
   - Model cache size
   - Disk I/O for model loading

### Logging

```python
# INFO level
logger.info(f"Sentiment: {label} (score: {score:.2f}, confidence: {confidence:.2f}, method: {method})")

# DEBUG level
logger.debug(f"Pattern result: {pattern_result}, NLP needed: {use_nlp}")
logger.debug(f"NLP inference time: {inference_time_ms:.1f}ms")

# WARNING level
logger.warning(f"NLP inference failed, falling back to pattern: {error}")
logger.warning(f"Slow NLP inference: {inference_time_ms:.1f}ms > 200ms")

# Periodic stats (every 100 messages)
logger.info(f"Stats: pattern={pattern_count}, nlp={nlp_count}, fallback={fallback_count}")
```

## Research References

1. **BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding**

   - Devlin et al., 2018
   - arXiv:1810.04805
   - Foundation for transformer-based NLP

2. **TweetNLP: Cutting-Edge Natural Language Processing for Social Media**

   - Camacho-Collados et al., 2022
   - Twitter-RoBERTa model trained on 124M tweets
   - State-of-the-art social media sentiment analysis

3. **RoBERTa: A Robustly Optimized BERT Pretraining Approach**

   - Liu et al., 2019
   - Improvements over BERT for social media text

4. **Hugging Face Transformers Library**
   - Wolf et al., 2020
   - Industry-standard implementation
   - 27,000+ pre-trained models

## Configuration Example

```env
# Sentiment Analysis Configuration
SENTIMENT_NLP_ENABLED=true
SENTIMENT_NLP_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest
SENTIMENT_NLP_DEVICE=cpu
SENTIMENT_NLP_CONFIDENCE_THRESHOLD=0.7
SENTIMENT_PATTERN_CONFIDENCE_THRESHOLD=0.7
SENTIMENT_USE_CRYPTO_VOCABULARY=true
SENTIMENT_MODEL_CACHE_DIR=models/sentiment
SENTIMENT_FALLBACK_TO_PATTERN=true
```
