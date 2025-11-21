"""Async/sync boundary helpers with PEP 492 compliance.

Based on:
- PEP 492: Coroutines with async and await syntax
- Python asyncio documentation
- Best practices from asyncio maintainers

This module provides utilities for safely handling async/sync boundaries
and preventing common pitfalls like task garbage collection and event
loop detection issues.
"""
import asyncio
import functools
import weakref
from typing import Callable, Any, Optional, Set, Coroutine
from utils.logger import get_logger


class TaskTracker:
    """
    Tracks asyncio tasks to prevent garbage collection.
    
    Based on Python asyncio best practices:
    - Store strong references to tasks
    - Clean up completed tasks automatically
    - Provide wait_all() for graceful shutdown
    
    Reference: https://docs.python.org/3/library/asyncio-task.html
    """
    
    def __init__(self, name: str = "TaskTracker"):
        """
        Initialize task tracker.
        
        Args:
            name: Name for logging purposes
        """
        self.name = name
        self._tasks: Set[asyncio.Task] = set()
        self.logger = get_logger(f'TaskTracker.{name}')
    
    def create_task(self, coro: Coroutine, name: Optional[str] = None) -> asyncio.Task:
        """
        Create task with automatic tracking.
        
        Args:
            coro: Coroutine to run
            name: Optional task name
            
        Returns:
            Created task
        """
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        
        # Remove from set when done (prevents memory leak)
        task.add_done_callback(self._tasks.discard)
        
        self.logger.debug(f"Created task: {name or 'unnamed'} (total: {len(self._tasks)})")
        return task
    
    async def wait_all(self, timeout: Optional[float] = None) -> list:
        """
        Wait for all tracked tasks to complete.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            List of task results (or exceptions)
        """
        if not self._tasks:
            return []
        
        self.logger.info(f"Waiting for {len(self._tasks)} tasks to complete...")
        
        try:
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=timeout
                )
            else:
                results = await asyncio.gather(*self._tasks, return_exceptions=True)
            
            self.logger.info(f"All tasks completed")
            return results
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for tasks, {len(self._tasks)} still running")
            raise
    
    def cancel_all(self):
        """Cancel all tracked tasks."""
        if not self._tasks:
            return
        
        self.logger.info(f"Cancelling {len(self._tasks)} tasks...")
        for task in self._tasks:
            if not task.done():
                task.cancel()
    
    def get_active_count(self) -> int:
        """Get number of active tasks."""
        return len(self._tasks)


class AsyncSyncBoundary:
    """
    Manages async/sync boundaries safely.
    
    Based on PEP 492 and asyncio best practices:
    - Detect event loop context
    - Prevent sync calls in async context
    - Provide safe wrappers for both contexts
    
    Reference: https://www.python.org/dev/peps/pep-0492/
    """
    
    @staticmethod
    def is_async_context() -> bool:
        """
        Check if currently in async context.
        
        Returns:
            True if event loop is running
        """
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    @staticmethod
    def require_async_context(func_name: str):
        """
        Raise error if not in async context.
        
        Args:
            func_name: Function name for error message
            
        Raises:
            RuntimeError: If not in async context
        """
        if not AsyncSyncBoundary.is_async_context():
            raise RuntimeError(
                f"{func_name} must be called from async context. "
                f"Use 'await {func_name}()' or run in asyncio.run()"
            )
    
    @staticmethod
    def require_sync_context(func_name: str):
        """
        Raise error if in async context.
        
        Args:
            func_name: Function name for error message
            
        Raises:
            RuntimeError: If in async context
        """
        if AsyncSyncBoundary.is_async_context():
            raise RuntimeError(
                f"{func_name} cannot be called from async context. "
                f"Use the async version instead."
            )
    
    @staticmethod
    async def run_in_executor(func: Callable, *args, **kwargs) -> Any:
        """
        Run blocking function in executor.
        
        Args:
            func: Blocking function to run
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        loop = asyncio.get_running_loop()
        
        # Use functools.partial for kwargs support
        if kwargs:
            func = functools.partial(func, **kwargs)
        
        return await loop.run_in_executor(None, func, *args)


class EventPublisher:
    """
    Safe event publishing with task tracking.
    
    Prevents common issues:
    - Task garbage collection
    - Silent failures
    - Event loss on shutdown
    
    Based on asyncio task management best practices.
    """
    
    def __init__(self, event_bus, name: str = "EventPublisher"):
        """
        Initialize event publisher.
        
        Args:
            event_bus: EventBus instance
            name: Name for logging
        """
        self.event_bus = event_bus
        self.name = name
        self.task_tracker = TaskTracker(name)
        self.logger = get_logger(f'EventPublisher.{name}')
    
    def publish_safe(self, event: Any) -> Optional[asyncio.Task]:
        """
        Publish event safely from any context.
        
        Args:
            event: Event to publish
            
        Returns:
            Task if published, None if queued or failed
        """
        if not self.event_bus:
            self.logger.warning(f"No event bus, dropping {type(event).__name__}")
            return None
        
        try:
            # Check if in async context
            loop = asyncio.get_running_loop()
            
            # Create tracked task
            task = self.task_tracker.create_task(
                self.event_bus.publish(event),
                name=f"publish_{type(event).__name__}"
            )
            
            # Add error handler
            def handle_error(t: asyncio.Task):
                try:
                    t.result()
                except Exception as e:
                    self.logger.error(
                        f"Error publishing {type(event).__name__}: {e}",
                        exc_info=True
                    )
            
            task.add_done_callback(handle_error)
            return task
            
        except RuntimeError:
            # No event loop - cannot publish
            self.logger.debug(
                f"Cannot publish {type(event).__name__} - no event loop running"
            )
            return None
    
    async def wait_for_pending(self, timeout: float = 5.0):
        """
        Wait for all pending event publishing tasks.
        
        Args:
            timeout: Timeout in seconds
        """
        await self.task_tracker.wait_all(timeout=timeout)
    
    def cancel_pending(self):
        """Cancel all pending event publishing tasks."""
        self.task_tracker.cancel_all()
    
    def get_pending_count(self) -> int:
        """Get number of pending event publishing tasks."""
        return self.task_tracker.get_active_count()


def async_only(func: Callable) -> Callable:
    """
    Decorator to enforce async-only functions.
    
    Usage:
        @async_only
        async def my_async_function():
            pass
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped function that validates async context
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        AsyncSyncBoundary.require_async_context(func.__name__)
        return await func(*args, **kwargs)
    
    return wrapper


def sync_only(func: Callable) -> Callable:
    """
    Decorator to enforce sync-only functions.
    
    Usage:
        @sync_only
        def my_sync_function():
            pass
    
    Args:
        func: Sync function to wrap
        
    Returns:
        Wrapped function that validates sync context
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        AsyncSyncBoundary.require_sync_context(func.__name__)
        return func(*args, **kwargs)
    
    return wrapper
