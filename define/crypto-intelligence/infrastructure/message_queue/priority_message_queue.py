"""Priority message queue for channel-based message processing.

Implements producer-consumer pattern with priority based on channel reputation.
Based on verified patterns:
- asyncio.PriorityQueue (Python official docs)
- Producer-consumer pattern (Dijkstra 1965)
- Token bucket rate limiting (industry standard)
"""
import asyncio
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from domain.message_event import MessageEvent
from utils.logger import setup_logger
from utils.rate_limiter import RateLimiter


@dataclass(order=True)
class PrioritizedMessage:
    """Message with priority for queue ordering."""
    priority: float = field(compare=True)  # Lower = higher priority (min-heap)
    timestamp: datetime = field(compare=True)  # Tie-breaker: older first
    event: MessageEvent = field(compare=False)


class PriorityMessageQueue:
    """
    Priority queue for message processing with rate limiting.
    
    Features:
    - Priority based on channel reputation (high-rep channels processed first)
    - Global rate limiting (prevents API flooding)
    - Backpressure handling (queue fills up, producers slow down)
    - Graceful shutdown
    
    Based on verified patterns:
    - asyncio.PriorityQueue (Python docs)
    - Producer-consumer (Dijkstra 1965)
    - Token bucket rate limiting
    """
    
    def __init__(
        self,
        reputation_engine,
        max_queue_size: int = 1000,
        messages_per_second: float = 2.0,
        logger=None
    ):
        """
        Initialize priority message queue.
        
        Args:
            reputation_engine: ReputationEngine for channel priority
            max_queue_size: Maximum queue size (backpressure threshold)
            messages_per_second: Global message processing rate limit
            logger: Optional logger instance
        """
        self.reputation_engine = reputation_engine
        self.max_queue_size = max_queue_size
        self.messages_per_second = messages_per_second
        self.logger = logger or setup_logger('PriorityMessageQueue')
        
        # Priority queue (min-heap: lower priority value = higher priority)
        self.queue = asyncio.PriorityQueue(maxsize=max_queue_size)
        
        # Global rate limiter (messages per second)
        # Convert to messages per minute for RateLimiter
        messages_per_minute = int(messages_per_second * 60)
        self.rate_limiter = RateLimiter(messages_per_minute, 60)
        
        # Consumer task
        self._consumer_task: Optional[asyncio.Task] = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            'total_enqueued': 0,
            'total_processed': 0,
            'total_dropped': 0,
            'queue_full_count': 0
        }
        
        self.logger.info(
            f"Priority message queue initialized: "
            f"max_size={max_queue_size}, "
            f"rate={messages_per_second:.1f} msg/s"
        )
    
    def get_channel_priority(self, channel_name: str) -> float:
        """
        Get priority for channel based on reputation.
        
        Higher reputation = lower priority value (processed first in min-heap).
        
        Args:
            channel_name: Channel name
            
        Returns:
            Priority value (lower = higher priority)
        """
        reputation = self.reputation_engine.get_reputation(channel_name)
        
        if reputation:
            # Invert reputation score (0-100) to priority (100-0)
            # High reputation (100) -> low priority value (0) -> processed first
            priority = 100 - reputation.reputation_score
        else:
            # Unknown channel -> medium priority (50)
            priority = 50
        
        return priority
    
    async def enqueue(self, event: MessageEvent) -> bool:
        """
        Enqueue message with priority based on channel reputation.
        
        Args:
            event: Message event to enqueue
            
        Returns:
            True if enqueued, False if queue full (dropped)
        """
        try:
            # Get channel priority
            priority = self.get_channel_priority(event.channel_name)
            
            # Create prioritized message
            prioritized = PrioritizedMessage(
                priority=priority,
                timestamp=event.timestamp,
                event=event
            )
            
            # Try to enqueue (non-blocking)
            self.queue.put_nowait(prioritized)
            
            self.stats['total_enqueued'] += 1
            
            self.logger.debug(
                f"Enqueued message from {event.channel_name} "
                f"(priority={priority:.1f}, queue_size={self.queue.qsize()})"
            )
            
            return True
            
        except asyncio.QueueFull:
            # Queue full - drop message (backpressure)
            self.stats['total_dropped'] += 1
            self.stats['queue_full_count'] += 1
            
            self.logger.warning(
                f"Queue full ({self.max_queue_size}), dropped message from {event.channel_name}. "
                f"Total dropped: {self.stats['total_dropped']}"
            )
            
            return False
    
    async def start_consumer(self, message_handler: Callable):
        """
        Start consumer task that processes messages from queue.
        
        Args:
            message_handler: Async function to handle each message
        """
        if self._running:
            self.logger.warning("Consumer already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        self._consumer_task = asyncio.create_task(
            self._consumer_loop(message_handler)
        )
        
        self.logger.info("Consumer started")
    
    async def _consumer_loop(self, message_handler: Callable):
        """
        Consumer loop that processes messages with rate limiting.
        
        Args:
            message_handler: Async function to handle each message
        """
        self.logger.info("Consumer loop started")
        
        try:
            while self._running:
                try:
                    # Get message from queue (with timeout for shutdown check)
                    try:
                        prioritized = await asyncio.wait_for(
                            self.queue.get(),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        # No message available, check if shutting down
                        if self._shutdown_event.is_set():
                            break
                        continue
                    
                    # Apply global rate limiting
                    await self.rate_limiter.acquire()
                    
                    # Process message with retry on failure
                    try:
                        await message_handler(prioritized.event)
                        self.stats['total_processed'] += 1
                        
                        self.logger.debug(
                            f"Processed message from {prioritized.event.channel_name} "
                            f"(priority={prioritized.priority:.1f})"
                        )
                        
                    except Exception as e:
                        self.logger.error(
                            f"❌ Error processing message from {prioritized.event.channel_name}: {e}"
                        )
                        
                        # Retry logic: add message back to queue with lower priority
                        # Check if this message has already been retried
                        retry_count = getattr(prioritized.event, '_retry_count', 0)
                        max_retries = 1
                        
                        if retry_count < max_retries:
                            # Add back to queue with lower priority (will be processed later)
                            prioritized.event._retry_count = retry_count + 1
                            new_priority = prioritized.priority + 100  # Much lower priority
                            
                            retry_msg = PrioritizedMessage(
                                priority=new_priority,
                                timestamp=prioritized.timestamp,
                                event=prioritized.event
                            )
                            
                            try:
                                self.queue.put_nowait(retry_msg)
                                self.logger.info(
                                    f"🔄 Added message to retry queue (attempt {retry_count + 1}/{max_retries}): "
                                    f"{prioritized.event.channel_name} (ID: {prioritized.event.message_id})"
                                )
                            except asyncio.QueueFull:
                                self.logger.warning(f"⚠️  Queue full, cannot retry message {prioritized.event.message_id}")
                        else:
                            self.logger.warning(
                                f"⚠️  Message failed after {max_retries} retries, giving up: "
                                f"{prioritized.event.channel_name} (ID: {prioritized.event.message_id})"
                            )
                    
                    finally:
                        # Mark task as done
                        self.queue.task_done()
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error in consumer loop: {e}", exc_info=True)
        
        except asyncio.CancelledError:
            self.logger.info("Consumer loop cancelled, draining remaining messages...")
            
            # Drain remaining messages (with timeout)
            import time
            drain_start = time.time()
            drain_timeout = 10.0
            drained_count = 0
            
            while not self.queue.empty() and (time.time() - drain_start) < drain_timeout:
                try:
                    prioritized = self.queue.get_nowait()
                    await message_handler(prioritized.event)
                    self.queue.task_done()
                    drained_count += 1
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    self.logger.error(f"Error draining message: {e}")
                    self.queue.task_done()
            
            remaining = self.queue.qsize()
            if drained_count > 0:
                self.logger.info(f"Drained {drained_count} messages during shutdown")
            if remaining > 0:
                self.logger.warning(f"Shutdown with {remaining} messages unprocessed")
            
            raise  # Re-raise to complete cancellation
        
        self.logger.info("Consumer loop stopped")
    
    async def stop_consumer(self, timeout: float = 30.0):
        """
        Stop consumer and wait for queue to drain.
        
        Args:
            timeout: Maximum time to wait for queue to drain (seconds)
        """
        if not self._running:
            return
        
        self.logger.info("Stopping consumer...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for queue to drain (with timeout)
        try:
            await asyncio.wait_for(self.queue.join(), timeout=timeout)
            self.logger.info("Queue drained successfully")
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Queue drain timeout ({timeout}s), "
                f"{self.queue.qsize()} messages remaining"
            )
        
        # Stop consumer task
        self._running = False
        
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Consumer stopped")
    
    def get_stats(self) -> dict:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'is_running': self._running,
            'processing_rate': self.messages_per_second
        }
    
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running
