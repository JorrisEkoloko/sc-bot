"""Atomic file operations based on ACID principles.

Based on:
- ACID properties (Atomicity, Consistency, Isolation, Durability)
- Wikipedia: ACID (computer science)
- POSIX atomic operations

This module provides atomic file operations to prevent data corruption
and ensure consistency even in the presence of crashes or concurrent access.
"""
import os
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from utils.logger import get_logger


class AtomicFileWriter:
    """
    Atomic file writer using write-then-rename pattern.
    
    Based on POSIX atomic rename operation:
    1. Write to temporary file
    2. Flush and sync to disk
    3. Atomically rename to target file
    
    This ensures either the old file or new file exists, never partial data.
    
    Reference: https://en.wikipedia.org/wiki/ACID
    """
    
    def __init__(self, target_path: Path, logger=None):
        """
        Initialize atomic file writer.
        
        Args:
            target_path: Target file path
            logger: Optional logger instance
        """
        self.target_path = Path(target_path)
        self.logger = logger or get_logger('AtomicFileWriter')
        self._lock: Optional[asyncio.Lock] = None
    
    async def _ensure_lock(self):
        """Ensure lock is initialized."""
        if self._lock is None:
            self._lock = asyncio.Lock()
    
    async def write_json(self, data: Dict[str, Any], indent: int = 2):
        """
        Write JSON data atomically.
        
        Args:
            data: Data to write
            indent: JSON indentation
            
        Raises:
            IOError: If write fails
            json.JSONEncodeError: If data cannot be serialized
        """
        await self._ensure_lock()
        
        async with self._lock:
            # Ensure parent directory exists
            self.target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary file in same directory (ensures same filesystem)
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.target_path.parent,
                prefix=f".{self.target_path.name}.",
                suffix=".tmp"
            )
            
            temp_path = Path(temp_path)
            
            try:
                # Write to temporary file
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=indent, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is on disk
                
                # Atomic rename (POSIX guarantees atomicity)
                temp_path.replace(self.target_path)
                
                self.logger.debug(
                    f"Atomically wrote {len(data)} entries to {self.target_path.name}"
                )
                
            except Exception as e:
                # Cleanup temporary file on error
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass
                
                self.logger.error(f"Atomic write failed: {e}")
                raise
    
    def write_json_sync(self, data: Dict[str, Any], indent: int = 2):
        """
        Write JSON data atomically (synchronous version).
        
        Args:
            data: Data to write
            indent: JSON indentation
            
        Raises:
            IOError: If write fails
            json.JSONEncodeError: If data cannot be serialized
        """
        # Ensure parent directory exists
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in same directory
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.target_path.parent,
            prefix=f".{self.target_path.name}.",
            suffix=".tmp"
        )
        
        temp_path = Path(temp_path)
        
        try:
            # Write to temporary file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename
            temp_path.replace(self.target_path)
            
            self.logger.debug(
                f"Atomically wrote {len(data)} entries to {self.target_path.name}"
            )
            
        except Exception as e:
            # Cleanup temporary file on error
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
            
            self.logger.error(f"Atomic write failed: {e}")
            raise


