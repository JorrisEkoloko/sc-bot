"""Processing configuration for message analysis."""
import os
from dataclasses import dataclass


@dataclass
class ProcessingConfig:
    """Message processing configuration."""
    confidence_threshold: float = 0.7
    hdrb_max_ic: float = 1000.0
    min_message_length: int = 10
    max_processing_time_ms: float = 100.0
    
    # Timeout configurations for async operations (in seconds)
    historical_price_timeout: float = 30.0  # Timeout for historical price fetches
    ohlc_fetch_timeout: float = 20.0  # Timeout for OHLC data fetches
    
    @classmethod
    def load_from_env(cls) -> 'ProcessingConfig':
        """Load processing configuration from environment variables."""
        try:
            confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))
        except ValueError:
            confidence_threshold = 0.7
        
        try:
            hdrb_max_ic = float(os.getenv('HDRB_MAX_IC', '1000.0'))
        except ValueError:
            hdrb_max_ic = 1000.0
        
        try:
            min_message_length = int(os.getenv('MIN_MESSAGE_LENGTH', '10'))
        except ValueError:
            min_message_length = 10
        
        try:
            max_processing_time_ms = float(os.getenv('MAX_PROCESSING_TIME_MS', '100.0'))
        except ValueError:
            max_processing_time_ms = 100.0
        
        try:
            historical_price_timeout = float(os.getenv('HISTORICAL_PRICE_TIMEOUT', '30.0'))
        except ValueError:
            historical_price_timeout = 30.0
        
        try:
            ohlc_fetch_timeout = float(os.getenv('OHLC_FETCH_TIMEOUT', '20.0'))
        except ValueError:
            ohlc_fetch_timeout = 20.0
        
        return cls(
            confidence_threshold=confidence_threshold,
            hdrb_max_ic=hdrb_max_ic,
            min_message_length=min_message_length,
            max_processing_time_ms=max_processing_time_ms,
            historical_price_timeout=historical_price_timeout,
            ohlc_fetch_timeout=ohlc_fetch_timeout
        )
