"""
Hybrid sentiment analyzer orchestrating pattern matching and NLP.

Classifies messages as positive, negative, or neutral using a two-stage approach:
1. Fast pattern matching for high-confidence cases
2. NLP enhancement for complex/ambiguous cases

Example:
    >>> analyzer = SentimentAnalyzer()
    >>> result = analyzer.analyze_detailed("Bitcoin is going to the moon! 🚀")
    >>> print(f"{result.label}: {result.score:.2f}")
    positive: 0.85
"""

import time
import threading
from typing import Tuple, Dict, Any, Literal
from utils.logger import get_logger
from services.analytics.sentiment_config import SentimentConfig
from services.analytics.sentiment_result import SentimentResult
from services.analytics.pattern_matcher import PatternMatcher
from services.analytics.nlp_analyzer import NLPAnalyzer


class SentimentAnalyzer:
    """
    Hybrid sentiment analyzer using pattern matching and NLP.
    
    Orchestrates a two-stage sentiment analysis pipeline:
    1. Pattern matching (fast, high-confidence)
    2. NLP enhancement (slower, handles complex cases)
    """
    
    def __init__(self, config: SentimentConfig = None):
        """
        Initialize sentiment analyzer.
        
        Args:
            config: Optional configuration. If None, loads from environment.
        """
        self.logger = get_logger('SentimentAnalyzer')
        self.config = config or SentimentConfig.from_env()
        
        # Initialize pattern matcher
        self.pattern_matcher = PatternMatcher(self.config)
        
        # Initialize NLP analyzer if enabled
        self.nlp_analyzer = None
        if self.config.nlp_enabled:
            try:
                self.nlp_analyzer = NLPAnalyzer(self.config)
                self.logger.info("NLP analyzer initialized")
                
                # Pre-load model at startup to avoid first-inference delay
                self._preload_nlp_model()
            except Exception as e:
                self.logger.warning(f"Failed to initialize NLP analyzer: {e}")
                if not self.config.fallback_to_pattern:
                    raise
        
        # Performance tracking (thread-safe)
        self._metrics_lock = threading.Lock()
        self._pattern_count = 0
        self._nlp_count = 0
        self._fallback_count = 0
        self._total_count = 0
        self._total_inference_time_ms = 0.0
        self._nlp_inference_time_ms = 0.0
        
        self.logger.info(
            f"Sentiment analyzer initialized "
            f"(NLP: {'enabled' if self.config.nlp_enabled else 'disabled'})"
        )
    
    def _preload_nlp_model(self):
        """Pre-load NLP model at startup to avoid first-inference delay."""
        if not self.nlp_analyzer:
            return
        
        try:
            import time
            self.logger.info("Pre-loading NLP model (this may take 10-20 seconds)...")
            start_time = time.time()
            
            # Run a dummy inference to trigger model loading
            test_text = "Bitcoin is going to the moon"
            self.nlp_analyzer.analyze(test_text)
            
            load_time = (time.time() - start_time) * 1000
            self.logger.info(f"✓ NLP model pre-loaded successfully ({load_time:.0f}ms)")
        except Exception as e:
            self.logger.warning(f"Failed to pre-load NLP model: {e}")
            # Don't raise - model will load on first real inference
    
    def analyze(self, text: str) -> Tuple[Literal['positive', 'negative', 'neutral'], float]:
        """
        Analyze sentiment of text (backward compatible interface).
        
        Args:
            text: Message text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score)
            - sentiment_label: 'positive', 'negative', or 'neutral'
            - sentiment_score: -1.0 to +1.0
        """
        return self.pattern_matcher.analyze(text)
    
    def analyze_with_confidence(self, text: str) -> Tuple[Literal['positive', 'negative', 'neutral'], float, float, bool]:
        """
        Analyze sentiment with confidence score (backward compatible interface).
        
        Args:
            text: Message text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score, confidence, has_conflict)
            - sentiment_label: 'positive', 'negative', or 'neutral'
            - sentiment_score: -1.0 to +1.0
            - confidence: 0.0 to 1.0
            - has_conflict: True if conflicting signals detected
        """
        return self.pattern_matcher.analyze_with_confidence(text)
    
    def analyze_detailed(self, text: str) -> SentimentResult:
        """
        Analyze sentiment with detailed results including all metadata.
        
        This is the main hybrid analysis method that:
        1. Calls pattern matcher first
        2. Evaluates confidence
        3. Routes to NLP if needed
        4. Merges and returns results
        
        Args:
            text: Message text to analyze
            
        Returns:
            SentimentResult with complete analysis details
        """
        start_time = time.time()
        method = 'pattern'  # Default method for metrics
        nlp_inference_time_ms = 0.0
        
        try:
            if not text:
                return self._format_result(
                    label='neutral',
                    score=0.0,
                    confidence=0.0,
                    method='pattern',
                    processing_time_ms=0.0
                )
            
            # Step 1: Get pattern-based analysis with confidence
            label, score, confidence, has_conflict = self.pattern_matcher.analyze_with_confidence(text)
            pattern_result = (label, score, confidence)
            
            # Detect context flags
            has_negation = self.pattern_matcher.detect_negation(text)
            has_sarcasm = self.pattern_matcher.detect_sarcasm(text)
            
            # Extract crypto terms
            crypto_terms = self.pattern_matcher.extract_crypto_terms(text)
            
            # Step 2: Evaluate confidence and decide if NLP is needed
            use_nlp = self._should_use_nlp(confidence, has_conflict, text)
            
            # Step 3: Route to NLP if needed
            nlp_result = None
            final_label = label
            final_score = score
            final_confidence = confidence
            
            if use_nlp and self.nlp_analyzer is not None:
                try:
                    # Invoke NLP analyzer (use sync wrapper for backward compatibility)
                    self.logger.debug("Routing to NLP for analysis")
                    nlp_start_time = time.time()
                    
                    # Call synchronous analyze method (handles async internally)
                    nlp_label, nlp_score, nlp_confidence = self.nlp_analyzer.analyze(text)
                    
                    nlp_inference_time_ms = (time.time() - nlp_start_time) * 1000
                    nlp_result = (nlp_label, nlp_score, nlp_confidence)
                    
                    # Use NLP results
                    final_label = nlp_label
                    final_score = nlp_score
                    final_confidence = nlp_confidence  # Use actual NLP model confidence
                    method = 'nlp'
                    
                    # Log NLP inference time and warn if slow
                    self.logger.debug(
                        f"NLP analysis: {nlp_label} (score: {nlp_score:+.2f}, "
                        f"inference_time: {nlp_inference_time_ms:.1f}ms)"
                    )
                    if nlp_inference_time_ms > 200:
                        self.logger.warning(
                            f"Slow NLP inference: {nlp_inference_time_ms:.1f}ms > 200ms threshold"
                        )
                    
                except Exception as e:
                    # Step 4: Fallback mechanism - catch NLP errors
                    error_type = type(e).__name__
                    self.logger.warning(
                        f"Fallback event: NLP inference failed ({error_type}: {str(e)[:100]}), "
                        f"using pattern result instead"
                    )
                    # Keep pattern results
                    method = 'fallback'
            
            # Step 5: Merge and return results
            result = self._format_result(
                label=final_label,
                score=final_score,
                confidence=final_confidence,
                method=method,
                processing_time_ms=(time.time() - start_time) * 1000,
                pattern_result=pattern_result,
                nlp_result=nlp_result,
                has_negation=has_negation,
                has_sarcasm=has_sarcasm,
                has_conflict=has_conflict,
                crypto_terms=crypto_terms
            )
            
            # Log classification method with confidence scores
            self.logger.debug(
                f"Classification method: {result.method} | "
                f"Sentiment: {result.label} (score: {result.score:+.2f}) | "
                f"Confidence: pattern={result.pattern_confidence:.2f}"
                f"{f', nlp={result.nlp_confidence:.2f}' if result.nlp_confidence else ''} | "
                f"Time: {result.processing_time_ms:.1f}ms"
            )
            
            return result
            
        except Exception as e:
            # Catch-all error handler - never raise unhandled exceptions
            self.logger.error(f"Error in sentiment analysis: {e}")
            method = 'fallback'
            return self._format_result(
                label='neutral',
                score=0.0,
                confidence=0.0,
                method='fallback',
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        finally:
            # ALWAYS update metrics, even on early exit or exception
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Capture all metrics atomically
            stats_snapshot = None
            with self._metrics_lock:
                self._total_count += 1
                self._total_inference_time_ms += processing_time_ms
                
                if method == 'nlp':
                    self._nlp_count += 1
                    self._nlp_inference_time_ms += nlp_inference_time_ms
                elif method == 'pattern':
                    self._pattern_count += 1
                elif method == 'fallback':
                    self._fallback_count += 1
                
                current_count = self._total_count
                should_log_stats = (current_count % self.config.stats_log_frequency == 0)
                
                # Capture stats snapshot while holding lock (prevents inconsistency)
                if should_log_stats and self._total_count > 0:
                    stats_snapshot = {
                        'total': self._total_count,
                        'pattern_rate': (self._pattern_count / self._total_count) * 100,
                        'nlp_rate': (self._nlp_count / self._total_count) * 100,
                        'fallback_rate': (self._fallback_count / self._total_count) * 100
                    }
            
            # Log performance warning if slow (outside lock)
            if processing_time_ms > 200:
                self.logger.warning(
                    f"Slow sentiment analysis: {processing_time_ms:.1f}ms"
                )
            
            # Log periodic statistics using snapshot (outside lock to avoid I/O while holding lock)
            if stats_snapshot:
                self.logger.info(
                    f"Sentiment stats (n={stats_snapshot['total']}): "
                    f"pattern={stats_snapshot['pattern_rate']:.1f}%, "
                    f"nlp={stats_snapshot['nlp_rate']:.1f}%, "
                    f"fallback={stats_snapshot['fallback_rate']:.1f}%"
                )
    
    def _should_use_nlp(
        self, 
        confidence: float, 
        has_conflict: bool,
        text: str
    ) -> bool:
        """
        Determine if NLP processing is needed.
        
        Routes to NLP if:
        - Confidence is below threshold (but not zero/neutral)
        - Conflicting signals detected
        - Negation detected
        - Sarcasm indicators found
        """
        if not self.config.nlp_enabled:
            return False
        
        if confidence == 0.0:
            return False
        
        if confidence < self.config.pattern_confidence_threshold:
            self.logger.debug(f"Low confidence ({confidence:.2f}), routing to NLP")
            return True
        
        if has_conflict:
            self.logger.debug("Conflicting signals detected, routing to NLP")
            return True
        
        if self.pattern_matcher.detect_negation(text):
            self.logger.debug("Negation detected, routing to NLP")
            return True
        
        if self.pattern_matcher.detect_sarcasm(text):
            self.logger.debug("Sarcasm indicators detected, routing to NLP")
            return True
        
        return False
    
    def _format_result(
        self,
        label: str,
        score: float,
        confidence: float,
        method: str,
        processing_time_ms: float,
        pattern_result: Tuple[str, float, float] = None,
        nlp_result: Tuple[str, float, float] = None,
        has_negation: bool = False,
        has_sarcasm: bool = False,
        has_conflict: bool = False,
        crypto_terms: list = None
    ) -> SentimentResult:
        """Format analysis results into SentimentResult dataclass."""
        pattern_label = None
        pattern_score = None
        pattern_confidence = confidence
        
        if pattern_result:
            pattern_label = pattern_result[0]
            pattern_score = pattern_result[1]
            pattern_confidence = pattern_result[2] if len(pattern_result) > 2 else confidence
        
        nlp_label = None
        nlp_score = None
        nlp_confidence = None
        
        if nlp_result:
            nlp_label = nlp_result[0]
            nlp_score = nlp_result[1]
            nlp_confidence = nlp_result[2] if len(nlp_result) > 2 else None
        
        return SentimentResult(
            label=label,
            score=score,
            confidence=confidence,
            method=method,
            processing_time_ms=processing_time_ms,
            pattern_confidence=pattern_confidence,
            pattern_label=pattern_label,
            pattern_score=pattern_score,
            nlp_confidence=nlp_confidence,
            nlp_label=nlp_label,
            nlp_score=nlp_score,
            has_negation=has_negation,
            has_sarcasm=has_sarcasm,
            has_conflict=has_conflict,
            crypto_terms=crypto_terms or []
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for sentiment analysis (thread-safe).
        
        Returns:
            Dictionary containing:
            - total_count: Total number of analyses performed
            - pattern_count: Number using pattern-only
            - nlp_count: Number using NLP
            - fallback_count: Number that fell back due to errors
            - pattern_rate: Percentage using pattern-only
            - nlp_rate: Percentage using NLP
            - fallback_rate: Percentage that fell back
            - avg_inference_time_ms: Average total inference time
            - avg_nlp_inference_time_ms: Average NLP-only inference time
        """
        with self._metrics_lock:
            if self._total_count == 0:
                return {
                    'total_count': 0,
                    'pattern_count': 0,
                    'nlp_count': 0,
                    'fallback_count': 0,
                    'pattern_rate': 0.0,
                    'nlp_rate': 0.0,
                    'fallback_rate': 0.0,
                    'avg_inference_time_ms': 0.0,
                    'avg_nlp_inference_time_ms': 0.0
                }
            
            avg_inference_time = self._total_inference_time_ms / self._total_count
            avg_nlp_inference_time = (
                self._nlp_inference_time_ms / self._nlp_count 
                if self._nlp_count > 0 else 0.0
            )
            
            return {
                'total_count': self._total_count,
                'pattern_count': self._pattern_count,
                'nlp_count': self._nlp_count,
                'fallback_count': self._fallback_count,
                'pattern_rate': (self._pattern_count / self._total_count) * 100,
                'nlp_rate': (self._nlp_count / self._total_count) * 100,
                'fallback_rate': (self._fallback_count / self._total_count) * 100,
                'avg_inference_time_ms': avg_inference_time,
                'avg_nlp_inference_time_ms': avg_nlp_inference_time
            }
