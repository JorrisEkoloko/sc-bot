"""
Unit tests for pattern-based sentiment analysis.

Tests the PatternMatcher component including:
- Existing positive/negative/neutral cases
- New crypto vocabulary
- Confidence calculation
- Conflicting signal detection
"""

import pytest
from services.analytics.pattern_matcher import PatternMatcher
from services.analytics.sentiment_config import SentimentConfig


class TestPatternMatcherBasic:
    """Test basic pattern matching functionality."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with default config."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_positive_sentiment(self, matcher):
        """Test clear positive sentiment detection."""
        text = "Bitcoin is bullish! Moon rocket 🚀"
        label, score = matcher.analyze(text)
        
        assert label == 'positive'
        assert score > 0.5
    
    def test_negative_sentiment(self, matcher):
        """Test clear negative sentiment detection."""
        text = "This is a scam! Dump and crash 📉"
        label, score = matcher.analyze(text)
        
        assert label == 'negative'
        assert score < -0.5
    
    def test_neutral_sentiment(self, matcher):
        """Test neutral sentiment (no indicators)."""
        text = "The price is currently at $50,000"
        label, score = matcher.analyze(text)
        
        assert label == 'neutral'
        assert score == 0.0
    
    def test_empty_text(self, matcher):
        """Test handling of empty text."""
        label, score = matcher.analyze("")
        
        assert label == 'neutral'
        assert score == 0.0


class TestCryptoVocabulary:
    """Test crypto-specific vocabulary."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with crypto vocabulary enabled."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_crypto_positive_wagmi(self, matcher):
        """Test WAGMI (We're All Gonna Make It)."""
        text = "WAGMI frens! 🚀"
        label, score = matcher.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_crypto_positive_lfg(self, matcher):
        """Test LFG (Let's F***ing Go)."""
        text = "LFG to the moon!"
        label, score = matcher.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_crypto_positive_diamond_hands(self, matcher):
        """Test diamond hands."""
        text = "Diamond hands holding strong 💎"
        label, score = matcher.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_crypto_positive_hodl(self, matcher):
        """Test HODL."""
        text = "Just hodl and be patient"
        label, score = matcher.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_crypto_positive_alpha(self, matcher):
        """Test alpha (exclusive information)."""
        text = "Got some alpha on this project"
        label, score = matcher.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_crypto_negative_rekt(self, matcher):
        """Test rekt (wrecked)."""
        text = "Got rekt on that trade"
        label, score = matcher.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_crypto_negative_paper_hands(self, matcher):
        """Test paper hands."""
        text = "Paper hands selling at the bottom"
        label, score = matcher.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_crypto_negative_fud(self, matcher):
        """Test FUD (Fear, Uncertainty, Doubt)."""
        text = "Stop spreading FUD about this project"
        label, score = matcher.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_crypto_negative_rugged(self, matcher):
        """Test rugged (rug pulled)."""
        text = "Project rugged, lost everything"
        label, score = matcher.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_crypto_negative_bagholder(self, matcher):
        """Test bagholder."""
        text = "Now I'm a bagholder stuck with losses"
        label, score = matcher.analyze(text)
        
        assert label == 'negative'
        assert score < 0


class TestConfidenceCalculation:
    """Test confidence score calculation."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with default config."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_high_confidence_multiple_indicators(self, matcher):
        """Test high confidence with multiple clear indicators."""
        text = "Bullish pump! Moon rocket gains! 🚀📈"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        assert label == 'positive'
        assert confidence > 0.7
    
    def test_low_confidence_single_indicator(self, matcher):
        """Test lower confidence with single indicator."""
        text = "moon"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        assert label == 'positive'
        assert confidence < 0.7
    
    def test_neutral_zero_confidence(self, matcher):
        """Test neutral sentiment has zero confidence."""
        text = "The price is $50,000"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        assert label == 'neutral'
        assert confidence == 0.0
    
    def test_confidence_increases_with_matches(self, matcher):
        """Test confidence increases with more matches."""
        text1 = "bullish"
        text2 = "bullish pump moon rocket"
        
        _, _, conf1, _ = matcher.analyze_with_confidence(text1)
        _, _, conf2, _ = matcher.analyze_with_confidence(text2)
        
        assert conf2 > conf1
    
    def test_short_text_penalty(self, matcher):
        """Test confidence penalty for very short text."""
        text = "moon"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        # Short text should have reduced confidence
        assert confidence <= 0.5


class TestConflictingSignals:
    """Test detection of conflicting signals."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with default config."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_conflicting_signals_detected(self, matcher):
        """Test detection of both positive and negative signals."""
        text = "Bullish setup but could dump if support breaks"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        assert has_conflict is True
    
    def test_conflicting_signals_reduce_confidence(self, matcher):
        """Test that conflicting signals reduce confidence."""
        text_clear = "Bullish pump moon rocket"
        text_conflict = "Bullish but could dump"
        
        _, _, conf_clear, _ = matcher.analyze_with_confidence(text_clear)
        _, _, conf_conflict, _ = matcher.analyze_with_confidence(text_conflict)
        
        assert conf_conflict < conf_clear
    
    def test_no_conflict_positive_only(self, matcher):
        """Test no conflict with only positive signals."""
        text = "Bullish pump gains moon"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        assert has_conflict is False
    
    def test_no_conflict_negative_only(self, matcher):
        """Test no conflict with only negative signals."""
        text = "Dump crash scam bearish"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        assert has_conflict is False
    
    def test_minor_conflict_not_detected(self, matcher):
        """Test that minor conflicts (low ratio) are not flagged."""
        text = "Bullish pump moon rocket gains with minor risk"
        label, score, confidence, has_conflict = matcher.analyze_with_confidence(text)
        
        # Should be positive with no conflict (ratio too low)
        assert label == 'positive'


