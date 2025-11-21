"""
Error handler with retry logic and circuit breaker pattern.

Provides robust error handling with exponential backoff, jitter, and circuit breaker
for resilient message processing.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Type
from datetime import datetime


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents repeated failures by temporarily disabling operations
    after a threshold of consecutive failures.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.
        
        FIXED: Issue #1 - Context Manager Interference
        Removed threading lock to prevent sync/async mixing.
        Lock is now created only in async context.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._state_lock = None  # Will be initialized in async context
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Circuit breaker initialized (threshold={failure_threshold}, timeout={timeout}s)")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN, "timeout elapsed, attempting recovery")
            else:
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    async def _ensure_lock_initialized(self):
        """
        Initialize async lock safely.
        
        FIXED: Issue #1 - Removed threading lock to prevent deadlock.
        Uses simple check since this is only called from async context.
        
        Based on PEP 492: Async operations should not mix with sync primitives.
        """
        if self._state_lock is None:
            self._state_lock = asyncio.Lock()
            self.logger.debug("Circuit breaker lock initialized")
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function through circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Ensure lock is initialized (thread-safe)
        await self._ensure_lock_initialized()
        
        # Check state with lock protection
        async with self._state_lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN, "timeout elapsed, attempting recovery (async)")
                else:
                    raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        try:
            result = await func(*args, **kwargs)
            async with self._state_lock:
                self._on_success()
            return result
        except Exception as e:
            async with self._state_lock:
                self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.timeout
    
    def _transition_to(self, new_state: CircuitState, reason: str = ""):
        """
        Transition to a new state with logging.
        
        Args:
            new_state: Target state
            reason: Reason for transition
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.info(
                f"Circuit breaker: {old_state.value} → {new_state.value} "
                f"({reason if reason else 'no reason specified'})"
            )
    
    def _on_success(self):
        """Handle successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.CLOSED, "successful recovery")
            self.failure_count = 0
        elif self.failure_count > 0:
            self.failure_count = 0
            self.logger.debug("Failure count reset after success")
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN, "failed recovery attempt")
        elif self.failure_count >= self.failure_threshold:
            self._transition_to(
                CircuitState.OPEN,
                f"{self.failure_count} consecutive failures (threshold: {self.failure_threshold})"
            )
    
    def reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = None
        self._transition_to(CircuitState.CLOSED, "manual reset")
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN


@dataclass
class ErrorStats:
    """Error statistics tracking."""
    total_errors: int = 0
    retry_attempts: int = 0
    circuit_breaker_trips: int = 0
    error_types: dict = field(default_factory=dict)
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


class ErrorHandler:
    """
    Error handler with retry logic and circuit breaker.
    
    Provides exponential backoff with jitter for transient failures
    and circuit breaker for persistent failures.
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize error handler.
        
        Args:
            retry_config: Retry configuration (uses defaults if None)
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.stats = ErrorStats()
        self.logger = logging.getLogger(__name__)
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        operation_name: str = "operation",
        error_types: tuple[Type[Exception], ...] = (Exception,),
        use_circuit_breaker: bool = False,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            operation_name: Name for logging and circuit breaker key
            error_types: Tuple of exception types to retry
            use_circuit_breaker: Whether to use circuit breaker
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        circuit_breaker = None
        if use_circuit_breaker:
            if operation_name not in self.circuit_breakers:
                self.circuit_breakers[operation_name] = CircuitBreaker()
            circuit_breaker = self.circuit_breakers[operation_name]
        
        last_exception = None
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                # Execute through circuit breaker if enabled
                if circuit_breaker:
                    result = await circuit_breaker.call_async(func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # Success - log if this was a retry
                if attempt > 1:
                    self.logger.info(
                        f"{operation_name} succeeded on attempt {attempt}/{self.retry_config.max_attempts}"
                    )
                
                return result
                
            except error_types as e:
                last_exception = e
                
                # Don't track circuit breaker state exceptions as operation errors
                if "Circuit breaker is OPEN" not in str(e):
                    self._track_error(e, operation_name)
                
                # Check if circuit breaker is open
                if circuit_breaker and circuit_breaker.is_open():
                    self.stats.circuit_breaker_trips += 1
                    self.logger.error(
                        f"{operation_name} failed: circuit breaker is open"
                    )
                    raise e
                
                # Last attempt - don't retry
                if attempt == self.retry_config.max_attempts:
                    self.logger.error(
                        f"{operation_name} failed after {attempt} attempts: {str(e)}"
                    )
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                
                self.logger.warning(
                    f"{operation_name} failed (attempt {attempt}/{self.retry_config.max_attempts}): "
                    f"{str(e)}. Retrying in {delay:.2f}s..."
                )
                
                self.stats.retry_attempts += 1
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.
        
        Uses "Full Jitter" algorithm from AWS:
        delay = random(0, min(max_delay, base_delay * exponential_base ^ attempt))
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        exponential_delay = self.retry_config.base_delay * (
            self.retry_config.exponential_base ** (attempt - 1)
        )
        
        # Cap at max_delay
        capped_delay = min(self.retry_config.max_delay, exponential_delay)
        
        # Apply jitter if enabled (Full Jitter: random between 0 and capped_delay)
        if self.retry_config.jitter:
            return random.uniform(0, capped_delay)
        else:
            return capped_delay
    
    def _track_error(self, error: Exception, operation_name: str):
        """Track error statistics."""
        self.stats.total_errors += 1
        self.stats.last_error = f"{operation_name}: {str(error)}"
        self.stats.last_error_time = datetime.now()
        
        # Track error type
        error_type = type(error).__name__
        if error_type not in self.stats.error_types:
            self.stats.error_types[error_type] = 0
        self.stats.error_types[error_type] += 1
    
    def get_error_stats(self) -> dict:
        """
        Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': self.stats.total_errors,
            'retry_attempts': self.stats.retry_attempts,
            'circuit_breaker_trips': self.stats.circuit_breaker_trips,
            'error_types': dict(self.stats.error_types),
            'last_error': self.stats.last_error,
            'last_error_time': self.stats.last_error_time.isoformat() if self.stats.last_error_time else None,
            'circuit_breakers': {
                name: {
                    'state': cb.state.value,
                    'failure_count': cb.failure_count
                }
                for name, cb in self.circuit_breakers.items()
            }
        }
    
    def reset_stats(self):
        """Reset error statistics."""
        self.stats = ErrorStats()
        for cb in self.circuit_breakers.values():
            cb.reset()
