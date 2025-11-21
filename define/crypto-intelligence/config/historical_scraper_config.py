"""Configuration for automatic historical scraper."""
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class HistoricalScraperConfig:
    """Configuration for automatic historical scraping on startup."""
    
    enabled: bool = True
    message_limit: int = 0  # 0 = unlimited, fetch ALL messages (complete history)
    scraped_channels_file: str = "data/scraped_channels.json"
    
    @classmethod
    def load_from_env(cls) -> 'HistoricalScraperConfig':
        """
        Load configuration from environment variables.
        
        Returns:
            HistoricalScraperConfig instance
        """
        return cls(
            enabled=os.getenv('HISTORICAL_SCRAPER_ENABLED', 'true').lower() == 'true',
            message_limit=int(os.getenv('HISTORICAL_SCRAPER_MESSAGE_LIMIT', '0')),  # 0 = unlimited
            scraped_channels_file=os.getenv(
                'HISTORICAL_SCRAPER_SCRAPED_CHANNELS_FILE',
                'data/scraped_channels.json'
            )
        )
