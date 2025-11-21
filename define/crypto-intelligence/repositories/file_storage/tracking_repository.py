"""Performance tracking data persistence.

Pure data access layer for loading and saving tracking data.

FIXED: Issue #15 - Async/Sync Boundary Conflicts
- Removed automatic async/sync detection that creates orphaned tasks
- Enforces explicit async vs sync method usage
- Uses AtomicFileWriter for guaranteed data consistency

Based on:
- PEP 492: Coroutines with async and await syntax
- ACID properties: Atomic file operations
"""
import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import setup_logger
from utils.atomic_operations import AtomicFileWriter, AtomicFileReader
from utils.async_helpers import AsyncSyncBoundary


class TrackingRepository:
    """Pure data access for performance tracking - no business logic."""
    
    def __init__(self, data_dir: str = "data/performance", logger=None):
        """
        Initialize tracking repository.
        
        Args:
            data_dir: Directory for storing tracking data
            logger: Optional logger instance
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.tracking_file = self.data_dir / "tracking.json"
        self.logger = logger or setup_logger('TrackingRepository')
        
        # Use atomic file operations (ACID compliance)
        self.writer = AtomicFileWriter(self.tracking_file, logger)
        self.reader = AtomicFileReader(self.tracking_file, logger)
        
        # Locks for thread-safe operations
        self._async_save_lock = None  # Initialized in async context
        self._sync_save_lock = threading.Lock()
    
    def save(self, tracking_data: Dict[str, Any]) -> None:
        """
        Save tracking data to JSON file (synchronous only).
        
        FIXED: Issue #15 - Enforces sync-only context
        Uses AtomicFileWriter for ACID compliance.
        
        Args:
            tracking_data: Dictionary of tracking data
            
        Raises:
            RuntimeError: If called from async context
        """
        # Enforce sync context (PEP 492 compliance)
        AsyncSyncBoundary.require_sync_context("TrackingRepository.save")
        
        # Use threading lock for sync context
        with self._sync_save_lock:
            try:
                # Use atomic writer (ACID compliance)
                self.writer.write_json_sync(tracking_data)
            except Exception as e:
                self.logger.error(f"Failed to save tracking data: {e}")
                raise
    
    async def _ensure_async_lock(self):
        """Ensure async lock is initialized in async context."""
        if self._async_save_lock is None:
            self._async_save_lock = asyncio.Lock()
    
    async def save_async(self, tracking_data: Dict[str, Any]) -> None:
        """
        Save tracking data to JSON file (async, thread-safe).
        
        FIXED: Issue #15 - Proper async implementation
        Uses AtomicFileWriter with executor for non-blocking I/O.
        
        Args:
            tracking_data: Dictionary of tracking data
        """
        await self._ensure_async_lock()
        
        async with self._async_save_lock:
            try:
                # Use atomic writer (ACID compliance)
                await self.writer.write_json(tracking_data)
            except Exception as e:
                self.logger.error(f"Failed to save tracking data: {e}")
                raise
    
    def load(self) -> Dict[str, Any]:
        """
        Load tracking data from JSON file.
        
        FIXED: Uses AtomicFileReader for corruption detection.
        
        Returns:
            Dictionary of tracking data
        """
        return self.reader.read_json(default={})
    
    def get_file_path(self) -> Path:
        """Get the path to the tracking file."""
        return self.tracking_file
