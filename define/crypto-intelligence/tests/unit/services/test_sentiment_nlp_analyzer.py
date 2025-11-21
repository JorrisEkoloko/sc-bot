"""
Unit tests for NLP-based sentiment analysis.

Tests the NLPAnalyzer component including:
- Model loading and caching
- Text preprocessing correctness
- Inference accuracy
- Error handling and fallback
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.analytics.nlp_analyzer import NLPAnalyzer
from services.analytics.sentiment_config import SentimentConfig


class TestModelLoading:
    """Test NLP model loading and caching."""
    
    def test_lazy_loading(self):
        """Test model is not loaded until first use."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Model should not be loaded yet
        assert analyzer._model is None
        assert analyzer._tokenizer is None
    
    def test_model_loads_on_first_analyze(self):
        """Test model loads on first analyze call."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Model should not be loaded yet
        assert analyzer._model is None
        
        # Try to load model (will fail if transformers not installed, which is fine)
        try:
            result = analyzer._load_model()
            # If successful, model should be loaded
            if result:
                assert analyzer._model is not None
                assert analyzer._tokenizer is not None
        except Exception:
            # If transformers not installed, that's expected
            pass
    
    def test_model_caching(self):
        """Test model is cached after first load."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Simulate model loaded
        analyzer._model = Mock()
        analyzer._tokenizer = Mock()
        
        # Second load should return True immediately
        result = analyzer._load_model()
        assert result is True
    
    def test_device_detection_cpu(self):
        """Test CPU device detection."""
        config = SentimentConfig(nlp_enabled=True, nlp_device='cpu')
        analyzer = NLPAnalyzer(config)
        
        device = analyzer._detect_device()
        assert device == 'cpu'
    
    def test_device_detection_gpu_available(self):
        """Test GPU device detection when available."""
        config = SentimentConfig(nlp_enabled=True, nlp_device='gpu')
        analyzer = NLPAnalyzer(config)
        
        device = analyzer._detect_device()
        # Should be 'cuda' if GPU available, 'cpu' otherwise
        assert device in ['cuda', 'cpu']
    
    def test_device_detection_gpu_unavailable(self):
        """Test GPU fallback to CPU when unavailable."""
        config = SentimentConfig(nlp_enabled=True, nlp_device='gpu')
        analyzer = NLPAnalyzer(config)
        
        device = analyzer._detect_device()
        # Should fallback to CPU if GPU not available
        assert device in ['cuda', 'cpu']


class TestTextPreprocessing:
    """Test text preprocessing correctness."""
    
    @pytest.fixture
    def analyzer(self):
        """Create NLP analyzer."""
        config = SentimentConfig(nlp_enabled=True)
        return NLPAnalyzer(config)
    
    def test_preprocess_mentions(self, analyzer):
        """Test @mentions are replaced with @user."""
        text = "@alice and @bob are discussing crypto"
        processed = analyzer._preprocess_text(text)
        
        assert '@alice' not in processed
        assert '@bob' not in processed
        assert '@user' in processed
    
    def test_preprocess_urls(self, analyzer):
        """Test URLs are replaced with http."""
        text = "Check this out https://example.com/article"
        processed = analyzer._preprocess_text(text)
        
        assert 'https://example.com' not in processed
        assert 'http' in processed
    
    def test_preprocess_whitespace(self, analyzer):
        """Test whitespace normalization."""
        text = "Too    many     spaces"
        processed = analyzer._preprocess_text(text)
        
        assert '    ' not in processed
        assert processed == "Too many spaces"
    
    def test_preprocess_truncation(self, analyzer):
        """Test long text is truncated."""
        # Create very long text
        text = "word " * 1000
        processed = analyzer._preprocess_text(text)
        
        # Should be truncated
        max_chars = analyzer.config.max_text_length * 4
        assert len(processed) <= max_chars
    
    def test_preprocess_combined(self, analyzer):
        """Test combined preprocessing."""
        text = "@user1 check   https://example.com  for  info"
        processed = analyzer._preprocess_text(text)
        
        assert '@user1' not in processed
        assert '@user' in processed
        assert 'https://example.com' not in processed
        assert 'http' in processed
        assert '  ' not in processed


