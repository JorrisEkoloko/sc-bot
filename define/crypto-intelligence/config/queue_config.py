"""Configuration for priority message queue."""
from dataclasses import dataclass
import os


@dataclass
class QueueConfig:
    """Configuration for priority message queue."""
    
    # Queue settings
    max_queue_size: int = 5000  # Maximum messages in queue (increased for ALL messages)
    messages_per_second: float = 2.0  # Global rate limit (2 msg/s = 120 msg/min)
    
    # Parallel scraping settings
    max_concurrent_scraping: int = 10  # Max channels to scrape in parallel (increased for speed)
    
    @classmethod
    def load_from_env(cls) -> 'QueueConfig':
        """
        Load configuration from environment variables.
        
        Returns:
            QueueConfig instance
        """
        return cls(
            max_queue_size=int(os.getenv('QUEUE_MAX_SIZE', '5000')),
            messages_per_second=float(os.getenv('QUEUE_MESSAGES_PER_SECOND', '2.0')),
            max_concurrent_scraping=int(os.getenv('PARALLEL_SCRAPER_MAX_CONCURRENT', '10'))
        )
