"""Configuration for sentiment analysis."""

import os
from dataclasses import dataclass


@dataclass
class SentimentConfig:
    """Configuration for sentiment analyzer."""
    
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
    stats_log_frequency: int = 100  # Log stats every N messages
    
    # Fallback settings
    fallback_to_pattern: bool = True
    retry_on_error: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ValueError: If any configuration parameter is invalid
        """
        # Validate model name format (should be org/model or model)
        if not self.nlp_model_name or not isinstance(self.nlp_model_name, str):
            raise ValueError("nlp_model_name must be a non-empty string")
        
        # Validate device selection
        if self.nlp_device not in ['cpu', 'gpu', 'cuda']:
            raise ValueError(f"nlp_device must be 'cpu' or 'gpu', got: {self.nlp_device}")
        
        # Normalize 'cuda' to 'gpu'
        if self.nlp_device == 'cuda':
            self.nlp_device = 'gpu'
        
        # Validate threshold ranges (0.0-1.0)
        if not 0.0 <= self.nlp_confidence_threshold <= 1.0:
            raise ValueError(
                f"nlp_confidence_threshold must be between 0.0 and 1.0, "
                f"got: {self.nlp_confidence_threshold}"
            )
        
        if not 0.0 <= self.pattern_confidence_threshold <= 1.0:
            raise ValueError(
                f"pattern_confidence_threshold must be between 0.0 and 1.0, "
                f"got: {self.pattern_confidence_threshold}"
            )
        
        # Validate batch size
        if self.nlp_batch_size < 1:
            raise ValueError(f"nlp_batch_size must be >= 1, got: {self.nlp_batch_size}")
        
        # Validate stats log frequency
        if self.stats_log_frequency < 1:
            raise ValueError(f"stats_log_frequency must be >= 1, got: {self.stats_log_frequency}")
        
        # Validate max text length
        if self.max_text_length < 1 or self.max_text_length > 512:
            raise ValueError(
                f"max_text_length must be between 1 and 512, "
                f"got: {self.max_text_length}"
            )
        
        # Validate model cache directory
        if not self.model_cache_dir or not isinstance(self.model_cache_dir, str):
            raise ValueError("model_cache_dir must be a non-empty string")
    
    @classmethod
    def from_env(cls) -> 'SentimentConfig':
        """
        Load configuration from environment variables.
        
        Reads sentiment configuration from environment variables with fallback
        to sensible defaults. Validates all parameters after loading.
        
        Environment Variables:
            SENTIMENT_NLP_ENABLED: Enable/disable NLP enhancement (default: true)
            SENTIMENT_NLP_MODEL: Model name from Hugging Face (default: cardiffnlp/twitter-roberta-base-sentiment-latest)
            SENTIMENT_NLP_DEVICE: Device for inference - 'cpu' or 'gpu' (default: cpu)
            SENTIMENT_NLP_CONFIDENCE_THRESHOLD: Threshold for NLP invocation (default: 0.7)
            SENTIMENT_PATTERN_CONFIDENCE_THRESHOLD: Threshold for pattern confidence (default: 0.7)
            SENTIMENT_USE_CRYPTO_VOCABULARY: Enable crypto-specific vocabulary (default: true)
            SENTIMENT_MODEL_CACHE_DIR: Directory for model cache (default: models/sentiment)
            SENTIMENT_FALLBACK_TO_PATTERN: Enable fallback to pattern on NLP failure (default: true)
            SENTIMENT_STATS_LOG_FREQUENCY: Log statistics every N messages (default: 100)
        
        Returns:
            SentimentConfig instance with validated parameters
            
        Raises:
            ValueError: If any configuration parameter is invalid
        """
        try:
            config = cls(
                nlp_enabled=os.getenv('SENTIMENT_NLP_ENABLED', 'true').lower() == 'true',
                nlp_model_name=os.getenv('SENTIMENT_NLP_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment-latest'),
                nlp_device=os.getenv('SENTIMENT_NLP_DEVICE', 'cpu').lower(),
                nlp_confidence_threshold=float(os.getenv('SENTIMENT_NLP_CONFIDENCE_THRESHOLD', '0.7')),
                pattern_confidence_threshold=float(os.getenv('SENTIMENT_PATTERN_CONFIDENCE_THRESHOLD', '0.7')),
                use_crypto_vocabulary=os.getenv('SENTIMENT_USE_CRYPTO_VOCABULARY', 'true').lower() == 'true',
                model_cache_dir=os.getenv('SENTIMENT_MODEL_CACHE_DIR', 'models/sentiment'),
                fallback_to_pattern=os.getenv('SENTIMENT_FALLBACK_TO_PATTERN', 'true').lower() == 'true',
                stats_log_frequency=int(os.getenv('SENTIMENT_STATS_LOG_FREQUENCY', '100'))
            )
            return config
        except ValueError as e:
            # Re-raise validation errors with context
            raise ValueError(f"Invalid sentiment configuration: {e}") from e
        except Exception as e:
            # Catch parsing errors (e.g., invalid float values)
            raise ValueError(f"Error loading sentiment configuration from environment: {e}") from e
