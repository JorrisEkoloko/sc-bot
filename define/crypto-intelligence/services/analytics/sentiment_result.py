"""Sentiment analysis result dataclass."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SentimentResult:
    """
    Comprehensive sentiment analysis result.
    
    Contains all information about sentiment classification including
    pattern and NLP results, confidence scores, and metadata.
    """
    # Core results
    label: str                          # 'positive', 'negative', or 'neutral'
    score: float                        # -1.0 to +1.0
    confidence: float                   # 0.0 to 1.0
    method: str                         # 'pattern', 'nlp', or 'fallback'
    
    # Performance metadata
    processing_time_ms: float           # Time taken for analysis
    
    # Pattern matching details
    pattern_confidence: float           # Pattern matcher confidence
    pattern_label: Optional[str] = None # Pattern-based label
    pattern_score: Optional[float] = None # Pattern-based score
    
    # NLP details (if used)
    nlp_confidence: Optional[float] = None  # NLP model confidence
    nlp_label: Optional[str] = None         # NLP-based label
    nlp_score: Optional[float] = None       # NLP-based score
    
    # Context flags
    has_negation: bool = False          # Negation detected
    has_sarcasm: bool = False           # Sarcasm indicators found
    has_conflict: bool = False          # Conflicting signals detected
    
    # Crypto-specific
    crypto_terms: List[str] = field(default_factory=list)  # Matched crypto terms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'label': self.label,
            'score': self.score,
            'confidence': self.confidence,
            'method': self.method,
            'processing_time_ms': self.processing_time_ms,
            'pattern_confidence': self.pattern_confidence,
            'pattern_label': self.pattern_label,
            'pattern_score': self.pattern_score,
            'nlp_confidence': self.nlp_confidence,
            'nlp_label': self.nlp_label,
            'nlp_score': self.nlp_score,
            'has_negation': self.has_negation,
            'has_sarcasm': self.has_sarcasm,
            'has_conflict': self.has_conflict,
            'crypto_terms': self.crypto_terms
        }