class TestNegationDetection:
    """Test negation keyword detection."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with default config."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_negation_with_positive_word(self, matcher):
        """Test negation detected near positive word."""
        text = "Not bullish on this project"
        has_negation = matcher.detect_negation(text)
        
        assert has_negation is True
    
    def test_negation_with_negative_word(self, matcher):
        """Test negation detected near negative word."""
        text = "Don't dump your bags yet"
        has_negation = matcher.detect_negation(text)
        
        assert has_negation is True
    
    def test_no_negation(self, matcher):
        """Test no negation in clear positive text."""
        text = "Bullish pump to the moon"
        has_negation = matcher.detect_negation(text)
        
        assert has_negation is False
    
    def test_negation_keywords(self, matcher):
        """Test various negation keywords."""
        negation_texts = [
            "never going to moon",
            "no pump happening",
            "won't buy this",
            "isn't bullish"
        ]
        
        for text in negation_texts:
            has_negation = matcher.detect_negation(text)
            assert has_negation is True, f"Failed to detect negation in: {text}"


class TestSarcasmDetection:
    """Test sarcasm indicator detection."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with default config."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_sarcasm_emoji_eye_roll(self, matcher):
        """Test eye roll emoji detection."""
        text = "Yeah sure, this will moon 🙄"
        has_sarcasm = matcher.detect_sarcasm(text)
        
        assert has_sarcasm is True
    
    def test_sarcasm_emoji_clown(self, matcher):
        """Test clown emoji detection."""
        text = "Great project 🤡"
        has_sarcasm = matcher.detect_sarcasm(text)
        
        assert has_sarcasm is True
    
    def test_quoted_positive_word(self, matcher):
        """Test quoted positive words as sarcasm."""
        text = 'This will "moon" definitely'
        has_sarcasm = matcher.detect_sarcasm(text)
        
        assert has_sarcasm is True
    
    def test_excessive_punctuation(self, matcher):
        """Test excessive punctuation as sarcasm."""
        text = "This is great!!!"
        has_sarcasm = matcher.detect_sarcasm(text)
        
        assert has_sarcasm is True
    
    def test_no_sarcasm(self, matcher):
        """Test no sarcasm in genuine positive text."""
        text = "Bullish on this project"
        has_sarcasm = matcher.detect_sarcasm(text)
        
        assert has_sarcasm is False


class TestCryptoTermExtraction:
    """Test extraction of crypto-specific terms."""
    
    @pytest.fixture
    def matcher(self):
        """Create pattern matcher with crypto vocabulary enabled."""
        config = SentimentConfig(use_crypto_vocabulary=True)
        return PatternMatcher(config)
    
    def test_extract_positive_terms(self, matcher):
        """Test extraction of positive crypto terms."""
        text = "WAGMI frens! Diamond hands hodl!"
        terms = matcher.extract_crypto_terms(text)
        
        assert 'wagmi' in terms
        assert 'fren' in terms
        assert 'diamond hands' in terms
        assert 'hodl' in terms
    
    def test_extract_negative_terms(self, matcher):
        """Test extraction of negative crypto terms."""
        text = "Got rekt, paper hands rugged"
        terms = matcher.extract_crypto_terms(text)
        
        assert 'rekt' in terms
        assert 'paper hands' in terms
        assert 'rugged' in terms
    
    def test_extract_mixed_terms(self, matcher):
        """Test extraction of mixed positive and negative terms."""
        text = "WAGMI but some paper hands got rekt"
        terms = matcher.extract_crypto_terms(text)
        
        assert 'wagmi' in terms
        assert 'paper hands' in terms
        assert 'rekt' in terms
    
    def test_no_crypto_terms(self, matcher):
        """Test no extraction when no crypto terms present."""
        text = "The price is going up"
        terms = matcher.extract_crypto_terms(text)
        
        assert len(terms) == 0
    
    def test_crypto_vocabulary_disabled(self):
        """Test no extraction when crypto vocabulary disabled."""
        config = SentimentConfig(use_crypto_vocabulary=False)
        matcher = PatternMatcher(config)
        
        text = "WAGMI frens hodl"
        terms = matcher.extract_crypto_terms(text)
        
        assert len(terms) == 0