class AtomicFileReader:
    """
    Atomic file reader with corruption detection.
    
    Provides safe reading with fallback to backup if main file is corrupted.
    """
    
    def __init__(self, file_path: Path, logger=None):
        """
        Initialize atomic file reader.
        
        Args:
            file_path: File path to read
            logger: Optional logger instance
        """
        self.file_path = Path(file_path)
        self.logger = logger or get_logger('AtomicFileReader')
    
    def read_json(self, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Read JSON data with corruption handling.
        
        Args:
            default: Default value if file doesn't exist or is corrupted
            
        Returns:
            Loaded data or default
        """
        if not self.file_path.exists():
            self.logger.debug(f"File not found: {self.file_path.name}")
            return default or {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.debug(
                f"Read {len(data)} entries from {self.file_path.name}"
            )
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Corrupted JSON in {self.file_path.name}: {e}. "
                f"Using default value."
            )
            return default or {}
            
        except Exception as e:
            self.logger.error(f"Failed to read {self.file_path.name}: {e}")
            return default or {}


class TwoFileTracker:
    """
    Two-file tracking system with atomic archival.
    
    Maintains two files:
    - Active file: Current/in-progress items
    - Archive file: Completed/historical items
    
    Provides atomic move from active to archive.
    
    Based on ACID principles and database archival patterns.
    """
    
    def __init__(
        self,
        active_path: Path,
        archive_path: Path,
        logger=None
    ):
        """
        Initialize two-file tracker.
        
        Args:
            active_path: Path to active tracking file
            archive_path: Path to archive file
            logger: Optional logger instance
        """
        self.active_path = Path(active_path)
        self.archive_path = Path(archive_path)
        self.active_writer = AtomicFileWriter(active_path, logger)
        self.archive_writer = AtomicFileWriter(archive_path, logger)
        self.active_reader = AtomicFileReader(active_path, logger)
        self.archive_reader = AtomicFileReader(archive_path, logger)
        self.logger = logger or get_logger('TwoFileTracker')
    
    def load(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load both active and archive data.
        
        Returns:
            Tuple of (active_data, archive_data)
        """
        active = self.active_reader.read_json(default={})
        archive = self.archive_reader.read_json(default={})
        
        self.logger.info(
            f"Loaded {len(active)} active, {len(archive)} archived items"
        )
        
        return active, archive
    
    async def save(
        self,
        active_data: Dict[str, Any],
        archive_data: Dict[str, Any]
    ):
        """
        Save both active and archive data atomically.
        
        Args:
            active_data: Active tracking data
            archive_data: Archive data
        """
        # Save both files (each write is atomic)
        await self.active_writer.write_json(active_data)
        await self.archive_writer.write_json(archive_data)
        
        self.logger.debug(
            f"Saved {len(active_data)} active, {len(archive_data)} archived items"
        )
    
    def save_sync(
        self,
        active_data: Dict[str, Any],
        archive_data: Dict[str, Any]
    ):
        """
        Save both active and archive data atomically (sync version).
        
        Args:
            active_data: Active tracking data
            archive_data: Archive data
        """
        self.active_writer.write_json_sync(active_data)
        self.archive_writer.write_json_sync(archive_data)
        
        self.logger.debug(
            f"Saved {len(active_data)} active, {len(archive_data)} archived items"
        )
    
    async def archive_item(
        self,
        item_key: str,
        active_data: Dict[str, Any],
        archive_data: Dict[str, Any]
    ) -> bool:
        """
        Archive item from active to archive atomically.
        
        Args:
            item_key: Key of item to archive
            active_data: Active data dict (will be modified)
            archive_data: Archive data dict (will be modified)
            
        Returns:
            True if archived successfully
        """
        if item_key not in active_data:
            self.logger.warning(f"Cannot archive {item_key}: not in active data")
            return False
        
        # Move item
        item = active_data[item_key]
        archive_data[item_key] = item
        del active_data[item_key]
        
        # Save both files atomically
        await self.save(active_data, archive_data)
        
        self.logger.info(f"Archived item: {item_key}")
        return True
    
    def check_duplicate(
        self,
        item_key: str,
        active_data: Dict[str, Any],
        archive_data: Dict[str, Any]
    ) -> tuple[bool, Optional[Any]]:
        """
        Check if item is duplicate (deduplication).
        
        Args:
            item_key: Key to check
            active_data: Active data dict
            archive_data: Archive data dict
            
        Returns:
            Tuple of (is_duplicate, archived_item_if_exists)
        """
        # Check active first (true duplicate)
        if item_key in active_data:
            return True, None
        
        # Check archive (fresh start)
        if item_key in archive_data:
            return False, archive_data[item_key]
        
        # First mention
        return False, None
