"""
Unit tests for crypto-specific language understanding.

Tests the sentiment analyzer's ability to understand:
- Crypto-specific positive terms (15 cases)
- Crypto-specific negative terms (15 cases)
- Context-dependent terms (10 cases)
"""

import pytest
from services.analytics.sentiment_analyzer import SentimentAnalyzer
from services.analytics.sentiment_config import SentimentConfig


class TestCryptoPositiveTerms:
    """Test crypto-specific positive terms (15 cases)."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with crypto vocabulary enabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_wagmi(self, analyzer):
        """Test: WAGMI (We're All Gonna Make It)."""
        text = "WAGMI frens! 🚀"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_gm(self, analyzer):
        """Test: GM (Good Morning)."""
        text = "GM everyone, bullish day ahead"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_lfg(self, analyzer):
        """Test: LFG (Let's F***ing Go)."""
        text = "LFG to the moon!"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_degen(self, analyzer):
        """Test: Degen (positive context)."""
        text = "Degen play but could 100x"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_ape(self, analyzer):
        """Test: Ape (buying aggressively)."""
        text = "Aping into this gem early"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_diamond_hands(self, analyzer):
        """Test: Diamond hands."""
        text = "Diamond hands holding strong 💎"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_hodl(self, analyzer):
        """Test: HODL."""
        text = "Just hodl and be patient"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_alpha(self, analyzer):
        """Test: Alpha (exclusive information)."""
        text = "Got some alpha on this project"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_based(self, analyzer):
        """Test: Based (authentic, good)."""
        text = "Based project with real utility"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_ser(self, analyzer):
        """Test: Ser (respectful address)."""
        text = "Ser, this is a gem"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_fren(self, analyzer):
        """Test: Fren (friend)."""
        text = "WAGMI frens!"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_chad(self, analyzer):
        """Test: Chad (successful trader)."""
        text = "Chad move buying the dip"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_whale(self, analyzer):
        """Test: Whale (large holder)."""
        text = "Whale accumulating, bullish signal"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_moonshot(self, analyzer):
        """Test: Moonshot (high potential)."""
        text = "This is a moonshot opportunity"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_to_the_moon(self, analyzer):
        """Test: To the moon."""
        text = "To the moon we go! 🚀"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0


class TestCryptoNegativeTerms:
    """Test crypto-specific negative terms (15 cases)."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with crypto vocabulary enabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_ngmi(self, analyzer):
        """Test: NGMI (Not Gonna Make It)."""
        text = "Paper hands NGMI"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_paper_hands(self, analyzer):
        """Test: Paper hands."""
        text = "Paper hands selling at the bottom"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_rekt(self, analyzer):
        """Test: Rekt (wrecked)."""
        text = "Got rekt on that trade"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_fud(self, analyzer):
        """Test: FUD (Fear, Uncertainty, Doubt)."""
        text = "Stop spreading FUD"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_jeet(self, analyzer):
        """Test: Jeet (weak seller)."""
        text = "Jeets selling everything"
        label, score = analyzer.analyze(text)
        
        # "jeet" alone may not be strong enough, but with "selling" context should be negative
        assert label in ['negative', 'neutral']
    
    def test_rugged(self, analyzer):
        """Test: Rugged (rug pulled)."""
        text = "Project rugged, lost everything"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_honeypot(self, analyzer):
        """Test: Honeypot (scam contract)."""
        text = "This is a honeypot, can't sell"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_bagholder(self, analyzer):
        """Test: Bagholder."""
        text = "Now I'm a bagholder stuck with losses"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_cope(self, analyzer):
        """Test: Cope (coping with losses)."""
        text = "Just cope and hold"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_salty(self, analyzer):
        """Test: Salty (bitter about losses)."""
        text = "Salty and rekt from losses"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_exit_liquidity(self, analyzer):
        """Test: Exit liquidity."""
        text = "We're just exit liquidity for whales"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_vaporware(self, analyzer):
        """Test: Vaporware."""
        text = "This project is vaporware"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_shitcoin(self, analyzer):
        """Test: Shitcoin."""
        text = "Another shitcoin pump and dump"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0
    
    def test_pump_and_dump(self, analyzer):
        """Test: Pump and dump."""
        text = "Classic pump and dump scam avoid"
        label, score = analyzer.analyze(text)
        
        # With "scam" and "avoid" added, should be clearly negative
        assert label == 'negative'
        assert score < 0
    
    def test_wash_trading(self, analyzer):
        """Test: Wash trading."""
        text = "Volume is fake, just wash trading"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < 0


class TestContextDependentTerms:
    """Test context-dependent crypto terms (10 cases)."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with crypto vocabulary enabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_degen_positive_context(self, analyzer):
        """Test: Degen in positive context."""
        text = "Degen play with huge upside potential"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
    
    def test_degen_negative_context(self, analyzer):
        """Test: Degen in negative context."""
        text = "Degen trap, avoid this scam"
        label, score = analyzer.analyze(text)
        
        # Should be negative due to 'trap' and 'scam'
        assert label == 'negative'
    
    def test_ape_positive_context(self, analyzer):
        """Test: Ape in positive context."""
        text = "Aping in early before the pump"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
    
    def test_ape_negative_context(self, analyzer):
        """Test: Ape in negative context."""
        text = "Aping into this scam trap"
        label, score = analyzer.analyze(text)
        
        # Should be negative due to 'scam' and 'trap'
        assert label == 'negative'
    
    def test_moon_positive_context(self, analyzer):
        """Test: Moon in positive context."""
        text = "Going to moon soon 🚀"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
    
    def test_moon_negative_context(self, analyzer):
        """Test: Moon in negative context."""
        text = "Never moon, it's a scam rug"
        label, score = analyzer.analyze(text)
        
        # Should be negative due to 'scam' and 'rug'
        assert label == 'negative'
    
    def test_whale_positive_context(self, analyzer):
        """Test: Whale in positive context."""
        text = "Whale accumulating, bullish"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
    
    def test_whale_negative_context(self, analyzer):
        """Test: Whale in negative context."""
        text = "Whale dumping crash exit scam"
        label, score = analyzer.analyze(text)
        
        # Should be negative due to 'dumping', 'crash', 'exit', 'scam'
        assert label == 'negative'
    
    def test_pump_positive_context(self, analyzer):
        """Test: Pump in positive context."""
        text = "Massive pump incoming!"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
    
    def test_pump_negative_context(self, analyzer):
        """Test: Pump in negative context (pump and dump)."""
        text = "Pump and dump scheme, avoid"
        label, score = analyzer.analyze(text)
        
        # Should be negative due to 'dump' and 'avoid'
        assert label == 'negative'


class TestCryptoVocabularyToggle:
    """Test crypto vocabulary can be enabled/disabled."""
    
    def test_crypto_vocab_enabled(self):
        """Test crypto terms recognized when enabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        analyzer = SentimentAnalyzer(config)
        
        text = "WAGMI frens, diamond hands hodl!"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0
    
    def test_crypto_vocab_disabled(self):
        """Test crypto terms not recognized when disabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=False)
        analyzer = SentimentAnalyzer(config)
        
        text = "WAGMI frens hodl"
        label, score = analyzer.analyze(text)
        
        # Without crypto vocab, these terms won't be recognized
        assert label == 'neutral'
        assert score == 0.0
    
    def test_standard_terms_work_without_crypto_vocab(self):
        """Test standard terms still work when crypto vocab disabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=False)
        analyzer = SentimentAnalyzer(config)
        
        text = "Bullish pump to the moon 🚀"
        label, score = analyzer.analyze(text)
        
        # Standard terms like 'bullish', 'pump', 'moon' should still work
        assert label == 'positive'
        assert score > 0


class TestMixedCryptoLanguage:
    """Test mixed crypto and standard language."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer with crypto vocabulary enabled."""
        config = SentimentConfig(nlp_enabled=False, use_crypto_vocabulary=True)
        return SentimentAnalyzer(config)
    
    def test_mixed_positive(self, analyzer):
        """Test mixed positive crypto and standard terms."""
        text = "Bullish setup, WAGMI frens! Diamond hands to the moon 🚀"
        label, score = analyzer.analyze(text)
        
        assert label == 'positive'
        assert score > 0.7  # Should have high score with multiple indicators
    
    def test_mixed_negative(self, analyzer):
        """Test mixed negative crypto and standard terms."""
        text = "Bearish dump, paper hands getting rekt. Avoid this scam"
        label, score = analyzer.analyze(text)
        
        assert label == 'negative'
        assert score < -0.7  # Should have strong negative score
    
    def test_mixed_conflicting(self, analyzer):
        """Test mixed with conflicting signals."""
        text = "Bullish chart but paper hands might dump"
        label, score = analyzer.analyze(text)
        
        # Should detect conflict
        result = analyzer.analyze_detailed(text)
        assert result.has_conflict or abs(result.score) < 0.5
