# Control Flow Best Practices

This document outlines best practices for maintaining robust control flow in the crypto-intelligence system, based on the fixes implemented on 2025-11-20.

---

## 1. Async/Sync Boundary Management

### ❌ Don't: Call async functions from sync contexts without handling
```python
def sync_function(self):
    # This will fail if no event loop is running
    asyncio.create_task(self.async_operation())
```

### ✅ Do: Queue operations when event loop unavailable
```python
def sync_function(self):
    try:
        loop = asyncio.get_running_loop()
        task = asyncio.create_task(self.async_operation())
        task.add_done_callback(self._handle_error)
    except RuntimeError:
        # Queue for later processing
        self._pending_operations.append(operation)
```

---

## 2. State Machine Transitions

### ❌ Don't: Modify state without lock protection
```python
async def start(self):
    if self._state == "running":
        return
    self._state = "starting"  # RACE CONDITION
    # ... start logic ...
```

### ✅ Do: Use atomic state transitions with locks
```python
async def start(self):
    async with self._state_lock:
        if self._state == "running":
            return
        self._state = "starting"
    
    # Perform operations outside lock
    try:
        # ... start logic ...
    finally:
        async with self._state_lock:
            self._state = "running"
```

---

## 3. Resource Cleanup

### ❌ Don't: Allow double cleanup
```python
async def cleanup(self):
    if self.resource:
        await self.resource.close()  # Could be called twice
```

### ✅ Do: Guard against double cleanup
```python
async def cleanup(self):
    if 'resource' not in self._cleanup_completed:
        if self.resource:
            await self.resource.close()
            self._cleanup_completed.add('resource')
```

---

## 4. Error Recovery

### ❌ Don't: Stop on first failure
```python
if self._failure_count >= 10:
    raise RuntimeError("Too many failures")
```

### ✅ Do: Use exponential backoff
```python
if self._failure_count >= 10:
    backoff = min(2 ** (self._failure_count - 10), 60)
    await asyncio.sleep(backoff)

if self._failure_count >= 20:
    raise RuntimeError("Persistent failures")
```

---

## 5. Queue Draining

### ❌ Don't: Exit immediately on cancellation
```python
try:
    while True:
        item = await queue.get()
        await process(item)
except asyncio.CancelledError:
    break  # Messages lost!
```

### ✅ Do: Drain queue before exiting
```python
try:
    while True:
        item = await queue.get()
        await process(item)
except asyncio.CancelledError:
    # Drain remaining items
    while not queue.empty():
        try:
            item = queue.get_nowait()
            await process(item)
        except asyncio.QueueEmpty:
            break
    raise
```

---

## 6. Lock Initialization

### ❌ Don't: Create locks conditionally without protection
```python
async def ensure_lock(self):
    if not hasattr(self, '_lock'):
        self._lock = asyncio.Lock()  # RACE CONDITION
```

### ✅ Do: Use module-level lock for initialization
```python
_global_init_lock = None

async def ensure_lock(self):
    global _global_init_lock
    if _global_init_lock is None:
        _global_init_lock = asyncio.Lock()
    
    async with _global_init_lock:
        if not hasattr(self, '_lock'):
            self._lock = asyncio.Lock()
```

---

## 7. Event Handler Cleanup

### ❌ Don't: Clear state outside lock
```python
try:
    # ... monitoring ...
finally:
    self._active = False  # RACE CONDITION
    self._handler = None
```

### ✅ Do: Protect state changes with locks
```python
try:
    # ... monitoring ...
finally:
    async with self._lock:
        self._active = False
        handler = self._handler
        self._handler = None
    
    # Cleanup outside lock
    if handler:
        cleanup(handler)
```

---

## 8. Callback Error Isolation

### ❌ Don't: Let callback errors stop the loop
```python
for item in items:
    await callback(item)  # Exception stops loop
```

### ✅ Do: Isolate callback errors
```python
for item in items:
    try:
        await callback(item)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Continue processing
```

---

## 9. Timeout Handling

### ❌ Don't: Ignore timeout errors
```python
try:
    result = await asyncio.wait_for(operation(), timeout=5)
except asyncio.TimeoutError:
    pass  # Silent failure
```

### ✅ Do: Handle timeouts explicitly
```python
try:
    result = await asyncio.wait_for(operation(), timeout=5)
except asyncio.TimeoutError:
    logger.warning("Operation timed out, using fallback")
    result = fallback_value
```

---

## 10. Finally Block Safety

### ❌ Don't: Return from finally blocks
```python
try:
    await operation()
finally:
    cleanup()
    return result  # Shadows exceptions!
```

### ✅ Do: Let exceptions propagate
```python
try:
    result = await operation()
    return result
finally:
    cleanup()  # Always runs, exceptions propagate
```

---

## Common Patterns

### Pattern: Idempotent Shutdown
```python
async def shutdown(self):
    async with self._lock:
        if self._state == "stopped":
            return
        self._state = "stopping"
    
    try:
        await self._cleanup()
    finally:
        async with self._lock:
            self._state = "stopped"
```

### Pattern: Event Publishing with Fallback
```python
def publish_event(self, event):
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(self._publish(event))
    except RuntimeError:
        self._pending_events.append(event)
```

### Pattern: Graceful Consumer Loop
```python
async def consumer_loop(self):
    try:
        while self._running:
            item = await self.queue.get()
            await self.process(item)
    except asyncio.CancelledError:
        await self._drain_queue()
        raise
```

---

## Testing Guidelines

### Test State Transitions
```python
async def test_concurrent_start():
    system = System()
    tasks = [system.start() for _ in range(10)]
    await asyncio.gather(*tasks)
    # Should only start once
```

### Test Idempotency
```python
async def test_multiple_shutdowns():
    system = System()
    await system.start()
    await system.shutdown()
    await system.shutdown()  # Should be safe
```

### Test Error Recovery
```python
async def test_failure_recovery():
    system = System()
    # Simulate failures
    for _ in range(15):
        system._failure_count += 1
    # Should apply backoff, not crash
```

---

## Code Review Checklist

When reviewing control flow code, check for:

- [ ] State changes are protected by locks
- [ ] Early returns don't skip cleanup
- [ ] Exceptions don't prevent resource release
- [ ] Async operations handle missing event loop
- [ ] Cleanup is idempotent
- [ ] Errors are isolated and logged
- [ ] Timeouts are handled explicitly
- [ ] Queue draining on cancellation
- [ ] Lock initialization is thread-safe
- [ ] Finally blocks don't shadow exceptions

---

## References

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Control Flow Fixes Implementation Report](../CONTROL_FLOW_FIXES_IMPLEMENTED.md)
- [Control Flow Analysis Report](../CONTROL_FLOW_ANALYSIS_REPORT.md)
