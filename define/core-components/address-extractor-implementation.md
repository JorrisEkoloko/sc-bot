# AddressExtractor - Deep Implementation Guide

## Overview

Multi-chain cryptocurrency address extraction with 95% accuracy validation and confidence scoring.

## Architecture Design

### Core Responsibilities

- Ethereum address detection and validation (EIP-55 checksum)
- Solana address detection and Base58 validation
- Context-aware confidence scoring
- Deduplication and quality filtering
- Chain classification and routing

### Component Structure

```
AddressExtractor/
├── ethereum_extractor.py    # Ethereum-specific extraction
├── solana_extractor.py      # Solana-specific extraction
├── address_validator.py     # Multi-chain validation
├── context_analyzer.py      # Context-aware scoring
└── deduplicator.py         # Quality filtering system
```

## Multi-Chain Implementation

### 1. Ethereum Address Extraction

```python
class EthereumExtractor:
    """Ethereum address extraction with EIP-55 validation"""

    def extract_ethereum_addresses(self, text):
        # Regex: 0x[a-fA-F0-9]{40}
        # Context analysis for confidence
        # EIP-55 checksum validation

    def validate_ethereum_checksum(self, address):
        # Keccak256 hash validation
        # Mixed case verification
        # Checksum compliance scoring

    def calculate_ethereum_confidence(self, address, context):
        # Base confidence: 0.7 for valid format
        # Context boost: contract/token mentions
        # Checksum bonus: +0.1 for valid checksum
        # False positive penalty: test/example detection
```

### 2. Solana Address Extraction

```python
class SolanaExtractor:
    """Solana address extraction with Base58 validation"""

    def extract_solana_addresses(self, text):
        # Regex: [1-9A-HJ-NP-Za-km-z]{32,44}
        # Length validation (32-44 characters)
        # Base58 alphabet compliance

    def validate_solana_base58(self, address):
        # Base58 decoding validation
        # 32-byte decoded length check
        # Character distribution analysis

    def calculate_solana_confidence(self, address, context):
        # Base confidence: 0.7 for valid format
        # Context boost: Solana/SPL mentions
        # Quality indicators: character distribution
        # Length optimization: 32-44 range scoring
```

### 3. Universal Address Validator

```python
class AddressValidator:
    """Cross-chain address validation and quality assessment"""

    def validate_address_format(self, address, chain):
        # Chain-specific format validation
        # Checksum verification where applicable
        # Length and character set validation

    def detect_false_positives(self, address, chain):
        # Common false positive patterns
        # Zero addresses and test patterns
        # Repeated character detection

    def assess_address_quality(self, address, context, chain):
        # Format compliance scoring
        # Context relevance analysis
        # False positive probability
        # Overall confidence calculation
```

## Context Analysis System

### Context Scoring Factors

```python
class ContextAnalyzer:
    """Analyzes message context for address confidence scoring"""

    def analyze_address_context(self, address, surrounding_text):
        # High confidence indicators:
        # - "contract address:", "token:", "CA:"
        # - Chart links (dextools, poocoin)
        # - Trading instructions

        # Medium confidence indicators:
        # - "buy", "trade", "swap" mentions
        # - Price discussions
        # - Technical analysis

        # Low confidence indicators:
        # - "example", "test", "demo"
        # - Educational content
        # - Code snippets
```

### Confidence Calculation Algorithm

```python
def calculate_integrated_confidence(self, address_info, context_data):
    """
    Confidence Scoring Formula:
    Base Score (0.7) + Context Boost (±0.3) + Quality Factors (±0.2)

    Factors:
    - Format validity: Required baseline
    - Context relevance: High impact (±0.2)
    - Checksum validation: Moderate impact (+0.1)
    - False positive indicators: High penalty (-0.3)
    - Chain-specific quality: Moderate impact (±0.1)
    """
```

## Deduplication & Quality Control

### 1. Deduplication Strategy

