"""Performance tracking data persistence.

Pure data access layer for loading and saving tracking data.
"""
import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import setup_logger


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
        
        # Locks for thread-safe operations
        self._async_save_lock = None  # Initialized in async context
        self._sync_save_lock = threading.Lock()
    
    def save(self, tracking_data: Dict[str, Any]) -> None:
        """
        Save tracking data to JSON file (synchronous).
        
        Args:
            tracking_data: Dictionary of tracking data
        """
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in async context - warn and schedule async version
            self.logger.warning("save() called in async context, use save_async() instead")
            
            # Create task with error handling
            task = asyncio.create_task(self.save_async(tracking_data))
            
            def handle_save_error(future):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Async save failed: {e}")
            
            task.add_done_callback(handle_save_error)
            return
        except RuntimeError:
            # No running loop - safe to proceed with sync save
            pass
        
        # Use threading lock for sync context
        with self._sync_save_lock:
            try:
                # Write to temporary file first for atomic operation
                temp_file = self.tracking_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(tracking_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                temp_file.replace(self.tracking_file)
                self.logger.debug(f"Saved tracking data with {len(tracking_data)} entries")
            except (IOError, OSError) as e:
                self.logger.error(f"Failed to save tracking data (I/O error): {e}")
                raise
            except json.JSONEncodeError as e:
                self.logger.error(f"Failed to encode tracking data to JSON: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error saving tracking data: {e}")
                raise
    
    async def _ensure_async_lock(self):
        """Ensure async lock is initialized in async context."""
        if self._async_save_lock is None:
            self._async_save_lock = asyncio.Lock()
    
    async def save_async(self, tracking_data: Dict[str, Any]) -> None:
        """
        Save tracking data to JSON file (async, thread-safe).
        
        Args:
            tracking_data: Dictionary of tracking data
        """
        await self._ensure_async_lock()
        
        async with self._async_save_lock:
            try:
                # Write to temporary file first for atomic operation
                temp_file = self.tracking_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(tracking_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                temp_file.replace(self.tracking_file)
                self.logger.debug(f"Saved tracking data with {len(tracking_data)} entries")
            except (IOError, OSError) as e:
                self.logger.error(f"Failed to save tracking data (I/O error): {e}")
                raise
            except json.JSONEncodeError as e:
                self.logger.error(f"Failed to encode tracking data to JSON: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error saving tracking data: {e}")
                raise
    
    def load(self) -> Dict[str, Any]:
        """
        Load tracking data from JSON file.
        
        Returns:
            Dictionary of tracking data
        """
        if not self.tracking_file.exists():
            self.logger.debug("No tracking file found, starting fresh")
            return {}
        
        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.debug(f"Loaded tracking data with {len(data)} entries")
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Corrupted tracking data file: {e}. Starting fresh.")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load tracking data: {e}")
            return {}
    
    def get_file_path(self) -> Path:
        """Get the path to the tracking file."""
        return self.tracking_file
