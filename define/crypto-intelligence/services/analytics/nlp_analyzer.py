"""NLP-based sentiment analysis using transformer models."""

import re
import os
import time
import asyncio
from typing import Tuple, Callable, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from utils.logger import get_logger
from services.analytics.sentiment_config import SentimentConfig


class NLPAnalyzer:
    """
    NLP-based sentiment analyzer using transformer models.
    
    Uses pre-trained models from Hugging Face for advanced sentiment analysis
    with support for negation, sarcasm, and context understanding.
    """
    
    # Timeout for NLP inference (5 seconds)
    INFERENCE_TIMEOUT = 5.0
    
    def __init__(self, config: SentimentConfig):
        """
        Initialize NLP analyzer.
        
        Args:
            config: Sentiment configuration
        """
        self.logger = get_logger('NLPAnalyzer')
        self.config = config
        
        # Lazy loading - model loaded on first use
        self._model = None
        self._tokenizer = None
        self._device = None
        self._original_device = None
        
        # Thread pool for timeout handling
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # OOM tracking
        self._oom_count = 0
        self._max_oom_retries = 2
        
        self.logger.info(
            f"NLP analyzer initialized "
            f"(model: {config.nlp_model_name}, device: {config.nlp_device})"
        )
    

    
    def _detect_device(self) -> str:
        """Detect available device for inference."""
        if self.config.nlp_device == 'gpu':
            try:
                import torch
                if torch.cuda.is_available():
                    self.logger.info("GPU detected and available")
                    return 'cuda'
                else:
                    self.logger.warning("GPU requested but not available, falling back to CPU")
                    return 'cpu'
            except ImportError:
                self.logger.warning("PyTorch not available, falling back to CPU")
                return 'cpu'
        
        return 'cpu'
    
    def _clear_model_cache(self) -> None:
        """Clear model cache to free memory."""
        try:
            import torch
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                self.logger.info("Cleared CUDA cache")
            
            import gc
            gc.collect()
            self.logger.info("Forced garbage collection")
            
        except Exception as e:
            self.logger.warning(f"Failed to clear model cache: {e}")
    
    def _handle_oom_error(self, error: Exception) -> bool:
        """
        Handle out-of-memory errors with recovery strategies.
        
        Returns:
            True if recovery was attempted and should retry, False if should give up
        """
        self._oom_count += 1
        
        self.logger.error(
            f"Out of memory error detected (attempt {self._oom_count}/{self._max_oom_retries}): "
            f"{str(error)[:100]}"
        )
        
        # Strategy 1: Clear cache and retry
        if self._oom_count == 1:
            self.logger.info("OOM recovery strategy 1: Clearing model cache and retrying")
            self._clear_model_cache()
            return True
        
        # Strategy 2: Reload model on CPU if on GPU (safe - avoids race conditions)
        if self._oom_count == 2 and self._device == 'cuda':
            self.logger.warning("OOM recovery strategy 2: Reloading model on CPU")
            
            try:
                import torch
                
                # Clear existing model first (thread-safe)
                self._model = None
                self._tokenizer = None
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Force CPU device for next load
                self._device = 'cpu'
                self.logger.info("Model cleared, will reload on CPU on next inference")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to prepare CPU reload: {e}")
                return False
        
        # Strategy 3: Give up
        self.logger.error(
            f"OOM recovery failed after {self._oom_count} attempts. "
            "Falling back to pattern-only mode."
        )
        return False
    
    def _is_oom_error(self, error: Exception) -> bool:
        """Check if an error is an out-of-memory error."""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in [
            'out of memory',
            'oom',
            'cuda out of memory',
            'memory error',
            'allocation failed'
        ])
    
    def _load_model(self) -> bool:
        """
        Load transformer model and tokenizer.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if self._model is not None:
            return True
        
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
        except ImportError as e:
            self.logger.error(
                f"Failed to import transformers library: {e}. "
                "Install with: pip install transformers torch. "
                "Falling back to pattern-only mode."
            )
            return False
        
        self._device = self._detect_device()
        
        try:
            os.makedirs(self.config.model_cache_dir, exist_ok=True)
        except Exception as e:
            self.logger.error(
                f"Failed to create model cache directory {self.config.model_cache_dir}: {e}. "
                "Falling back to pattern-only mode."
            )
            return False
        
        max_retries = 1
        retry_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(
                        f"Retrying model load (attempt {attempt + 1}/{max_retries + 1}) "
                        f"after {retry_delay}s delay..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.info(f"Loading NLP model: {self.config.nlp_model_name}")
                
                self.logger.debug("Loading tokenizer...")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.config.nlp_model_name,
                    cache_dir=self.config.model_cache_dir
                )
                
                self.logger.debug("Loading model...")
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    self.config.nlp_model_name,
                    cache_dir=self.config.model_cache_dir
                )
                
                self._model.to(self._device)
                self._model.eval()
                
                self.logger.info(
                    f"NLP model loaded successfully "
                    f"(device: {self._device}, cache: {self.config.model_cache_dir})"
                )
                
                return True
                
            except Exception as e:
                error_type = type(e).__name__
                self.logger.error(
                    f"Failed to load NLP model (attempt {attempt + 1}/{max_retries + 1}): "
                    f"{error_type}: {str(e)[:200]}"
                )
                
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    self.logger.error(
                        "Network error detected. Check internet connection and "
                        "Hugging Face Hub availability."
                    )
                elif "disk" in str(e).lower() or "space" in str(e).lower():
                    self.logger.error(
                        f"Disk space issue detected. Check available space in "
                        f"{self.config.model_cache_dir}"
                    )
                elif "permission" in str(e).lower():
                    self.logger.error(
                        f"Permission error. Check write permissions for "
                        f"{self.config.model_cache_dir}"
                    )
                
                if attempt == max_retries:
                    self.logger.error(
                        f"All {max_retries + 1} attempts to load NLP model failed. "
                        "Falling back to pattern-only mode."
                    )
                    return False
        
        return False
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for NLP inference."""
        # Replace @mentions
        text = re.sub(r'@\w+', '@user', text)
        
        # Replace URLs
        text = re.sub(r'https?://\S+', 'http', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if too long
        max_chars = self.config.max_text_length * 4
        if len(text) > max_chars:
            text = text[:max_chars]
            self.logger.debug(f"Text truncated to {max_chars} characters")
        
        return text
    
    def _analyze_internal(self, text: str) -> Tuple[str, float]:
        """Internal method to perform NLP inference without timeout wrapper."""
        import torch
        
        processed_text = self._preprocess_text(text)
        
        try:
            inputs = self._tokenizer(
                processed_text,
                return_tensors='pt',
                truncation=True,
                max_length=self.config.max_text_length,
                padding=True
            )
        except Exception as e:
            truncated_text = text[:100] + "..." if len(text) > 100 else text
            self.logger.error(
                f"Tokenization failed: {type(e).__name__}: {str(e)[:100]}. "
                f"Input text (truncated): '{truncated_text}'"
            )
            raise RuntimeError(f"Tokenization failed: {e}") from e
        
        try:
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
        except Exception as e:
            if self._is_oom_error(e):
                self.logger.error(f"OOM error during device transfer: {str(e)[:100]}")
                raise MemoryError(f"OOM during device transfer: {e}") from e
            
            self.logger.error(
                f"Failed to move inputs to device {self._device}: "
                f"{type(e).__name__}: {str(e)[:100]}"
            )
            raise RuntimeError(f"Device transfer failed: {e}") from e
        
        try:
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
        except RuntimeError as e:
            if self._is_oom_error(e):
                self.logger.error(f"OOM error during inference: {str(e)[:100]}")
                raise MemoryError(f"OOM during inference: {e}") from e
            elif "cuda" in str(e).lower():
                self.logger.error(f"CUDA error during inference: {str(e)[:100]}")
                raise RuntimeError(f"CUDA error: {e}") from e
            else:
                truncated_text = text[:100] + "..." if len(text) > 100 else text
                self.logger.error(
                    f"Model inference failed: {type(e).__name__}: {str(e)[:100]}. "
                    f"Input text (truncated): '{truncated_text}'"
                )
                raise RuntimeError(f"Inference failed: {e}") from e
        except Exception as e:
            truncated_text = text[:100] + "..." if len(text) > 100 else text
            self.logger.error(
                f"Unexpected inference error: {type(e).__name__}: {str(e)[:100]}. "
                f"Input text (truncated): '{truncated_text}'"
            )
            raise RuntimeError(f"Inference failed: {e}") from e
        
        try:
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
            
            label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
            sentiment_label = label_map.get(predicted_class, 'neutral')
            
            if sentiment_label == 'positive':
                sentiment_score = confidence
            elif sentiment_label == 'negative':
                sentiment_score = -confidence
            else:
                sentiment_score = 0.0
            
            self.logger.debug(
                f"NLP analysis: {sentiment_label} "
                f"(score: {sentiment_score:+.2f}, confidence: {confidence:.2f})"
            )
            
            if self._oom_count > 0:
                self.logger.info(
                    f"Inference successful after {self._oom_count} OOM recovery attempts"
                )
                self._oom_count = 0
            
            return (sentiment_label, sentiment_score, confidence)
            
        except Exception as e:
            self.logger.error(
                f"Failed to process model output: {type(e).__name__}: {str(e)[:100]}"
            )
            raise RuntimeError(f"Output processing failed: {e}") from e
    

    def analyze(self, text: str) -> Tuple[str, float, float]:
        """
        Analyze sentiment using NLP model (synchronous version with timeout).
        
        This runs inference in the ThreadPoolExecutor with timeout protection
        to avoid blocking the event loop.
        
        Args:
            text: Message text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score, confidence)
            
        Raises:
            RuntimeError: If model is not available or inference fails
        """
        if not text:
            return ('neutral', 0.0, 0.0)
        
        if not self._load_model():
            self.logger.warning("Model not available, cannot perform NLP analysis")
            raise RuntimeError("NLP model not available")
        
        if self._original_device is None:
            self._original_device = self._device
        
        max_attempts = self._max_oom_retries + 1
        for attempt in range(max_attempts):
            start_time = time.time()
            
            try:
                # Run inference in thread pool with timeout protection
                future = self._executor.submit(self._analyze_internal, text)
                try:
                    result = future.result(timeout=self.INFERENCE_TIMEOUT)
                except FuturesTimeoutError:
                    self.logger.error(
                        f"NLP inference timeout after {self.INFERENCE_TIMEOUT}s. "
                        f"Text length: {len(text)} chars"
                    )
                    raise RuntimeError(f"NLP inference timeout after {self.INFERENCE_TIMEOUT}s")
                
                inference_time_ms = (time.time() - start_time) * 1000
                if inference_time_ms > 200:
                    self.logger.warning(
                        f"Slow NLP inference: {inference_time_ms:.1f}ms > 200ms threshold"
                    )
                
                return result
            
            except MemoryError as e:
                # Handle OOM errors FIRST (before any transformation)
                if not self._handle_oom_error(e):
                    self.logger.error("OOM recovery failed. Falling back to pattern-only mode.")
                    raise RuntimeError(f"Out of memory: {e}") from e
                
                self.logger.info(f"Retrying inference after OOM recovery (attempt {attempt + 2}/{max_attempts})")
                continue
                
            except RuntimeError as e:
                # Re-raise RuntimeError without transformation, but check if it's from OOM
                if "Out of memory" in str(e):
                    raise  # Re-raise OOM-derived errors as-is
                raise
                
            except Exception as e:
                # Catch truly unexpected errors
                truncated_text = text[:100] + "..." if len(text) > 100 else text
                self.logger.error(
                    f"Unexpected error in NLP analysis: {type(e).__name__}: {str(e)[:100]}. "
                    f"Input text (truncated): '{truncated_text}'"
                )
                raise RuntimeError(f"NLP analysis failed: {e}") from e
        
        self.logger.error("Max OOM retry attempts exceeded")
        raise RuntimeError("Max OOM retry attempts exceeded")
    
    def analyze_batch(self, texts: list[str]) -> list[Tuple[str, float]]:
        """
        Analyze sentiment for multiple texts in batch.
        
        Args:
            texts: List of message texts to analyze
            
        Returns:
            List of tuples (sentiment_label, sentiment_score) for each text
            
        Raises:
            RuntimeError: If model is not available or inference fails
        """
        if not texts:
            return []
        
        if not self._load_model():
            self.logger.warning("Model not available, cannot perform NLP analysis")
            raise RuntimeError("NLP model not available")
        
        try:
            import torch
            
            try:
                processed_texts = [self._preprocess_text(text) for text in texts]
            except Exception as e:
                self.logger.error(
                    f"Text preprocessing failed in batch: {type(e).__name__}: {str(e)[:100]}"
                )
                raise RuntimeError(f"Batch preprocessing failed: {e}") from e
            
            try:
                inputs = self._tokenizer(
                    processed_texts,
                    return_tensors='pt',
                    truncation=True,
                    max_length=self.config.max_text_length,
                    padding=True
                )
            except Exception as e:
                self.logger.error(
                    f"Batch tokenization failed: {type(e).__name__}: {str(e)[:100]}. "
                    f"Batch size: {len(texts)}"
                )
                raise RuntimeError(f"Batch tokenization failed: {e}") from e
            
            try:
                inputs = {k: v.to(self._device) for k, v in inputs.items()}
            except Exception as e:
                self.logger.error(
                    f"Failed to move batch inputs to device {self._device}: "
                    f"{type(e).__name__}: {str(e)[:100]}"
                )
                raise RuntimeError(f"Batch device transfer failed: {e}") from e
            
            try:
                with torch.no_grad():
                    outputs = self._model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=1)
            except RuntimeError as e:
                if self._is_oom_error(e):
                    self.logger.error(
                        f"OOM error during batch inference: {str(e)[:100]}. "
                        f"Batch size: {len(texts)}"
                    )
                    raise MemoryError(f"OOM during batch inference: {e}") from e
                elif "cuda" in str(e).lower():
                    self.logger.error(
                        f"CUDA error during batch inference: {str(e)[:100]}. "
                        f"Batch size: {len(texts)}"
                    )
                    raise RuntimeError(f"CUDA error: {e}") from e
                else:
                    self.logger.error(
                        f"Batch inference failed: {type(e).__name__}: {str(e)[:100]}. "
                        f"Batch size: {len(texts)}"
                    )
                    raise RuntimeError(f"Batch inference failed: {e}") from e
            except Exception as e:
                self.logger.error(
                    f"Unexpected batch inference error: {type(e).__name__}: {str(e)[:100]}. "
                    f"Batch size: {len(texts)}"
                )
                raise RuntimeError(f"Batch inference failed: {e}") from e
            
            try:
                results = []
                label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
                
                for i in range(len(texts)):
                    predicted_class = torch.argmax(probabilities[i]).item()
                    confidence = probabilities[i][predicted_class].item()
                    
                    sentiment_label = label_map.get(predicted_class, 'neutral')
                    
                    if sentiment_label == 'positive':
                        sentiment_score = confidence
                    elif sentiment_label == 'negative':
                        sentiment_score = -confidence
                    else:
                        sentiment_score = 0.0
                    
                    results.append((sentiment_label, sentiment_score))
                
                self.logger.debug(f"Batch NLP analysis completed for {len(texts)} texts")
                
                return results
                
            except Exception as e:
                self.logger.error(
                    f"Failed to process batch output: {type(e).__name__}: {str(e)[:100]}"
                )
                raise RuntimeError(f"Batch output processing failed: {e}") from e
        
        except RuntimeError:
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error in batch NLP analysis: {type(e).__name__}: {str(e)[:100]}. "
                f"Batch size: {len(texts)}"
            )
            raise RuntimeError(f"Batch NLP analysis failed: {e}") from e
