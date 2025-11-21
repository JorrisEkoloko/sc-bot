"""Resource lifecycle management with guaranteed cleanup.

Based on:
- PEP 343: The "with" Statement
- Context manager best practices
- RAII (Resource Acquisition Is Initialization) pattern

This module provides utilities for managing resource lifecycles with
guaranteed cleanup, even in the presence of exceptions.
"""
import asyncio
from typing import Optional, Callable, Any, Dict, Set
from enum import Enum
from utils.logger import get_logger


class ResourceState(Enum):
    """Resource lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class ManagedResource:
    """
    Managed resource with state tracking and guaranteed cleanup.
    
    Based on RAII pattern and PEP 343 context managers.
    Ensures resources are properly cleaned up even on exceptions.
    
    Reference: https://www.python.org/dev/peps/pep-0343/
    """
    
    def __init__(
        self,
        name: str,
        init_func: Optional[Callable] = None,
        cleanup_func: Optional[Callable] = None,
        async_cleanup: bool = False
    ):
        """
        Initialize managed resource.
        
        Args:
            name: Resource name for logging
            init_func: Optional initialization function
            cleanup_func: Optional cleanup function
            async_cleanup: Whether cleanup is async
        """
        self.name = name
        self.init_func = init_func
        self.cleanup_func = cleanup_func
        self.async_cleanup = async_cleanup
        self.state = ResourceState.UNINITIALIZED
        self.resource: Any = None
        self.logger = get_logger(f'ManagedResource.{name}')
        self._lock: Optional[asyncio.Lock] = None
    
    async def _ensure_lock(self):
        """Ensure lock is initialized."""
        if self._lock is None:
            self._lock = asyncio.Lock()
    
    async def initialize(self) -> Any:
        """
        Initialize resource with state validation.
        
        Returns:
            Initialized resource
            
        Raises:
            RuntimeError: If resource is not in valid state for initialization
        """
        await self._ensure_lock()
        
        async with self._lock:
            if self.state == ResourceState.READY:
                self.logger.debug(f"Resource already initialized")
                return self.resource
            
            if self.state not in [ResourceState.UNINITIALIZED, ResourceState.ERROR]:
                raise RuntimeError(
                    f"Cannot initialize resource in state {self.state.value}"
                )
            
            self.state = ResourceState.INITIALIZING
            
            try:
                if self.init_func:
                    if asyncio.iscoroutinefunction(self.init_func):
                        self.resource = await self.init_func()
                    else:
                        self.resource = self.init_func()
                
                self.state = ResourceState.READY
                self.logger.info(f"Resource initialized")
                return self.resource
                
            except Exception as e:
                self.state = ResourceState.ERROR
                self.logger.error(f"Resource initialization failed: {e}")
                raise
    
    async def cleanup(self, force: bool = False):
        """
        Cleanup resource with state validation.
        
        Args:
            force: Force cleanup even if already closed
            
        Raises:
            RuntimeError: If cleanup fails
        """
        await self._ensure_lock()
        
        async with self._lock:
            if self.state == ResourceState.CLOSED and not force:
                self.logger.debug(f"Resource already closed")
                return
            
            if self.state == ResourceState.CLOSING:
                self.logger.warning(f"Resource already closing")
                return
            
            self.state = ResourceState.CLOSING
            
            try:
                if self.cleanup_func and self.resource is not None:
                    if self.async_cleanup:
                        await self.cleanup_func(self.resource)
                    else:
                        self.cleanup_func(self.resource)
                
                self.resource = None
                self.state = ResourceState.CLOSED
                self.logger.info(f"Resource cleaned up")
                
            except Exception as e:
                self.state = ResourceState.ERROR
                self.logger.error(f"Resource cleanup failed: {e}")
                raise
    
    def is_ready(self) -> bool:
        """Check if resource is ready."""
        return self.state == ResourceState.READY
    
    def is_closed(self) -> bool:
        """Check if resource is closed."""
        return self.state == ResourceState.CLOSED


class ResourcePool:
    """
    Pool of managed resources with coordinated lifecycle.
    
    Ensures all resources are cleaned up together, even if some fail.
    Based on best practices for resource management in distributed systems.
    """
    
    def __init__(self, name: str = "ResourcePool"):
        """
        Initialize resource pool.
        
        Args:
            name: Pool name for logging
        """
        self.name = name
        self.resources: Dict[str, ManagedResource] = {}
        self.logger = get_logger(f'ResourcePool.{name}')
        self._cleanup_completed: Set[str] = set()
    
    def register(self, resource: ManagedResource):
        """
        Register resource with pool.
        
        Args:
            resource: ManagedResource to register
        """
        if resource.name in self.resources:
            self.logger.warning(f"Resource {resource.name} already registered")
            return
        
        self.resources[resource.name] = resource
        self.logger.debug(f"Registered resource: {resource.name}")
    
    async def initialize_all(self) -> Dict[str, Any]:
        """
        Initialize all resources in pool.
        
        Returns:
            Dictionary of resource_name -> initialized_resource
            
        Raises:
            RuntimeError: If any resource fails to initialize
        """
        self.logger.info(f"Initializing {len(self.resources)} resources...")
        
        initialized = {}
        failed = []
        
        for name, resource in self.resources.items():
            try:
                result = await resource.initialize()
                initialized[name] = result
                self.logger.debug(f"✓ {name}")
            except Exception as e:
                failed.append((name, e))
                self.logger.error(f"✗ {name}: {e}")
        
        if failed:
            # Cleanup successfully initialized resources
            await self.cleanup_all()
            
            error_msg = f"Failed to initialize {len(failed)} resource(s): " + \
                       ", ".join(f"{name}: {e}" for name, e in failed)
            raise RuntimeError(error_msg)
        
        self.logger.info(f"✅ All {len(self.resources)} resources initialized")
        return initialized
    
    async def cleanup_all(self, timeout: Optional[float] = None):
        """
        Cleanup all resources in pool.
        
        Guarantees all cleanup attempts are made, even if some fail.
        
        Args:
            timeout: Optional timeout for entire cleanup operation
        """
        if not self.resources:
            return
        
        self.logger.info(f"Cleaning up {len(self.resources)} resources...")
        
        cleanup_tasks = []
        for name, resource in self.resources.items():
            if name not in self._cleanup_completed:
                cleanup_tasks.append(self._cleanup_single(name, resource))
        
        if not cleanup_tasks:
            self.logger.debug("All resources already cleaned up")
            return
        
        # Execute all cleanups concurrently
        try:
            if timeout:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=timeout
                )
            else:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        except asyncio.TimeoutError:
            self.logger.error(f"Cleanup timeout after {timeout}s")
        
        # Log summary
        success_count = len(self._cleanup_completed)
        failed_count = len(self.resources) - success_count
        
        if failed_count > 0:
            self.logger.warning(
                f"Cleanup complete: {success_count} succeeded, {failed_count} failed"
            )
        else:
            self.logger.info(f"✅ All {success_count} resources cleaned up")
    
    async def _cleanup_single(self, name: str, resource: ManagedResource):
        """Cleanup single resource with error handling."""
        try:
            await resource.cleanup()
            self._cleanup_completed.add(name)
            self.logger.debug(f"✓ Cleaned up {name}")
        except Exception as e:
            self.logger.error(f"✗ Failed to cleanup {name}: {e}")
    
    def get_status(self) -> Dict[str, str]:
        """
        Get status of all resources.
        
        Returns:
            Dictionary of resource_name -> state
        """
        return {
            name: resource.state.value
            for name, resource in self.resources.items()
        }
    
    def reset(self):
        """Reset cleanup tracking (for testing or restart scenarios)."""
        self._cleanup_completed.clear()


class SessionManager:
    """
    Manages HTTP session lifecycle with guaranteed cleanup.
    
    Prevents common issues:
    - Session leaks from unclosed sessions
    - Multiple session creation race conditions
    - Session reuse after close
    
    Based on aiohttp best practices and PEP 343.
    """
    
    def __init__(self, name: str = "SessionManager"):
        """
        Initialize session manager.
        
        Args:
            name: Name for logging
        """
        self.name = name
        self._session: Optional[Any] = None
        self._lock: Optional[asyncio.Lock] = None
        self._closed = False
        self.logger = get_logger(f'SessionManager.{name}')
    
    async def _ensure_lock(self):
        """Ensure lock is initialized."""
        if self._lock is None:
            self._lock = asyncio.Lock()
    
    async def get_session(self):
        """
        Get or create session (thread-safe).
        
        Returns:
            aiohttp.ClientSession
        """
        await self._ensure_lock()
        
        async with self._lock:
            # Check if closed
            if self._closed:
                raise RuntimeError(
                    f"SessionManager {self.name} is closed, cannot get session"
                )
            
            # Check if session exists and is open
            if self._session is not None:
                if not self._session.closed:
                    return self._session
                else:
                    # Session was closed externally, clean up
                    self.logger.warning("Session was closed externally, creating new one")
                    self._session = None
            
            # Create new session
            import aiohttp
            self._session = aiohttp.ClientSession()
            self.logger.debug("Created new session")
            return self._session
    
    async def close(self):
        """Close session (idempotent)."""
        await self._ensure_lock()
        
        async with self._lock:
            if self._closed:
                self.logger.debug("Session manager already closed")
                return
            
            self._closed = True
            
            if self._session is not None and not self._session.closed:
                await self._session.close()
                self.logger.info("Session closed")
            
            self._session = None
    
    async def __aenter__(self):
        """Context manager entry."""
        return await self.get_session()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper exception handling."""
        close_error = None
        
        try:
            await self.close()
        except Exception as e:
            close_error = e
            self.logger.error(f"Error during cleanup: {e}")
        
        # Handle exception chaining
        if exc_type is not None and close_error is not None:
            # Chain close error to original exception
            if hasattr(exc_val, '__context__'):
                exc_val.__context__ = close_error
            return False  # Propagate original exception
        
        if close_error is not None:
            raise close_error
        
        return False  # Don't suppress exceptions
