"""Cleanup coordinator with guaranteed resource cleanup.

Based on resource management best practices and RAII pattern.
"""
import asyncio
from typing import Dict, Any, Optional
from utils.resource_manager import ResourcePool, ManagedResource
from utils.logger import get_logger


class CleanupCoordinator:
    """
    Coordinates cleanup of all system resources.
    
    Ensures:
    - All resources are cleaned up properly
    - No double-cleanup occurs
    - Failures in one component don't prevent others from cleaning up
    - Proper logging of cleanup status
    
    Based on RAII pattern and resource pool management.
    """
    
    def __init__(self, name: str = "CleanupCoordinator"):
        """
        Initialize cleanup coordinator.
        
        Args:
            name: Coordinator name
        """
        self.name = name
        self.resource_pool = ResourcePool(name)
        self.logger = get_logger(f'CleanupCoordinator.{name}')
    
    def register_component(
        self,
        name: str,
        component: Any,
        cleanup_method: str = "close",
        is_async: bool = True
    ):
        """
        Register component for cleanup.
        
        Args:
            name: Component name
            component: Component instance
            cleanup_method: Name of cleanup method
            is_async: Whether cleanup method is async
        """
        if component is None:
            self.logger.debug(f"Skipping registration of None component: {name}")
            return
        
        # Create cleanup function
        if hasattr(component, cleanup_method):
            cleanup_func = getattr(component, cleanup_method)
            
            resource = ManagedResource(
                name=name,
                cleanup_func=lambda c: cleanup_func(),
                async_cleanup=is_async
            )
            resource.resource = component
            resource.state = resource.state.READY  # Already initialized
            
            self.resource_pool.register(resource)
            self.logger.debug(f"Registered component: {name}")
        else:
            self.logger.warning(
                f"Component {name} has no {cleanup_method} method"
            )
    
    async def cleanup_all(self, timeout: Optional[float] = 30.0):
        """
        Cleanup all registered components.
        
        Args:
            timeout: Timeout for entire cleanup operation
        """
        self.logger.info("Starting coordinated cleanup...")
        
        try:
            await self.resource_pool.cleanup_all(timeout=timeout)
            self.logger.info("✅ Coordinated cleanup complete")
        except Exception as e:
            self.logger.error(f"Cleanup coordination error: {e}")
            raise
    
    def get_status(self) -> Dict[str, str]:
        """Get cleanup status of all components."""
        return self.resource_pool.get_status()
    
    def reset(self):
        """Reset cleanup tracking (for testing)."""
        self.resource_pool.reset()