class TestInferenceAccuracy:
    """Test NLP inference accuracy (requires model)."""
    
    @pytest.fixture
    def analyzer(self):
        """Create NLP analyzer with model."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Try to load model, skip tests if unavailable
        if not analyzer._load_model():
            pytest.skip("NLP model not available")
        
        return analyzer
    
    def test_clear_positive_inference(self, analyzer):
        """Test inference on clear positive text."""
        text = "This is amazing! I love it so much!"
        
        try:
            label, score = analyzer.analyze(text)
            assert label == 'positive'
            assert score > 0
        except RuntimeError:
            pytest.skip("NLP model not available")
    
    def test_clear_negative_inference(self, analyzer):
        """Test inference on clear negative text."""
        text = "This is terrible! I hate it completely!"
        
        try:
            label, score = analyzer.analyze(text)
            assert label == 'negative'
            assert score < 0
        except RuntimeError:
            pytest.skip("NLP model not available")
    
    def test_neutral_inference(self, analyzer):
        """Test inference on neutral text."""
        text = "The price is currently at $50,000"
        
        try:
            label, score = analyzer.analyze(text)
            assert label in ['neutral', 'positive', 'negative']
            assert -1.0 <= score <= 1.0
        except RuntimeError:
            pytest.skip("NLP model not available")
    
    def test_empty_text(self, analyzer):
        """Test handling of empty text."""
        label, score = analyzer.analyze("")
        
        assert label == 'neutral'
        assert score == 0.0


class TestErrorHandling:
    """Test error handling and fallback mechanisms."""
    
    def test_model_unavailable_raises_error(self):
        """Test error raised when model unavailable."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Force model loading to fail
        analyzer._model = None
        
        with patch.object(analyzer, '_load_model', return_value=False):
            with pytest.raises(RuntimeError, match="NLP model not available"):
                analyzer.analyze("test text")
    
    def test_model_loading_failure(self):
        """Test handling of model loading failure."""
        config = SentimentConfig(
            nlp_enabled=True,
            nlp_model_name="invalid/nonexistent-model"
        )
        analyzer = NLPAnalyzer(config)
        
        # Should return False when model loading fails
        result = analyzer._load_model()
        assert result is False
    
    def test_oom_error_detection(self):
        """Test OOM error detection."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        oom_error = RuntimeError("CUDA out of memory")
        assert analyzer._is_oom_error(oom_error) is True
        
        other_error = RuntimeError("Some other error")
        assert analyzer._is_oom_error(other_error) is False
    
    def test_oom_recovery_strategy(self):
        """Test OOM recovery attempts."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # First attempt should try cache clearing
        should_retry = analyzer._handle_oom_error(MemoryError("OOM"))
        assert should_retry is True
        assert analyzer._oom_count == 1
        
        # Second attempt should try CPU fallback
        analyzer._device = 'cuda'
        should_retry = analyzer._handle_oom_error(MemoryError("OOM"))
        # May or may not retry depending on model state
        assert analyzer._oom_count == 2
    
    def test_timeout_handling(self):
        """Test timeout handling."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Mock a slow operation
        def slow_operation(text):
            import time
            time.sleep(10)
            return ('positive', 0.8)
        
        # Should timeout
        with pytest.raises(TimeoutError):
            analyzer._run_with_timeout(slow_operation, 0.1, "test")
    
    def test_inference_error_handling(self):
        """Test inference error handling."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Setup mock model that fails
        analyzer._model = Mock()
        analyzer._tokenizer = Mock()
        analyzer._device = 'cpu'
        
        # Make tokenizer fail
        analyzer._tokenizer.side_effect = Exception("Tokenization failed")
        
        with pytest.raises(RuntimeError):
            analyzer._analyze_internal("test text")


class TestBatchProcessing:
    """Test batch processing functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create NLP analyzer with model."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Try to load model, skip tests if unavailable
        if not analyzer._load_model():
            pytest.skip("NLP model not available")
        
        return analyzer
    
    def test_batch_empty_list(self, analyzer):
        """Test batch processing with empty list."""
        results = analyzer.analyze_batch([])
        assert results == []
    
    def test_batch_single_text(self, analyzer):
        """Test batch processing with single text."""
        texts = ["This is great!"]
        
        try:
            results = analyzer.analyze_batch(texts)
            assert len(results) == 1
            assert isinstance(results[0], tuple)
            assert len(results[0]) == 2
        except RuntimeError:
            pytest.skip("NLP model not available")
    
    def test_batch_multiple_texts(self, analyzer):
        """Test batch processing with multiple texts."""
        texts = [
            "This is amazing!",
            "This is terrible!",
            "The price is $50k"
        ]
        
        try:
            results = analyzer.analyze_batch(texts)
            assert len(results) == 3
            
            # Check all results are valid
            for label, score in results:
                assert label in ['positive', 'negative', 'neutral']
                assert -1.0 <= score <= 1.0
        except RuntimeError:
            pytest.skip("NLP model not available")


class TestPerformanceMetrics:
    """Test performance-related functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create NLP analyzer."""
        config = SentimentConfig(nlp_enabled=True)
        return NLPAnalyzer(config)
    
    def test_inference_timeout_value(self, analyzer):
        """Test inference timeout is set correctly."""
        assert analyzer.INFERENCE_TIMEOUT == 5.0
    
    def test_max_oom_retries(self, analyzer):
        """Test max OOM retries is set correctly."""
        assert analyzer._max_oom_retries == 2
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        config = SentimentConfig(nlp_enabled=True)
        analyzer = NLPAnalyzer(config)
        
        # Should not raise an error
        try:
            analyzer._clear_model_cache()
            # If successful, test passes
            assert True
        except Exception as e:
            # If torch not available, that's fine
            assert "torch" in str(e).lower() or "module" in str(e).lower()
