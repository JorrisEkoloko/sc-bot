"""Message fetcher - handles fetching messages from Telegram channels."""
import asyncio
from typing import List, Optional

from infrastructure.telegram.telegram_monitor import TelegramMonitor
from utils.logger import get_logger


class MessageFetcher:
    """
    Fetches historical messages from Telegram channels.
    
    Responsibilities:
    - Check channel accessibility
    - Fetch messages with limits
    - Handle rate limiting
    - Manage fetch errors
    """
    
    def __init__(self, telegram_monitor: TelegramMonitor, logger=None):
        """
        Initialize message fetcher.
        
        Args:
            telegram_monitor: TelegramMonitor instance
            logger: Optional logger instance
        """
        self.telegram_monitor = telegram_monitor
        self.logger = logger or get_logger('MessageFetcher')
    
    async def is_channel_accessible(self, channel_id: str) -> bool:
        """
        Check if channel is accessible.
        
        Args:
            channel_id: Channel ID or username
            
        Returns:
            True if channel is accessible
        """
        try:
            entity = await self.telegram_monitor.client.get_entity(channel_id)
            self.logger.debug(f"Channel {channel_id} is accessible")
            return True
        except Exception as e:
            self.logger.error(f"Channel {channel_id} not accessible: {e}")
            return False
    
    async def fetch_messages(
        self,
        channel_id: str,
        limit: int,
        reverse: bool = True
    ) -> List:
        """
        Fetch historical messages from channel.
        
        Args:
            channel_id: Channel ID or username
            limit: Maximum number of messages to fetch (0 = unlimited)
            reverse: If True, fetch oldest messages first
            
        Returns:
            List of message objects
        """
        try:
            self.logger.info(
                f"Fetching {'all' if limit == 0 else limit} messages from {channel_id} "
                f"({'oldest first' if reverse else 'newest first'})"
            )
            
            messages = []
            
            if limit == 0:
                # Fetch all messages (unlimited)
                self.logger.info(f"Fetching ALL messages from {channel_id} (this may take a while)")
                async for message in self.telegram_monitor.client.iter_messages(
                    channel_id,
                    reverse=reverse
                ):
                    if message.text:  # Only text messages
                        messages.append(message)
                    
                    # Log progress every 1000 messages
                    if len(messages) % 1000 == 0:
                        self.logger.info(f"Fetched {len(messages)} messages so far...")
            else:
                # Fetch limited messages
                async for message in self.telegram_monitor.client.iter_messages(
                    channel_id,
                    limit=limit,
                    reverse=reverse
                ):
                    if message.text:  # Only text messages
                        messages.append(message)
            
            self.logger.info(f"Fetched {len(messages)} messages from {channel_id}")
            return messages
            
        except asyncio.CancelledError:
            self.logger.info(f"Message fetch cancelled for {channel_id}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching messages from {channel_id}: {e}")
            return []
    
    async def fetch_messages_with_retry(
        self,
        channel_id: str,
        limit: int,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> List:
        """
        Fetch messages with retry logic.
        
        Args:
            channel_id: Channel ID or username
            limit: Maximum number of messages to fetch
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            List of message objects
        """
        for attempt in range(max_retries):
            try:
                messages = await self.fetch_messages(channel_id, limit)
                return messages
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Fetch attempt {attempt + 1}/{max_retries} failed for {channel_id}: {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    self.logger.error(
                        f"All {max_retries} fetch attempts failed for {channel_id}"
                    )
                    return []
        
        return []
    
    async def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """
        Get channel information.
        
        Args:
            channel_id: Channel ID or username
            
        Returns:
            Dictionary with channel info or None
        """
        try:
            entity = await self.telegram_monitor.client.get_entity(channel_id)
            
            info = {
                'id': entity.id,
                'title': getattr(entity, 'title', ''),
                'username': getattr(entity, 'username', ''),
                'participants_count': getattr(entity, 'participants_count', 0),
                'is_broadcast': getattr(entity, 'broadcast', False)
            }
            
            return info
        except Exception as e:
            self.logger.error(f"Error getting channel info for {channel_id}: {e}")
            return None
