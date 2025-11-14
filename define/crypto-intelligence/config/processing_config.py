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
        
        return cls(
            confidence_threshold=confidence_threshold,
            hdrb_max_ic=hdrb_max_ic,
            min_message_length=min_message_length,
            max_processing_time_ms=max_processing_time_ms
        )
