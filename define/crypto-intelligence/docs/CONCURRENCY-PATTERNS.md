# Concurrency Patterns and Best Practices

## Overview

This document outlines the concurrency patterns used in the crypto intelligence system to prevent race conditions, deadlocks, and state inconsistencies.

## Core Patterns

### 1. Thread-Safe Lock Initialization

**Problem:** Async locks cannot be created in `__init__` because they require an event loop. Conditional initialization in async methods creates race conditions.

**Solution:** Double-checked locking pattern with initialization guard.

```python
class MyComponent:
    def __init__(self):
        self._lock = None
        self._locks_initialized = False
        self._init_lock = None

    async def _ensure_locks_initialized(self):
        """Initialize async locks in a thread-safe manner."""
        if self._locks_initialized:
            return  # Fast path - already initialized

        # Create init lock if needed
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()

        async with self._init_lock:
            # Double-check after acquiring lock
            if self._locks_initialized:
                return

            # Initialize all locks
            if self._lock is None:
                self._lock = asyncio.Lock()

            self._locks_initialized = True

    async def some_method(self):
        """Any method that needs locks."""
        await self._ensure_locks_initialized()
        async with self._lock:
            # Protected code
            pass
```

**Key Points:**

- Always check `_locks_initialized` first (fast path)
- Use a separate `_init_lock` to protect initialization
- Double-check after acquiring init lock
- Call `_ensure_locks_initialized()` at the start of every method that needs locks

---

### 2. Immediate State Flag Updates

**Problem:** Setting state flags in finally blocks or after operations allows concurrent calls to proceed based on stale state.

**Solution:** Set state flags immediately after guard checks.

```python
async def disconnect(self):
    """Disconnect with immediate state update."""
    await self._ensure_locks_initialized()

    async with self._disconnect_lock:
        # Guard check
        if not self.connected:
            return

        # Set flag IMMEDIATELY to prevent concurrent calls
        self.connected = False

        # Now do the actual work
        try:
            await self.client.disconnect()
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            # Don't reset flag - we're already disconnected
```

**Key Points:**

- Set state flags immediately after guard checks
- Don't reset flags in exception handlers unless appropriate
- Use flags to prevent concurrent operations

---

### 3. In-Progress Operation Tracking

**Problem:** Recursive or concurrent calls to the same operation can cause double cleanup or inconsistent state.

**Solution:** Track in-progress operations with dedicated flags.

```python
async def shutdown(self):
    """Shutdown with in-progress tracking."""
    await self._ensure_locks_initialized()

    async with self._shutdown_lock:
        # Check if already complete
        if self._shutdown_complete:
            return

        # Check if in progress (prevents recursion)
        if self._shutdown_in_progress:
            self.logger.warning("Shutdown already in progress")
            return

        # Mark as in progress
        self._shutdown_in_progress = True

        try:
            # Do cleanup
            await self._cleanup()
        finally:
            # Mark as complete
            self._shutdown_complete = True
```

**Key Points:**

- Use separate flags for "in progress" and "complete"
- Check both flags under lock protection
- Set "in progress" before starting work
- Set "complete" in finally block

---

### 4. Exception Context Preservation

**Problem:** Exception handlers during cleanup can shadow the original error.

**Solution:** Store original exception and log both errors.

```python
async def operation_with_cleanup(self):
    """Operation with cleanup that preserves error context."""
    last_exception = None

    try:
        await self.do_work()
    except Exception as e:
        last_exception = e
        self.logger.error(f"Operation failed: {e}")
        raise
    finally:
        # Cleanup that might also fail
        try:
            await self.cleanup()
        except Exception as cleanup_error:
            self.logger.error(f"Cleanup failed: {cleanup_error}")
            # Log original error for context
            if last_exception:
                self.logger.debug(f"Original error was: {last_exception}")
```

**Key Points:**

- Store original exception before cleanup
- Log both original and cleanup errors
- Don't let cleanup errors shadow original errors
- Consider exception chaining: `raise CleanupError() from original_error`

---

### 5. Conditional Resource Cleanup

**Problem:** Clearing resource references when cleanup fails prevents retry attempts.

**Solution:** Only clear references when cleanup succeeds.

```python
async def stop_monitoring(self):
    """Stop monitoring with conditional cleanup."""
    handler_removed = False

    if self._event_handler:
        try:
            self.client.remove_event_handler(self._event_handler)
            handler_removed = True
            self.logger.debug("Handler removed successfully")
        except Exception as e:
            self.logger.warning(f"Failed to remove handler: {e}")
        finally:
            # Only clear reference if removal succeeded
            if handler_removed:
                self._event_handler = None
            # Otherwise keep reference for retry
```

**Key Points:**

- Track whether cleanup succeeded
- Only clear references on success
- Keep references for retry on failure
- Log cleanup failures for monitoring

---

### 6. Nested Error Zones

**Problem:** Single try-except block for multiple operations makes error handling unclear.

