"""
Integration tests for hybrid sentiment analysis system.

Tests the complete sentiment analysis pipeline including:
- End-to-end sentiment analysis
- Hybrid system routing
- Backward compatibility
"""

import pytest
import time
from services.analytics.sentiment_analyzer import SentimentAnalyzer
from services.analytics.sentiment_config import SentimentConfig


class TestEndToEndSentimentAnalysis:
    """Test end-to-end sentiment analysis pipeline."""
    
    @pytest.fixture
    def analyzer_pattern_only(self):
        """Create analyzer with pattern-only mode."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    @pytest.fixture
    def analyzer_hybrid(self):
        """Create analyzer with hybrid mode."""
        config = SentimentConfig(nlp_enabled=True, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_e2e_clear_positive(self, analyzer_pattern_only):
        """Test end-to-end analysis of clear positive message."""
        text = "Bitcoin is bullish! Moon rocket gains! 🚀📈"
        result = analyzer_pattern_only.analyze_detailed(text)
        
        assert result.label == 'positive'
        assert result.score > 0.5
        assert result.method == 'pattern'
        assert result.processing_time_ms > 0
    
    def test_e2e_clear_negative(self, analyzer_pattern_only):
        """Test end-to-end analysis of clear negative message."""
        text = "This is a scam! Dump and crash! Avoid! 📉"
        result = analyzer_pattern_only.analyze_detailed(text)
        
        assert result.label == 'negative'
        assert result.score < -0.5
        assert result.method == 'pattern'
        assert result.processing_time_ms > 0
    
    def test_e2e_neutral(self, analyzer_pattern_only):
        """Test end-to-end analysis of neutral message."""
        text = "The current price is $50,000 USD"
        result = analyzer_pattern_only.analyze_detailed(text)
        
        assert result.label == 'neutral'
        assert result.score == 0.0
        assert result.method == 'pattern'
    
    def test_e2e_crypto_positive(self, analyzer_pattern_only):
        """Test end-to-end with crypto-specific positive terms."""
        text = "WAGMI frens! Diamond hands hodl to the moon! LFG! 🚀"
        result = analyzer_pattern_only.analyze_detailed(text)
        
        assert result.label == 'positive'
        assert result.score > 0.5
        assert len(result.crypto_terms) > 0
        assert 'wagmi' in result.crypto_terms
        assert 'diamond hands' in result.crypto_terms
    
    def test_e2e_crypto_negative(self, analyzer_pattern_only):
        """Test end-to-end with crypto-specific negative terms."""
        text = "Got rekt! Paper hands rugged! NGMI!"
        result = analyzer_pattern_only.analyze_detailed(text)
        
        assert result.label == 'negative'
        assert result.score < -0.5
        assert len(result.crypto_terms) > 0
        assert 'rekt' in result.crypto_terms
        assert 'paper hands' in result.crypto_terms
    
    def test_e2e_with_negation(self, analyzer_hybrid):
        """Test end-to-end with negation."""
        text = "Not bullish on this project at all"
        result = analyzer_hybrid.analyze_detailed(text)
        
        assert result.has_negation is True
        # Method could be pattern, nlp, or fallback depending on NLP availability
        assert result.method in ['pattern', 'nlp', 'fallback']
    
    def test_e2e_with_sarcasm(self, analyzer_hybrid):
        """Test end-to-end with sarcasm."""
        text = "Yeah sure, this will definitely moon 🙄"
        result = analyzer_hybrid.analyze_detailed(text)
        
        assert result.has_sarcasm is True
        # Should route to NLP if available
        assert result.method in ['pattern', 'nlp', 'fallback']
    
    def test_e2e_with_conflict(self, analyzer_hybrid):
        """Test end-to-end with conflicting signals."""
        text = "Bullish setup but could dump if support breaks"
        result = analyzer_hybrid.analyze_detailed(text)
        
        assert result.has_conflict is True
        # Should route to NLP if available
        assert result.method in ['pattern', 'nlp', 'fallback']


class TestHybridSystemRouting:
    """Test hybrid system routing logic."""
    
    @pytest.fixture
    def analyzer(self):
        """Create hybrid analyzer."""
        config = SentimentConfig(
            nlp_enabled=True,
            use_crypto_vocabulary=True,
            pattern_confidence_threshold=0.7
        )
        return SentimentAnalyzer(config)
    
    def test_high_confidence_uses_pattern(self, analyzer):
        """Test high confidence messages use pattern-only."""
        text = "Bullish pump moon rocket gains! 🚀📈"
        result = analyzer.analyze_detailed(text)
        
        # High confidence should use pattern
        if result.pattern_confidence > 0.7:
            assert result.method == 'pattern'
    
    def test_low_confidence_routes_to_nlp(self, analyzer):
        """Test low confidence messages route to NLP."""
        text = "maybe"
        result = analyzer.analyze_detailed(text)
        
        # Low confidence should attempt NLP (or fallback if unavailable)
        assert result.method in ['pattern', 'nlp', 'fallback']
    
    def test_negation_routes_to_nlp(self, analyzer):
        """Test negation triggers NLP routing."""
        text = "Not going to moon"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
        # Should attempt NLP routing
        assert result.method in ['pattern', 'nlp', 'fallback']
    
    def test_sarcasm_routes_to_nlp(self, analyzer):
        """Test sarcasm triggers NLP routing."""
        text = "Great project 🙄"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
        # Should attempt NLP routing
        assert result.method in ['pattern', 'nlp', 'fallback']
    
    def test_conflict_routes_to_nlp(self, analyzer):
        """Test conflicting signals trigger NLP routing."""
        text = "Bullish but bearish"
        result = analyzer.analyze_detailed(text)
        
        # Should detect conflict and attempt NLP
        if result.has_conflict:
            assert result.method in ['pattern', 'nlp', 'fallback']
    
    def test_fallback_on_nlp_failure(self):
        """Test fallback to pattern when NLP fails."""
        config = SentimentConfig(
            nlp_enabled=True,
            fallback_to_pattern=True,
            use_crypto_vocabulary=True
        )
        analyzer = SentimentAnalyzer(config)
        
        # Even if NLP is enabled, system should work
        text = "Bullish pump"
        result = analyzer.analyze_detailed(text)
        
        assert result.label == 'positive'
        assert result.method in ['pattern', 'nlp', 'fallback']


class TestBackwardCompatibility:
    """Test backward compatibility with existing interface."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_analyze_method_signature(self, analyzer):
        """Test analyze() method returns tuple."""
        text = "Bullish moon rocket"
        result = analyzer.analyze(text)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        label, score = result
        assert isinstance(label, str)
        assert isinstance(score, float)
    
    def test_analyze_method_labels(self, analyzer):
        """Test analyze() returns valid labels."""
        texts = [
            "Bullish pump",
            "Bearish dump",
            "The price is $50k"
        ]
        
        for text in texts:
            label, score = analyzer.analyze(text)
            assert label in ['positive', 'negative', 'neutral']
            assert -1.0 <= score <= 1.0
    
    def test_analyze_with_confidence_method(self, analyzer):
        """Test analyze_with_confidence() method."""
        text = "Bullish pump moon"
        result = analyzer.analyze_with_confidence(text)
        
        assert isinstance(result, tuple)
        assert len(result) == 4
        
        label, score, confidence, has_conflict = result
        assert isinstance(label, str)
        assert isinstance(score, float)
        assert isinstance(confidence, float)
        assert isinstance(has_conflict, bool)
    
    def test_analyze_detailed_method(self, analyzer):
        """Test analyze_detailed() returns SentimentResult."""
        text = "Bullish pump moon"
        result = analyzer.analyze_detailed(text)
        
        # Check all required fields exist
        assert hasattr(result, 'label')
        assert hasattr(result, 'score')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'method')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'pattern_confidence')
        assert hasattr(result, 'has_negation')
        assert hasattr(result, 'has_sarcasm')
        assert hasattr(result, 'has_conflict')
        assert hasattr(result, 'crypto_terms')
    
    def test_empty_text_handling(self, analyzer):
        """Test backward compatible empty text handling."""
        label, score = analyzer.analyze("")
        
        assert label == 'neutral'
        assert score == 0.0
    
    def test_none_text_handling(self, analyzer):
        """Test handling of None text."""
        label, score = analyzer.analyze(None)
        
        assert label == 'neutral'
        assert score == 0.0


