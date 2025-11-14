"""Retry configuration for error handling."""
import os
from dataclasses import dataclass


@dataclass
class RetryConfig:
    """Error handler retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    @classmethod
    def load_from_env(cls) -> 'RetryConfig':
        """Load retry configuration from environment variables."""
        try:
            max_attempts = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
        except ValueError:
            max_attempts = 3
        
        try:
            base_delay = float(os.getenv('RETRY_BASE_DELAY', '1.0'))
        except ValueError:
            base_delay = 1.0
        
        try:
            exponential_base = float(os.getenv('RETRY_EXPONENTIAL_BASE', '2.0'))
        except ValueError:
            exponential_base = 2.0
        
        jitter_str = os.getenv('RETRY_JITTER', 'true').lower()
        jitter = jitter_str in ('true', '1', 'yes')
        
        return cls(
            max_attempts=max_attempts,
            base_delay=base_delay,
            exponential_base=exponential_base,
            jitter=jitter
        )
