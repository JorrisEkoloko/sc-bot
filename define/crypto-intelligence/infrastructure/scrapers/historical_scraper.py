"""Automatic historical scraper for new channels."""
import json
import asyncio
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from enum import Enum

from config.historical_scraper_config import HistoricalScraperConfig
from infrastructure.telegram.telegram_monitor import TelegramMonitor
from domain.message_event import MessageEvent
from utils.logger import setup_logger


class ScrapingStatus(Enum):
    """Status of channel scraping."""
    PENDING = "pending"
    COMPLETED = "completed"
    EMPTY = "empty"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HistoricalScraper:
    """Automatic historical scraping for new channels on startup."""
    
    def __init__(
        self,
        config: HistoricalScraperConfig,
        telegram_monitor: TelegramMonitor,
        message_handler: Callable
    ):
        """
        Initialize historical scraper.
        
        Args:
            config: Historical scraper configuration
            telegram_monitor: TelegramMonitor instance
            message_handler: Async function to handle each message
        """
        self.config = config
        self.telegram_monitor = telegram_monitor
        self.message_handler = message_handler
        self.logger = setup_logger('HistoricalScraper')
        
        self.scraped_channels_file = Path(config.scraped_channels_file)
        self.scraped_channels = self._load_scraped_channels()
        
        self.logger.info(
            f"Historical scraper initialized "
            f"(enabled: {config.enabled}, limit: {config.message_limit})"
        )
    
    def _load_scraped_channels(self) -> set:
        """
        Load list of previously scraped channels.
        
        Returns:
            Set of channel IDs that have been successfully scraped
        """
        if not self.scraped_channels_file.exists():
            self.logger.info("No scraped channels file found, starting fresh")
            return set()
        
        try:
            with open(self.scraped_channels_file, 'r') as f:
                data = json.load(f)
                # Load channels with completed or empty status
                channels_data = data.get('channels', {})
                completed_channels = {
                    channel_id for channel_id, info in channels_data.items()
                    if info.get('status') in [ScrapingStatus.COMPLETED.value, ScrapingStatus.EMPTY.value]
                }
                self.logger.info(f"Loaded {len(completed_channels)} previously scraped channels")
                return completed_channels
        except Exception as e:
            self.logger.error(f"Error loading scraped channels: {e}")
            return set()
    
    def _save_channel_status(self, channel_id: str, status: ScrapingStatus, 
                            message_count: int = 0, error: Optional[str] = None):
        """
        Save channel scraping status to disk.
        
        Args:
            channel_id: Channel ID
            status: Scraping status
            message_count: Number of messages processed
            error: Error message if failed
        """
        try:
            # Create directory if needed
            self.scraped_channels_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing data
            channels_data = {}
            if self.scraped_channels_file.exists():
                try:
                    with open(self.scraped_channels_file, 'r') as f:
                        existing = json.load(f)
                        channels_data = existing.get('channels', {})
                except Exception:
                    pass
            
            # Update channel status
            channels_data[channel_id] = {
                'status': status.value,
                'last_attempt': datetime.now().isoformat(),
                'message_count': message_count,
                'error': error
            }
            
            # Save to file
            with open(self.scraped_channels_file, 'w') as f:
                json.dump({
                    'channels': channels_data,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            
            self.logger.debug(f"Saved status for channel {channel_id}: {status.value}")
        except Exception as e:
            self.logger.error(f"Error saving channel status: {e}")
    
    async def scrape_if_needed(self, channel_config) -> bool:
        """
        Scrape channel if not previously scraped.
        
        Args:
            channel_config: Channel configuration object
            
        Returns:
            True if scraping was performed or skipped successfully, False if failed
        """
        if not self.config.enabled:
            self.logger.debug("Historical scraping disabled")
            return True
        
        channel_id = channel_config.id
        channel_name = channel_config.name
        
        # Check if already scraped
        if channel_id in self.scraped_channels:
            self.logger.info(f"Channel {channel_name} already scraped, skipping")
            return True
        
        self.logger.info(
            f"Channel {channel_name} not scraped, "
            f"fetching {self.config.message_limit} historical messages"
        )
        
        try:
            # Fetch historical messages
            messages = await self._fetch_messages(channel_id, self.config.message_limit)
            
            if not messages:
                # Check if channel is accessible but empty vs fetch failed
                is_accessible = await self._is_channel_accessible(channel_id)
                if is_accessible:
                    self.logger.info(f"Channel {channel_name} is empty, marking as scraped")
                    self.scraped_channels.add(channel_id)
                    self._save_channel_status(channel_id, ScrapingStatus.EMPTY, 0)
                else:
                    self.logger.warning(f"Channel {channel_name} may be inaccessible, will retry next startup")
                    self._save_channel_status(channel_id, ScrapingStatus.FAILED, 0, "Channel inaccessible or no messages")
                return True
            
            # Process messages (may raise CancelledError)
            message_count = await self._process_messages(messages, channel_name)
            
            # Mark as scraped if processing completed successfully
            self.scraped_channels.add(channel_id)
            self._save_channel_status(channel_id, ScrapingStatus.COMPLETED, message_count)
            
            self.logger.info(f"Historical scraping complete for {channel_name}: {message_count} messages")
            return True
            
        except asyncio.CancelledError:
            # Don't mark as scraped if cancelled - allow retry on next startup
            self.logger.info(f"Historical scraping cancelled for {channel_name}, will retry on next startup")
            self._save_channel_status(channel_id, ScrapingStatus.CANCELLED, 0, "Scraping cancelled")
            raise  # Propagate cancellation
        except Exception as e:
            self.logger.error(f"Historical scraping failed for {channel_name}: {e}")
            self._save_channel_status(channel_id, ScrapingStatus.FAILED, 0, str(e))
            return False
    
    async def _is_channel_accessible(self, channel_id: str) -> bool:
        """
        Check if channel is accessible.
        
        Args:
            channel_id: Channel ID or username
            
        Returns:
            True if channel is accessible, False otherwise
        """
        try:
            await self.telegram_monitor.client.get_entity(channel_id)
            return True
        except Exception as e:
            self.logger.debug(f"Channel accessibility check failed: {e}")
            return False
    
    async def _fetch_messages(self, channel_id: str, limit: int) -> list:
        """
        Fetch historical messages from channel.
        
        Args:
            channel_id: Channel ID or username
            limit: Maximum number of messages to fetch
            
        Returns:
            List of messages
        """
        messages = []
        
        try:
            # Get the channel entity
            channel = await self.telegram_monitor.client.get_entity(channel_id)
            
            # Fetch messages
            async for message in self.telegram_monitor.client.iter_messages(
                channel,
                limit=limit
            ):
                if message.text:  # Only process text messages
                    messages.append(message)
            
            self.logger.info(f"Fetched {len(messages)} messages")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error fetching messages: {e}")
            return []
    
    async def _process_messages(self, messages: list, channel_name: str) -> int:
        """
        Process messages through the pipeline.
        
        Args:
            messages: List of Telegram messages
            channel_name: Name of the channel
            
        Returns:
            Number of messages successfully processed
        """
        total = len(messages)
        self.logger.info(f"Processing {total} historical messages")
        
        processed_count = 0
        for i, message in enumerate(messages, 1):
            try:
                # Log progress every 10 messages
                if i % 10 == 0:
                    self.logger.info(f"Processing historical message {i}/{total}")
                
                # Create message event
                event = MessageEvent(
                    channel_name=channel_name,
                    message_text=message.text,
                    timestamp=message.date,
                    message_id=message.id,
                    message_obj=message,
                    channel_id=str(message.peer_id.channel_id) 
                        if hasattr(message, 'peer_id') and hasattr(message.peer_id, 'channel_id') else "",
                    sender_id=str(message.sender_id) if hasattr(message, 'sender_id') else ""
                )
                
                # Process with timeout to prevent hanging
                try:
                    await asyncio.wait_for(
                        self.message_handler(event),
                        timeout=30.0  # 30 second timeout per message
                    )
                    processed_count += 1
                except asyncio.TimeoutError:
                    self.logger.error(f"Message {message.id} processing timed out after 30s")
                    # Continue with next message
                
            except asyncio.CancelledError:
                # Log cancellation at point of detection and propagate immediately
                self.logger.info(f"Cancellation detected at message {i}/{total}, processed {processed_count}/{total}")
                raise
            except Exception as e:
                self.logger.error(f"Error processing message {message.id}: {e}")
                # Continue processing other messages
        
        self.logger.info(f"Completed processing {processed_count}/{total} historical messages")
        return processed_count
