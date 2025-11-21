"""Tests for async/sync boundary helpers.

Validates PEP 492 compliance and task tracking.
"""
import pytest
import asyncio
from utils.async_helpers import (
    TaskTracker,
    AsyncSyncBoundary,
    EventPublisher,
    async_only,
    sync_only
)


class TestTaskTracker:
    """Test task tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test task creation and tracking."""
        tracker = TaskTracker("test")
        
        async def dummy_task():
            await asyncio.sleep(0.1)
            return "done"
        
        task = tracker.create_task(dummy_task(), name="dummy")
        assert tracker.get_active_count() == 1
        
        result = await task
        assert result == "done"
        
        # Task should be removed after completion
        await asyncio.sleep(0.01)
        assert tracker.get_active_count() == 0
    
    @pytest.mark.asyncio
    async def test_wait_all(self):
        """Test waiting for all tasks."""
        tracker = TaskTracker("test")
        
        async def task_func(n):
            await asyncio.sleep(0.1)
            return n * 2
        
        # Create multiple tasks
        for i in range(5):
            tracker.create_task(task_func(i), name=f"task_{i}")
        
        assert tracker.get_active_count() == 5
        
        results = await tracker.wait_all(timeout=1.0)
        assert len(results) == 5
        assert sorted(results) == [0, 2, 4, 6, 8]
    
    @pytest.mark.asyncio
    async def test_cancel_all(self):
        """Test cancelling all tasks."""
        tracker = TaskTracker("test")
        
        async def long_task():
            await asyncio.sleep(10)
        
        # Create tasks
        for i in range(3):
            tracker.create_task(long_task(), name=f"long_{i}")
        
        assert tracker.get_active_count() == 3
        
        # Cancel all
        tracker.cancel_all()
        
        # Wait a bit for cancellation to propagate
        await asyncio.sleep(0.1)
        
        # All tasks should be cancelled
        assert tracker.get_active_count() == 0


class TestAsyncSyncBoundary:
    """Test async/sync boundary detection."""
    
    def test_is_async_context_sync(self):
        """Test detection in sync context."""
        assert not AsyncSyncBoundary.is_async_context()
    
    @pytest.mark.asyncio
    async def test_is_async_context_async(self):
        """Test detection in async context."""
        assert AsyncSyncBoundary.is_async_context()
    
    @pytest.mark.asyncio
    async def test_require_async_context(self):
        """Test async context requirement."""
        # Should not raise in async context
        AsyncSyncBoundary.require_async_context("test_func")
    
    def test_require_async_context_fails(self):
        """Test async context requirement fails in sync."""
        with pytest.raises(RuntimeError, match="must be called from async context"):
            AsyncSyncBoundary.require_async_context("test_func")
    
    def test_require_sync_context(self):
        """Test sync context requirement."""
        # Should not raise in sync context
        AsyncSyncBoundary.require_sync_context("test_func")
    
    @pytest.mark.asyncio
    async def test_require_sync_context_fails(self):
        """Test sync context requirement fails in async."""
        with pytest.raises(RuntimeError, match="cannot be called from async context"):
            AsyncSyncBoundary.require_sync_context("test_func")
    
    @pytest.mark.asyncio
    async def test_run_in_executor(self):
        """Test running blocking function in executor."""
        def blocking_func(x, y):
            return x + y
        
        result = await AsyncSyncBoundary.run_in_executor(blocking_func, 5, 10)
        assert result == 15


class TestDecorators:
    """Test async_only and sync_only decorators."""
    
    @pytest.mark.asyncio
    async def test_async_only_decorator(self):
        """Test async_only decorator."""
        @async_only
        async def my_async_func():
            return "async"
        
        result = await my_async_func()
        assert result == "async"
    
    def test_sync_only_decorator(self):
        """Test sync_only decorator."""
        @sync_only
        def my_sync_func():
            return "sync"
        
        result = my_sync_func()
        assert result == "sync"


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.published_events = []
    
    async def publish(self, event):
        """Mock publish method."""
        await asyncio.sleep(0.01)  # Simulate async work
        self.published_events.append(event)


class TestEventPublisher:
    """Test event publisher with task tracking."""
    
    @pytest.mark.asyncio
    async def test_publish_safe(self):
        """Test safe event publishing."""
        event_bus = MockEventBus()
        publisher = EventPublisher(event_bus, "test")
        
        # Publish event
        task = publisher.publish_safe("test_event")
        assert task is not None
        assert publisher.get_pending_count() == 1
        
        # Wait for completion
        await publisher.wait_for_pending(timeout=1.0)
        
        assert len(event_bus.published_events) == 1
        assert event_bus.published_events[0] == "test_event"
        assert publisher.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_publish_multiple(self):
        """Test publishing multiple events."""
        event_bus = MockEventBus()
        publisher = EventPublisher(event_bus, "test")
        
        # Publish multiple events
        for i in range(5):
            publisher.publish_safe(f"event_{i}")
        
        assert publisher.get_pending_count() == 5
        
        # Wait for all
        await publisher.wait_for_pending(timeout=1.0)
        
        assert len(event_bus.published_events) == 5
        assert publisher.get_pending_count() == 0
    
    def test_publish_safe_no_loop(self):
        """Test publishing without event loop."""
        event_bus = MockEventBus()
        publisher = EventPublisher(event_bus, "test")
        
        # Should return None (no event loop)
        task = publisher.publish_safe("test_event")
        assert task is None