**Solution:** Separate error zones for different operations.

```python
async def handle_message(self, event):
    """Handle message with separated error zones."""

    # Phase 1: Extract data (separate error handling)
    try:
        data = await self.extract_data(event)
    except Exception as e:
        self.logger.error(f"Data extraction failed: {e}")
        return  # Don't proceed if extraction failed

    # Phase 2: Process data (separate error handling)
    if self.callback:
        try:
            await self.callback(data)
        except Exception as e:
            self.logger.error(f"Callback failed: {e}")
            # Track failures but don't stop monitoring
            self._failure_count += 1

            # Emergency shutdown if too many failures
            if self._failure_count >= 10:
                try:
                    await self.shutdown()
                except Exception as shutdown_error:
                    self.logger.error(f"Emergency shutdown failed: {shutdown_error}")
```

**Key Points:**

- Separate try-except blocks for different phases
- Each phase has appropriate error handling
- Nested operations have their own error handling
- Prevents error shadowing between phases

---

## Common Pitfalls

### ❌ DON'T: Initialize locks conditionally without protection

```python
async def method(self):
    if self._lock is None:
        self._lock = asyncio.Lock()  # RACE CONDITION!
    async with self._lock:
        pass
```

### ✅ DO: Use protected initialization

```python
async def method(self):
    await self._ensure_locks_initialized()
    async with self._lock:
        pass
```

---

### ❌ DON'T: Set state flags in finally blocks

```python
async def disconnect(self):
    async with self._lock:
        if not self.connected:
            return
        try:
            await self.client.disconnect()
        finally:
            self.connected = False  # Too late!
```

### ✅ DO: Set state flags immediately

```python
async def disconnect(self):
    async with self._lock:
        if not self.connected:
            return
        self.connected = False  # Immediate!
        await self.client.disconnect()
```

---

### ❌ DON'T: Let cleanup errors shadow original errors

```python
try:
    await operation()
except Exception as e:
    await cleanup()  # If this fails, original error is lost!
    raise
```

### ✅ DO: Protect cleanup from shadowing

```python
last_error = None
try:
    await operation()
except Exception as e:
    last_error = e
    try:
        await cleanup()
    except Exception as cleanup_error:
        self.logger.error(f"Cleanup failed: {cleanup_error}")
        self.logger.debug(f"Original error: {last_error}")
    raise
```

---

### ❌ DON'T: Clear references when cleanup fails

```python
try:
    self.client.remove_handler(self._handler)
finally:
    self._handler = None  # Lost reference even if removal failed!
```

### ✅ DO: Clear references conditionally

```python
removed = False
try:
    self.client.remove_handler(self._handler)
    removed = True
finally:
    if removed:
        self._handler = None
```

---

## Testing Concurrency

### Test Lock Initialization

```python
async def test_concurrent_initialization():
    component = MyComponent()

    # Call initialization concurrently
    tasks = [component._ensure_locks_initialized() for _ in range(10)]
    await asyncio.gather(*tasks)

    # Verify only one lock created
    lock_id = id(component._lock)

    # Call again
    await component._ensure_locks_initialized()

    # Verify same lock
    assert id(component._lock) == lock_id
```

### Test Concurrent Operations

```python
async def test_concurrent_shutdown():
    system = System()
    await system._ensure_locks_initialized()

    # Call shutdown concurrently
    tasks = [system.shutdown() for _ in range(5)]
    await asyncio.gather(*tasks)

    # Verify cleanup happened exactly once
    assert system._shutdown_complete is True
    assert system.cleanup_count == 1
```

### Test State Consistency

```python
async def test_state_consistency():
    component = Component()
    await component._ensure_locks_initialized()

    component.connected = True

    # Start disconnect
    disconnect_task = asyncio.create_task(component.disconnect())

    # Give it time to set flag
    await asyncio.sleep(0.01)

    # Verify flag is set immediately
    assert component.connected is False

    await disconnect_task
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Track Lock Acquisitions

```python
async def _ensure_locks_initialized(self):
    if self._locks_initialized:
        return

    self.logger.debug("Initializing locks...")

    if self._init_lock is None:
        self._init_lock = asyncio.Lock()
        self.logger.debug(f"Created init lock: {id(self._init_lock)}")

    async with self._init_lock:
        if self._locks_initialized:
            self.logger.debug("Locks already initialized by another task")
            return

        self._lock = asyncio.Lock()
        self.logger.debug(f"Created main lock: {id(self._lock)}")
        self._locks_initialized = True
```

### Monitor State Transitions

```python
def _set_state(self, new_state):
    old_state = self.state
    self.state = new_state
    self.logger.info(f"State transition: {old_state} -> {new_state}")
```

---

## References

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Double-checked locking](https://en.wikipedia.org/wiki/Double-checked_locking)
- [Exception chaining](https://docs.python.org/3/tutorial/errors.html#exception-chaining)
- [Async context managers](https://docs.python.org/3/reference/datamodel.html#async-context-managers)
