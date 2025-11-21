"""Parallel historical scraper with priority and concurrency control.

Based on verified patterns:
- asyncio.gather() for parallel execution (Python docs)
- asyncio.Semaphore for concurrency limiting (Python docs)
- Priority-based scraping (reputation-driven)
"""
import asyncio
from typing import List
from pathlib import Path

from config.historical_scraper_config import HistoricalScraperConfig
from infrastructure.telegram.telegram_monitor import TelegramMonitor
from infrastructure.scrapers.historical_scraper import HistoricalScraper
from utils.logger import setup_logger


class ParallelHistoricalScraper:
    """
    Parallel historical scraper with concurrency control.
    
    Features:
    - Scrapes multiple channels in parallel (faster startup)
    - Limits concurrent scraping (prevents resource exhaustion)
    - Priority-based scraping (high-reputation channels first)
    - Resume capability (tracks progress per channel)
    
    Based on verified patterns:
    - asyncio.gather() (Python official docs)
    - asyncio.Semaphore (Python official docs)
    """
    
    def __init__(
        self,
        config: HistoricalScraperConfig,
        telegram_monitor: TelegramMonitor,
        message_handler,
        reputation_engine,
        max_concurrent: int = 5,
        logger=None
    ):
        """
        Initialize parallel historical scraper.
        
        Args:
            config: Historical scraper configuration
            telegram_monitor: TelegramMonitor instance
            message_handler: Async function to handle each message
            reputation_engine: ReputationEngine for channel priority
            max_concurrent: Maximum concurrent scraping tasks
            logger: Optional logger instance
        """
        self.config = config
        self.telegram_monitor = telegram_monitor
        self.message_handler = message_handler
        self.reputation_engine = reputation_engine
        self.max_concurrent = max_concurrent
        self.logger = logger or setup_logger('ParallelHistoricalScraper')
        
        # Create base scraper for each channel
        self.base_scraper = HistoricalScraper(
            config,
            telegram_monitor,
            message_handler
        )
        
        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        self.logger.info(
            f"Parallel historical scraper initialized "
            f"(max_concurrent={max_concurrent})"
        )
    
    def get_channel_priority(self, channel_config) -> float:
        """
        Get priority for channel based on reputation.
        
        Higher reputation = higher priority (scraped first).
        
        Args:
            channel_config: Channel configuration object
            
        Returns:
            Priority value (higher = higher priority)
        """
        reputation = self.reputation_engine.get_reputation(channel_config.name)
        
        if reputation:
            # Use reputation score directly (0-100)
            # High reputation (100) -> high priority (100) -> scraped first
            priority = reputation.reputation_score
        else:
            # Unknown channel -> medium priority (50)
            priority = 50
        
        return priority
    
    async def scrape_channel_with_limit(self, channel_config) -> bool:
        """
        Scrape channel with semaphore limiting.
        
        FIXED: Issue #17 - Re-raises exceptions instead of swallowing them
        Preserves error information for better debugging.
        
        Args:
            channel_config: Channel configuration object
            
        Returns:
            True if scraping successful
            
        Raises:
            Exception: If scraping fails (caught by gather with return_exceptions=True)
        """
        async with self.semaphore:
            try:
                self.logger.info(
                    f"Starting scrape for {channel_config.name} "
                    f"(concurrent: {self.max_concurrent - self.semaphore._value}/{self.max_concurrent})"
                )
                
                result = await self.base_scraper.scrape_if_needed(channel_config)
                
                self.logger.info(
                    f"Completed scrape for {channel_config.name} "
                    f"(success={result})"
                )
                
                return result
                
            except asyncio.CancelledError:
                self.logger.info(f"Scraping cancelled for {channel_config.name}")
                raise  # Always propagate cancellation
            except Exception as e:
                # Log but re-raise to preserve error information
                self.logger.error(
                    f"Error scraping {channel_config.name}: {e}",
                    exc_info=True
                )
                # Re-raise instead of returning False
                raise
    
    async def scrape_all_channels(self, channels: List) -> dict:
        """
        Scrape all channels in parallel with priority ordering.
        
        Channels are sorted by reputation (high-rep channels scraped first).
        Concurrency is limited by semaphore.
        
        Args:
            channels: List of channel configuration objects
            
        Returns:
            Dictionary with scraping results
        """
        if not self.config.enabled:
            self.logger.info("Historical scraping disabled")
            return {'enabled': False}
        
        # Filter enabled channels
        enabled_channels = [c for c in channels if c.enabled]
        
        if not enabled_channels:
            self.logger.warning("No enabled channels to scrape")
            return {'enabled': True, 'total': 0, 'success': 0, 'failed': 0}
        
        # Sort channels by priority (high reputation first)
        sorted_channels = sorted(
            enabled_channels,
            key=lambda c: self.get_channel_priority(c),
            reverse=True  # High priority first
        )
        
        self.logger.info(
            f"Starting parallel scraping for {len(sorted_channels)} channels "
            f"(max_concurrent={self.max_concurrent})"
        )
        
        # Log priority order
        for i, channel in enumerate(sorted_channels[:5], 1):
            priority = self.get_channel_priority(channel)
            self.logger.info(f"  {i}. {channel.name} (priority={priority:.1f})")
        
        if len(sorted_channels) > 5:
            self.logger.info(f"  ... and {len(sorted_channels) - 5} more")
        
        # Scrape all channels in parallel (with semaphore limiting)
        try:
            results = await asyncio.gather(
                *[self.scrape_channel_with_limit(c) for c in sorted_channels],
                return_exceptions=True
            )
            
            # Categorize results with error details
            success_count = sum(1 for r in results if r is True)
            failed_count = sum(1 for r in results if r is False)
            exceptions = [r for r in results if isinstance(r, Exception)]
            
            # Log exception details
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    channel = sorted_channels[i]
                    self.logger.error(
                        f"Channel {channel.name} failed: {type(result).__name__}: {result}"
                    )
            
            self.logger.info(
                f"Parallel scraping complete: "
                f"{success_count} success, "
                f"{failed_count} failed, "
                f"{len(exceptions)} exceptions"
            )
            
            return {
                'enabled': True,
                'total': len(sorted_channels),
                'success': success_count,
                'failed': failed_count,
                'exceptions': len(exceptions),
                'exception_types': [type(e).__name__ for e in exceptions]
            }
            
        except asyncio.CancelledError:
            self.logger.info("Parallel scraping cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Parallel scraping error: {e}", exc_info=True)
            return {
                'enabled': True,
                'total': len(sorted_channels),
                'success': 0,
                'failed': len(sorted_channels),
                'error': str(e)
            }