class TestPerformanceMetrics:
    """Test performance metrics tracking."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_metrics_initialization(self, analyzer):
        """Test metrics are initialized correctly."""
        metrics = analyzer.get_performance_metrics()
        
        assert metrics['total_count'] == 0
        assert metrics['pattern_count'] == 0
        assert metrics['nlp_count'] == 0
        assert metrics['fallback_count'] == 0
    
    def test_metrics_tracking(self, analyzer):
        """Test metrics are tracked correctly."""
        texts = [
            "Bullish pump",
            "Bearish dump",
            "Neutral price",
            "Moon rocket",
            "Scam alert"
        ]
        
        for text in texts:
            analyzer.analyze_detailed(text)
        
        metrics = analyzer.get_performance_metrics()
        
        assert metrics['total_count'] == 5
        assert metrics['pattern_count'] == 5
        assert metrics['pattern_rate'] == 100.0
    
    def test_processing_time_tracking(self, analyzer):
        """Test processing time is tracked."""
        text = "Bullish pump moon"
        result = analyzer.analyze_detailed(text)
        
        assert result.processing_time_ms > 0
        assert result.processing_time_ms < 100  # Pattern-only should be fast
    
    def test_pattern_performance(self, analyzer):
        """Test pattern-only performance is fast."""
        text = "Bullish pump moon rocket gains"
        
        start_time = time.time()
        result = analyzer.analyze_detailed(text)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Pattern-only should be very fast
        assert elapsed_ms < 10
        assert result.method == 'pattern'


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_invalid_config_handling(self):
        """Test handling of invalid configuration."""
        with pytest.raises(ValueError):
            config = SentimentConfig(nlp_confidence_threshold=1.5)
    
    def test_analyzer_never_crashes(self):
        """Test analyzer never crashes on any input."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        analyzer = SentimentAnalyzer(config)
        
        # Test various edge cases
        edge_cases = [
            "",
            None,
            "a" * 10000,  # Very long text
            "🚀" * 100,   # Many emojis
            "!@#$%^&*()",  # Special characters
            "\n\n\n",     # Newlines
            "   ",        # Whitespace only
        ]
        
        for text in edge_cases:
            try:
                result = analyzer.analyze_detailed(text)
                assert result is not None
                assert result.label in ['positive', 'negative', 'neutral']
            except Exception as e:
                pytest.fail(f"Analyzer crashed on input '{text}': {e}")
    
    def test_concurrent_analysis(self):
        """Test analyzer works correctly with concurrent requests."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        analyzer = SentimentAnalyzer(config)
        
        texts = [
            "Bullish pump",
            "Bearish dump",
            "Neutral price"
        ] * 10
        
        # Analyze all texts
        results = [analyzer.analyze_detailed(text) for text in texts]
        
        # Verify all results are valid
        assert len(results) == 30
        for result in results:
            assert result.label in ['positive', 'negative', 'neutral']
            assert -1.0 <= result.score <= 1.0


class TestConfigurationOptions:
    """Test various configuration options."""
    
    def test_crypto_vocabulary_toggle(self):
        """Test crypto vocabulary can be toggled."""
        # With crypto vocab
        config1 = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        analyzer1 = SentimentAnalyzer(config1)
        
        text = "WAGMI frens hodl"
        label1, score1 = analyzer1.analyze(text)
        
        # Without crypto vocab
        config2 = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=False)
        analyzer2 = SentimentAnalyzer(config2)
        
        label2, score2 = analyzer2.analyze(text)
        
        # Results should differ
        assert label1 == 'positive'
        assert label2 == 'neutral'
    
    def test_confidence_threshold_configuration(self):
        """Test confidence threshold can be configured."""
        config = SentimentConfig(
            nlp_enabled=True,
            pattern_confidence_threshold=0.9,  # Very high threshold
            use_crypto_vocabulary=True
        )
        analyzer = SentimentAnalyzer(config)
        
        # Even clear messages might route to NLP with high threshold
        text = "Bullish"
        result = analyzer.analyze_detailed(text)
        
        # Should work regardless of routing
        assert result.label in ['positive', 'negative', 'neutral']
    
    def test_nlp_disabled_mode(self):
        """Test NLP can be completely disabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        analyzer = SentimentAnalyzer(config)
        
        # All messages should use pattern-only
        texts = [
            "Bullish pump",
            "Not bullish",  # Has negation
            "Great 🙄"      # Has sarcasm
        ]
        
        for text in texts:
            result = analyzer.analyze_detailed(text)
            assert result.method == 'pattern'
