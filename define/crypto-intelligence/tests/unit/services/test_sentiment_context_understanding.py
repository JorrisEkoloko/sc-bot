"""
Unit tests for context understanding in sentiment analysis.

Tests the hybrid sentiment analyzer's ability to understand:
- Negation handling (20 cases)
- Sarcasm detection (10 cases)
- Conditional sentiment (10 cases)
"""

import pytest
from services.analytics.sentiment_analyzer import SentimentAnalyzer
from services.analytics.sentiment_config import SentimentConfig


class TestNegationHandling:
    """Test negation handling with 20 test cases."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with NLP enabled."""
        config = SentimentConfig(nlp_enabled=True, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_negation_not_bullish(self, analyzer):
        """Test: Not bullish."""
        text = "Not bullish on this project"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
        # Pattern would say positive, but negation should be detected
    
    def test_negation_dont_buy(self, analyzer):
        """Test: Don't buy."""
        text = "Don't buy this pump and dump"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_never_moon(self, analyzer):
        """Test: Never going to moon."""
        text = "This will never moon"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_no_gains(self, analyzer):
        """Test: No gains."""
        text = "No gains on this trade"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_not_scam(self, analyzer):
        """Test: Not a scam (double negative = positive)."""
        text = "Not a scam, legit project"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_wont_dump(self, analyzer):
        """Test: Won't dump."""
        text = "This won't dump, strong support"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_cannot_buy(self, analyzer):
        """Test: Cannot buy."""
        text = "Cannot buy this pump"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_isnt_bearish(self, analyzer):
        """Test: Isn't bearish."""
        text = "Market isn't bearish anymore"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_doesnt_pump(self, analyzer):
        """Test: Doesn't pump."""
        text = "Chart doesn't pump anymore"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_didnt_pump(self, analyzer):
        """Test: Didn't pump."""
        text = "Token didn't pump as expected"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_never_selling(self, analyzer):
        """Test: Never selling (positive with negation)."""
        text = "Never selling, diamond hands"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_no_way_dumping(self, analyzer):
        """Test: No way I'm dumping."""
        text = "No way I'm dumping this gem"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_not_bearish(self, analyzer):
        """Test: Not bearish."""
        text = "Not bearish about the dip"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_none_bullish(self, analyzer):
        """Test: None more bullish."""
        text = "None more bullish than this"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_nobody_dump(self, analyzer):
        """Test: Nobody will dump."""
        text = "Nobody will dump"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_nothing_bearish(self, analyzer):
        """Test: Nothing bearish."""
        text = "Nothing bearish about this chart"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_neither_bullish_nor_bearish(self, analyzer):
        """Test: Neither bullish nor bearish."""
        text = "Neither bullish nor bearish, just sideways"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_nowhere_near_moon(self, analyzer):
        """Test: Nowhere near moon."""
        text = "Price is nowhere near moon"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_shouldnt_sell(self, analyzer):
        """Test: Shouldn't sell."""
        text = "You shouldn't sell at the bottom"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_negation_couldnt_be_more_bullish(self, analyzer):
        """Test: Couldn't be more bullish."""
        text = "Timing couldn't be more bullish"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True


class TestSarcasmDetection:
    """Test sarcasm detection with 10 test cases."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with NLP enabled."""
        config = SentimentConfig(nlp_enabled=True, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_sarcasm_eye_roll_emoji(self, analyzer):
        """Test: Eye roll emoji."""
        text = "Yeah sure, this will definitely moon 🙄"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_clown_emoji(self, analyzer):
        """Test: Clown emoji."""
        text = "Great project, totally not a scam 🤡"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_quoted_moon(self, analyzer):
        """Test: Quoted 'moon'."""
        text = 'This will "moon" for sure'
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_quoted_bullish(self, analyzer):
        """Test: Quoted 'bullish'."""
        text = '"Bullish" they said'
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_excessive_exclamation(self, analyzer):
        """Test: Excessive exclamation marks."""
        text = "This is amazing!!!"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_excessive_question(self, analyzer):
        """Test: Excessive question marks."""
        text = "You really think this will pump???"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_facepalm_emoji(self, analyzer):
        """Test: Facepalm emoji."""
        text = "Another rug pull 🤦"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_shrug_emoji(self, analyzer):
        """Test: Shrug emoji."""
        text = "Lost all my money 🤷"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_smirk_emoji(self, analyzer):
        """Test: Smirk emoji."""
        text = "Trust me bro 😏"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_sarcasm_quoted_gains(self, analyzer):
        """Test: Quoted 'gains'."""
        text = 'Totally "gains" incoming'
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True


class TestConditionalSentiment:
    """Test conditional sentiment with 10 test cases."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with NLP enabled."""
        config = SentimentConfig(nlp_enabled=True, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_conditional_if_breaks(self, analyzer):
        """Test: Bullish IF it breaks resistance."""
        text = "Bullish IF it breaks $50k resistance"
        result = analyzer.analyze_detailed(text)
        
        # Should detect positive sentiment but with context
        assert result.label in ['positive', 'neutral']
    
    def test_conditional_when_btc_recovers(self, analyzer):
        """Test: Will moon WHEN BTC recovers."""
        text = "Will moon when BTC recovers"
        result = analyzer.analyze_detailed(text)
        
        # Conditional future sentiment
        assert result.label in ['positive', 'neutral']
    
    def test_conditional_unless_dumps(self, analyzer):
        """Test: Bullish UNLESS it dumps."""
        text = "Bullish setup unless it dumps below support"
        result = analyzer.analyze_detailed(text)
        
        # Mixed conditional - should detect conflict or have positive with some confidence
        assert result.has_conflict or result.label in ['positive', 'neutral']
    
    def test_conditional_if_volume_increases(self, analyzer):
        """Test: Will pump IF volume increases."""
        text = "Will pump if volume increases"
        result = analyzer.analyze_detailed(text)
        
        assert result.label in ['positive', 'neutral']
    
    def test_conditional_could_moon(self, analyzer):
        """Test: COULD moon (possibility)."""
        text = "This could moon if everything aligns"
        result = analyzer.analyze_detailed(text)
        
        # Uncertain/conditional
        assert result.label in ['positive', 'neutral']
    
    def test_conditional_might_dump(self, analyzer):
        """Test: MIGHT dump (possibility)."""
        text = "Might dump if support breaks"
        result = analyzer.analyze_detailed(text)
        
        # Uncertain/conditional negative
        assert result.label in ['negative', 'neutral']
    
    def test_conditional_depends_on(self, analyzer):
        """Test: DEPENDS ON market conditions."""
        text = "Success depends on market conditions"
        result = analyzer.analyze_detailed(text)
        
        # Neutral conditional
        assert result.label == 'neutral' or result.confidence < 0.7
    
    def test_conditional_assuming_holds(self, analyzer):
        """Test: Bullish ASSUMING support holds."""
        text = "Bullish assuming support holds"
        result = analyzer.analyze_detailed(text)
        
        assert result.label in ['positive', 'neutral']
    
    def test_conditional_provided_that(self, analyzer):
        """Test: Will rally PROVIDED THAT."""
        text = "Will rally provided that volume comes in"
        result = analyzer.analyze_detailed(text)
        
        assert result.label in ['positive', 'neutral']
    
    def test_conditional_as_long_as(self, analyzer):
        """Test: Bullish AS LONG AS."""
        text = "Bullish as long as BTC stays above 40k"
        result = analyzer.analyze_detailed(text)
        
        assert result.label in ['positive', 'neutral']


class TestComplexContextCases:
    """Test complex context understanding scenarios."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with NLP enabled."""
        config = SentimentConfig(nlp_enabled=True, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_negation_with_sarcasm(self, analyzer):
        """Test: Negation combined with sarcasm."""
        text = 'Not a scam at all 🙄'
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
        assert result.has_sarcasm is True
    
    def test_conditional_with_negation(self, analyzer):
        """Test: Conditional with negation."""
        text = "Won't pump unless volume increases"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_multiple_negations(self, analyzer):
        """Test: Multiple negations in one sentence."""
        text = "Not saying it won't moon, but don't expect miracles"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_negation is True
    
    def test_sarcasm_with_positive_words(self, analyzer):
        """Test: Sarcasm with positive words."""
        text = "Amazing project, definitely not a rug pull 🤡"
        result = analyzer.analyze_detailed(text)
        
        assert result.has_sarcasm is True
    
    def test_conditional_with_conflict(self, analyzer):
        """Test: Conditional with conflicting signals."""
        text = "Bullish if it pumps, bearish if it dumps"
        result = analyzer.analyze_detailed(text)
        
        # Should detect conflict or be neutral
        assert result.has_conflict or result.label == 'neutral'