```python
class Deduplicator:
    """Advanced deduplication with quality preservation"""

    def deduplicate_addresses(self, address_list):
        # Case-insensitive deduplication
        # Confidence-based selection (keep highest)
        # Position-based tiebreaking
        # Cross-chain duplicate detection

    def merge_duplicate_contexts(self, duplicates):
        # Combine context information
        # Aggregate confidence scores
        # Preserve best validation results
```

### 2. Quality Filtering

```python
def apply_quality_filters(self, addresses):
    """
    Quality Gates:
    1. Minimum confidence threshold (0.3)
    2. Maximum addresses per message (5)
    3. False positive elimination
    4. Chain-specific validation
    5. Context relevance scoring
    """
```

## Chain Classification System

### Automatic Chain Detection

```python
class ChainClassifier:
    """Determines blockchain for extracted addresses"""

    def classify_address_chain(self, address):
        # Ethereum: 0x prefix + 40 hex characters
        # Solana: Base58, 32-44 characters, no 0x
        # Bitcoin: Base58, starts with 1/3, 25-34 characters
        # BSC: Same as Ethereum (context-dependent)

    def resolve_ambiguous_chains(self, address, context):
        # BSC vs Ethereum disambiguation
        # Context clues: "BSC", "Binance", "PancakeSwap"
        # Default to Ethereum for 0x addresses
```

## Performance Optimization

### Regex Compilation Strategy

```python
class PatternManager:
    """Optimized regex pattern management"""

    def __init__(self):
        # Pre-compile all regex patterns
        self.ethereum_pattern = re.compile(r'0x[a-fA-F0-9]{40}')
        self.solana_pattern = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')

        # Context patterns for confidence scoring
        self.context_patterns = {
            'contract': re.compile(r'(contract|token|address|ca)\s*:?\s*', re.IGNORECASE),
            'chart': re.compile(r'(chart|dextools|poocoin)', re.IGNORECASE)
        }
```

### Extraction Efficiency

- Single-pass text scanning
- Parallel validation for multiple addresses
- Cached context analysis results
- Early termination for low-quality addresses

## Validation Accuracy Targets

### Performance Metrics

- **95% Accuracy**: For both Ethereum and Solana
- **< 5% False Positives**: Strict quality filtering
- **> 90% True Positives**: High sensitivity for valid addresses
- **Context Confidence**: 80%+ correlation with manual validation

### Quality Assurance

```python
class QualityAssurance:
    """Continuous quality monitoring and improvement"""

    def track_extraction_accuracy(self):
        # Monitor false positive rates
        # Track confidence score correlation
        # Measure context analysis effectiveness

    def update_validation_rules(self, feedback_data):
        # Improve false positive detection
        # Refine confidence scoring
        # Update context analysis patterns
```

## Error Handling & Edge Cases

### Common Edge Cases

1. **Mixed Case Addresses**: EIP-55 checksum handling
2. **Partial Addresses**: Incomplete or truncated addresses
3. **Embedded Addresses**: Addresses within URLs or code
4. **Multiple Formats**: Same address in different formats
5. **Non-Standard Formats**: Custom or modified address formats

### Error Recovery Strategies

```python
def handle_extraction_errors(self, text, error):
    """
    Error Recovery:
    1. Malformed regex patterns → Fallback to basic patterns
    2. Encoding issues → UTF-8 normalization
    3. Memory limits → Chunked processing
    4. Timeout issues → Simplified validation
    """
```

## Integration Interfaces

### Input Interface

```python
def extract_addresses(self, message_text: str) -> List[ExtractedAddress]:
    """
    Input: Raw message text
    Output: List of validated addresses with confidence scores
    """
```

### Output Format

```python
@dataclass
class ExtractedAddress:
    address: str              # The extracted address
    chain: str               # Blockchain (ethereum/solana/bitcoin)
    confidence: float        # Confidence score (0.0-1.0)
    position: int           # Position in original text
    context: str            # Surrounding context
    validation_status: str  # valid/invalid/uncertain
```

### Integration Points

- **MessageProcessor**: Receives addresses for price fetching
- **PriceEngine**: Uses chain classification for API routing
- **PerformanceTracker**: Stores addresses for tracking
- **DataOutput**: Includes addresses in output records
