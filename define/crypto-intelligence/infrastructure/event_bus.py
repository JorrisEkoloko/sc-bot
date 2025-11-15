"""Event bus for publish-subscribe pattern with async support.

Implements the observer pattern for decoupled component communication.
Based on Wikipedia publish-subscribe pattern and Python asyncio best practices.
"""
import asyncio
from typing import Callable, Dict, List, Type, Any
from collections import defaultdict
import logging


class EventBus:
    """
    Async event bus for publish-subscribe messaging.
    
    Features:
    - Type-safe event routing (events routed by class type)
    - Async callback support (non-blocking event handling)
    - Multiple subscribers per event type
    - Error isolation (one subscriber failure doesn't affect others)
    - Thread-safe subscription management
    
    Usage:
        bus = EventBus()
        
        # Subscribe
        async def on_signal_completed(event: SignalCompletedEvent):
            print(f"Signal completed: {event.signal_id}")
        
        bus.subscribe(SignalCompletedEvent, on_signal_completed)
        
        # Publish
        event = SignalCompletedEvent(signal_id="123", ...)
        await bus.publish(event)
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize event bus.
        
        Args:
            logger: Optional logger for debugging
        """
        self._subscribers: Dict[Type, List[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self.logger = logger or logging.getLogger('EventBus')
        self._stats = {
            'events_published': 0,
            'events_delivered': 0,
            'subscriber_errors': 0
        }
    
    async def subscribe(self, event_type: Type, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event class to subscribe to (e.g., SignalCompletedEvent)
            callback: Async function to call when event is published
                     Signature: async def callback(event: EventType) -> None
        
        Example:
            async def on_signal_completed(event: SignalCompletedEvent):
                await process_signal(event)
            
            await bus.subscribe(SignalCompletedEvent, on_signal_completed)
        """
        async with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                self.logger.debug(
                    f"Subscribed {callback.__name__} to {event_type.__name__}"
                )
            else:
                self.logger.warning(
                    f"Callback {callback.__name__} already subscribed to {event_type.__name__}"
                )
    
    def subscribe_sync(self, event_type: Type, callback: Callable) -> None:
        """
        Synchronous version of subscribe for use in __init__ methods.
        
        Args:
            event_type: Event class to subscribe to
            callback: Async function to call when event is published
        
        Note: This is a convenience method for non-async contexts.
              The callback must still be async.
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            self.logger.debug(
                f"Subscribed {callback.__name__} to {event_type.__name__} (sync)"
            )
    
    async def unsubscribe(self, event_type: Type, callback: Callable) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event class to unsubscribe from
            callback: Callback function to remove
        """
        async with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                self.logger.debug(
                    f"Unsubscribed {callback.__name__} from {event_type.__name__}"
                )
            else:
                self.logger.warning(
                    f"Callback {callback.__name__} not found for {event_type.__name__}"
                )
    
    async def publish(self, event: Any) -> list:
        """
        Publish an event to all subscribers.
        
        Events are delivered asynchronously and concurrently to all subscribers.
        If a subscriber raises an exception, it's logged but doesn't affect other subscribers.
        
        Args:
            event: Event instance to publish (must be an instance of a registered event type)
        
        Returns:
            List of exceptions from failed subscribers (empty if all succeeded)
        
        Example:
            event = SignalCompletedEvent(
                signal_id="123",
                address="0xabc...",
                ath_multiplier=3.5
            )
            failures = await bus.publish(event)
            if failures:
                logger.warning(f"{len(failures)} subscribers failed")
        """
        event_type = type(event)
        
        # Get subscribers (no lock needed for read)
        subscribers = self._subscribers.get(event_type, [])
        
        if not subscribers:
            self.logger.debug(f"No subscribers for {event_type.__name__}")
            return []
        
        self._stats['events_published'] += 1
        
        # Create tasks for all subscribers (concurrent execution)
        tasks = []
        for callback in subscribers:
            task = asyncio.create_task(
                self._safe_callback(callback, event, event_type.__name__)
            )
            tasks.append(task)
        
        # Wait for all callbacks to complete and collect failures
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract failures
        failures = [r for r in results if isinstance(r, Exception)]
        
        if failures:
            self.logger.warning(
                f"Published {event_type.__name__} to {len(subscribers)} subscriber(s) "
                f"with {len(failures)} failure(s)"
            )
        else:
            self.logger.debug(
                f"Published {event_type.__name__} to {len(subscribers)} subscriber(s)"
            )
        
        return failures
    
    async def _safe_callback(
        self, 
        callback: Callable, 
        event: Any, 
        event_name: str
    ) -> Exception | None:
        """
        Execute callback with error handling.
        
        Args:
            callback: Subscriber callback function
            event: Event to pass to callback
            event_name: Event type name for logging
            
        Returns:
            Exception if callback failed, None if succeeded
        """
        try:
            # Check if callback is async
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                # Synchronous callback - run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, callback, event)
            
            self._stats['events_delivered'] += 1
            return None
            
        except Exception as e:
            self._stats['subscriber_errors'] += 1
            self.logger.error(
                f"Error in subscriber {callback.__name__} for {event_name}: {e}",
                exc_info=True
            )
            return e
    
    def get_subscriber_count(self, event_type: Type) -> int:
        """
        Get number of subscribers for an event type.
        
        Args:
            event_type: Event class
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))
    
    def get_all_subscriptions(self) -> Dict[str, int]:
        """
        Get subscription counts for all event types.
        
        Returns:
            Dictionary mapping event type names to subscriber counts
        """
        return {
            event_type.__name__: len(callbacks)
            for event_type, callbacks in self._subscribers.items()
        }
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get event bus statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self._stats.copy()
    
    async def clear_all_subscriptions(self) -> None:
        """Clear all subscriptions (useful for testing)."""
        async with self._lock:
            self._subscribers.clear()
            self.logger.info("Cleared all subscriptions")
    
    def __repr__(self) -> str:
        """String representation."""
        total_subscribers = sum(len(callbacks) for callbacks in self._subscribers.values())
        return (
            f"EventBus(event_types={len(self._subscribers)}, "
            f"total_subscribers={total_subscribers})"
        )
