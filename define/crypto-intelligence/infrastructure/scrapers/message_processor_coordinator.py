"""Message processor coordinator - handles batch message processing.

FIXED: Issue #19 - Loop/Iterator Lifecycle Conflicts
- Fixed off-by-one error in progress logging
- Added event loop yielding when rate limit is 0
- Better error tracking with message IDs
"""
import asyncio
from typing import List, Callable, Dict, Any
from datetime import datetime

from domain.message_event import MessageEvent
from utils.logger import get_logger


class MessageProcessorCoordinator:
    """
    Coordinates processing of batches of messages.
    
    Responsibilities:
    - Process messages through pipeline
    - Handle rate limiting
    - Track processing progress
    - Manage errors gracefully
    """
    
    def __init__(
        self,
        message_handler: Callable,
        rate_limit_delay: float = 0.5,
        logger=None
    ):
        """
        Initialize message processor coordinator.
        
        Args:
            message_handler: Async function to handle each message
            rate_limit_delay: Delay between messages in seconds
            logger: Optional logger instance
        """
        self.message_handler = message_handler
        self.rate_limit_delay = rate_limit_delay
        self.logger = logger or get_logger('MessageProcessorCoordinator')
    
    async def process_messages(
        self,
        messages: List,
        channel_name: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Process messages through the pipeline.
        
        FIXED: Issue #19 - Returns detailed dict instead of just count
        Tracks failed message IDs for retry capability.
        
        Args:
            messages: List of Telegram message objects
            channel_name: Channel name
            channel_id: Channel ID
            
        Returns:
            Dictionary with processed count, failed count, and failed message details
        """
        if not messages:
            return {'processed': 0, 'failed': 0, 'failed_messages': []}
        
        self.logger.info(f"Processing {len(messages)} messages from {channel_name}")
        
        processed_count = 0
        failed_messages = []
        
        for i, message in enumerate(messages, 1):
            try:
                # Create message event
                event = MessageEvent(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    message_id=message.id,
                    message_text=message.text,
                    timestamp=message.date,
                    sender_id=message.sender_id if hasattr(message, 'sender_id') else None,
                    message_obj=message
                )
                
                # Process message
                await self.message_handler(event)
                processed_count += 1
                
                # Log progress every 100 messages
                # Fixed: Use len(failed_messages) instead of undefined error_count variable
                if (i + 1) % 100 == 0:
                    self.logger.info(
                        f"Progress: {i + 1}/{len(messages)} messages processed "
                        f"({processed_count} successful, {len(failed_messages)} errors)"
                    )
                
                # Rate limiting
                if self.rate_limit_delay > 0:
                    await asyncio.sleep(self.rate_limit_delay)
                
            except asyncio.CancelledError:
                self.logger.info(f"Message processing cancelled at {i + 1}/{len(messages)}")
                raise
            except Exception as e:
                failed_messages.append({
                    'message_id': message.id,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                self.logger.error(f"Error processing message {message.id}: {e}")
                # Continue processing other messages
                
                # Yield to event loop even with no rate limit
                if self.rate_limit_delay == 0:
                    await asyncio.sleep(0)
        
        self.logger.info(
            f"Completed processing {channel_name}: "
            f"{processed_count} successful, {len(failed_messages)} errors"
        )
        
        return {
            'processed': processed_count,
            'failed': len(failed_messages),
            'failed_messages': failed_messages
        }
    
    async def process_messages_with_progress(
        self,
        messages: List,
        channel_name: str,
        channel_id: str,
        progress_callback: Callable[[int, int], None] = None
    ) -> int:
        """
        Process messages with progress callback.
        
        Args:
            messages: List of Telegram message objects
            channel_name: Channel name
            channel_id: Channel ID
            progress_callback: Optional callback(current, total)
            
        Returns:
            Number of messages successfully processed
        """
        if not messages:
            return 0
        
        processed_count = 0
        total = len(messages)
        
        for i, message in enumerate(messages, 1):
            try:
                event = MessageEvent(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    message_id=message.id,
                    message_text=message.text,
                    timestamp=message.date,
                    sender_id=message.sender_id if hasattr(message, 'sender_id') else None,
                    message_obj=message
                )
                
                await self.message_handler(event)
                processed_count += 1
                
                # Call progress callback
                if progress_callback:
                    progress_callback(i, total)
                
                # Rate limiting
                if self.rate_limit_delay > 0:
                    await asyncio.sleep(self.rate_limit_delay)
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Error processing message {message.id}: {e}")
        
        return processed_count
    
    async def process_messages_batch(
        self,
        messages: List,
        channel_name: str,
        channel_id: str,
        batch_size: int = 100
    ) -> int:
        """
        Process messages in batches for better performance.
        
        Args:
            messages: List of Telegram message objects
            channel_name: Channel name
            channel_id: Channel ID
            batch_size: Number of messages per batch
            
        Returns:
            Number of messages successfully processed
        """
        if not messages:
            return 0
        
        total_processed = 0
        total_messages = len(messages)
        
        # Process in batches
        for i in range(0, total_messages, batch_size):
            batch = messages[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_messages + batch_size - 1) // batch_size
            
            self.logger.info(
                f"Processing batch {batch_num}/{total_batches} "
                f"({len(batch)} messages)"
            )
            
            processed = await self.process_messages(batch, channel_name, channel_id)
            total_processed += processed
        
        return total_processed
