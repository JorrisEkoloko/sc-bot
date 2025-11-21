"""Automatic historical scraper for new channels (refactored)."""
import asyncio
from typing import Callable

from config.historical_scraper_config import HistoricalScraperConfig
from infrastructure.telegram.telegram_monitor import TelegramMonitor
from infrastructure.scrapers.scraping_progress_tracker import ScrapingProgressTracker, ScrapingStatus
from infrastructure.scrapers.message_fetcher import MessageFetcher
from infrastructure.scrapers.message_processor_coordinator import MessageProcessorCoordinator
from utils.logger import setup_logger


class HistoricalScraper:
    """
    Automatic historical scraping for new channels on startup.
    
    Refactored to use specialized components:
    - ScrapingProgressTracker: Manages scraping status
    - MessageFetcher: Fetches messages from Telegram
    - MessageProcessorCoordinator: Processes messages through pipeline
    """
    
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
        self.logger = setup_logger('HistoricalScraper')
        
        # Initialize specialized components
        self.progress_tracker = ScrapingProgressTracker(
            scraped_channels_file=config.scraped_channels_file,
            logger=self.logger
        )
        
        self.message_fetcher = MessageFetcher(
            telegram_monitor=telegram_monitor,
            logger=self.logger
        )
        
        self.message_processor = MessageProcessorCoordinator(
            message_handler=message_handler,
            rate_limit_delay=0.5,  # 0.5s between messages
            logger=self.logger
        )
        
        self.logger.info(
            f"Historical scraper initialized with refactored architecture "
            f"(enabled: {config.enabled}, limit: {config.message_limit})"
        )
    

    
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
        if self.progress_tracker.is_channel_scraped(channel_id):
            self.logger.info(f"Channel {channel_name} already scraped, skipping")
            return True
        
        self.logger.info(
            f"Channel {channel_name} not scraped, "
            f"fetching {self.config.message_limit} historical messages"
        )
        
        try:
            # Fetch historical messages using MessageFetcher
            messages = await self.message_fetcher.fetch_messages(
                channel_id,
                self.config.message_limit
            )
            
            if not messages:
                # Check if channel is accessible but empty vs fetch failed
                is_accessible = await self.message_fetcher.is_channel_accessible(channel_id)
                if is_accessible:
                    self.logger.info(f"Channel {channel_name} is empty, marking as scraped")
                    self.progress_tracker.mark_channel_completed(channel_id, 0)
                else:
                    self.logger.warning(f"Channel {channel_name} may be inaccessible, will retry next startup")
                    self.progress_tracker.mark_channel_failed(channel_id, "Channel inaccessible or no messages")
                return True
            
            # Process messages using MessageProcessorCoordinator (may raise CancelledError)
            result = await self.message_processor.process_messages(
                messages,
                channel_name,
                channel_id
            )
            
            # Extract message count from result dict
            message_count = result['processed'] if isinstance(result, dict) else result
            
            # Mark as scraped if processing completed successfully
            self.progress_tracker.mark_channel_completed(channel_id, message_count)
            
            self.logger.info(f"Historical scraping complete for {channel_name}: {message_count} messages")
            return True
            
        except asyncio.CancelledError:
            # Don't mark as scraped if cancelled - allow retry on next startup
            self.logger.info(f"Historical scraping cancelled for {channel_name}, will retry on next startup")
            self.progress_tracker.save_channel_status(channel_id, ScrapingStatus.CANCELLED, 0, "Scraping cancelled")
            raise  # Propagate cancellation
        except Exception as e:
            self.logger.error(f"Historical scraping failed for {channel_name}: {e}")
            self.progress_tracker.mark_channel_failed(channel_id, str(e))
            return False
    
    # Old methods removed - now handled by specialized components:
    # - ScrapingProgressTracker: Manages scraping status
    # - MessageFetcher: Fetches messages from Telegram
    # - MessageProcessorCoordinator: Processes messages through pipeline
    
    async def _is_channel_accessible_DEPRECATED(self, channel_id: str) -> bool:
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
            # Ensure client is connected
            if not self.telegram_monitor.client.is_connected():
                self.logger.warning("Client not connected, attempting to connect...")
                await self.telegram_monitor.client.connect()
            
            # Get the channel entity
            channel = await self.telegram_monitor.client.get_entity(channel_id)
            self.logger.info(f"Got channel entity: {channel.title} (ID: {channel.id})")
            
            # Fetch messages (limit=0 means unlimited, but use None for iter_messages)
            fetch_limit = None if limit == 0 else limit
            self.logger.info(f"Fetching messages with limit: {fetch_limit}")
            
            async for message in self.telegram_monitor.client.iter_messages(
                channel,
                limit=fetch_limit
            ):
                if message.text:  # Only process text messages
                    messages.append(message)
            
            self.logger.info(f"Fetched {len(messages)} messages")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error fetching messages: {e}", exc_info=True)
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
                    channel_id=str(message.peer_id.channel_id) 
                        if hasattr(message, 'peer_id') and hasattr(message.peer_id, 'channel_id') else "",
                    channel_name=channel_name,
                    message_id=message.id,
                    message_text=message.text,
                    timestamp=message.date,
                    sender_id=message.sender_id if hasattr(message, 'sender_id') else None,
                    message_obj=message
                )
                
                # Process with timeout to prevent hanging
                try:
                    await asyncio.wait_for(
                        self.message_handler(event),
                        timeout=60.0  # 60 second timeout per message (increased for NLP model loading + API calls)
                    )
                    processed_count += 1
                except asyncio.CancelledError:
                    # System is shutting down - stop processing immediately
                    self.logger.info(f"Message processing cancelled at message {message.id}, stopping scrape")
                    raise  # Re-raise to stop the scrape
                except asyncio.TimeoutError:
                    self.logger.warning(f"⏱️  Message {message.id} timed out - adding to retry queue")
                    # Add to retry queue instead of skipping
                    if not hasattr(self, '_retry_queue'):
                        self._retry_queue = []
                    self._retry_queue.append(message)
                except Exception as msg_error:
                    self.logger.error(f"❌ Message {message.id} failed: {msg_error}")
                    # Add failed messages to retry queue too
                    if not hasattr(self, '_retry_queue'):
                        self._retry_queue = []
                    self._retry_queue.append(message)
                
            except asyncio.CancelledError:
                # Log cancellation at point of detection and propagate immediately
                self.logger.info(f"Cancellation detected at message {i}/{total}, processed {processed_count}/{total}")
                raise
            except Exception as e:
                self.logger.error(f"Error processing message {message.id}: {e}")
                # Continue processing other messages
        
        self.logger.info(f"Completed first pass: {processed_count}/{total} messages processed")
        
        # Retry failed/timed-out messages
        if hasattr(self, '_retry_queue') and self._retry_queue:
            retry_count = len(self._retry_queue)
            self.logger.info(f"🔄 Retrying {retry_count} failed/timed-out messages...")
            
            retry_success = 0
            max_retries = 1  # Only retry once to avoid infinite loops
            
            for retry_attempt in range(max_retries):
                if not self._retry_queue:
                    break
                
                # Take messages from retry queue
                messages_to_retry = self._retry_queue.copy()
                self._retry_queue.clear()
                
                self.logger.info(f"Retry attempt {retry_attempt + 1}/{max_retries}: {len(messages_to_retry)} messages")
                
                for message in messages_to_retry:
                    try:
                        event = MessageEvent(
                            channel_id=str(message.peer_id.channel_id) 
                                if hasattr(message, 'peer_id') and hasattr(message.peer_id, 'channel_id') else "",
                            channel_name=channel_name,
                            message_id=message.id,
                            message_text=message.text or "",
                            timestamp=message.date,
                            sender_id=message.sender_id if hasattr(message, 'sender_id') else None,
                            message_obj=message
                        )
                        
                        # Retry with same timeout
                        await asyncio.wait_for(
                            self.message_handler(event),
                            timeout=60.0
                        )
                        retry_success += 1
                        self.logger.info(f"✅ Retry successful for message {message.id}")
                        
                    except asyncio.TimeoutError:
                        self.logger.warning(f"⏱️  Message {message.id} timed out again on retry")
                        # Don't add back to queue - give up after max retries
                    except Exception as e:
                        self.logger.error(f"❌ Message {message.id} failed again on retry: {e}")
            
            if retry_success > 0:
                self.logger.info(f"✅ Successfully retried {retry_success}/{retry_count} messages")
                processed_count += retry_success
            
            if self._retry_queue:
                self.logger.warning(f"⚠️  {len(self._retry_queue)} messages still failed after retries")
        
        self.logger.info(f"Completed processing {processed_count}/{total} historical messages")
        return processed_count
