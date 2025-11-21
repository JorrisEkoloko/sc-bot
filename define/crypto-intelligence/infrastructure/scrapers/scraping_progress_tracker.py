"""Scraping progress tracker - manages scraping status and persistence."""
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

from utils.logger import get_logger


class ScrapingStatus(Enum):
    """Status of channel scraping."""
    PENDING = "pending"
    COMPLETED = "completed"
    EMPTY = "empty"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapingProgressTracker:
    """
    Tracks and persists scraping progress for channels.
    
    Responsibilities:
    - Load/save scraping status
    - Track completed channels
    - Persist progress to disk
    - Provide scraping statistics
    """
    
    def __init__(self, scraped_channels_file: str, logger=None):
        """
        Initialize progress tracker.
        
        Args:
            scraped_channels_file: Path to scraped channels JSON file
            logger: Optional logger instance
        """
        self.scraped_channels_file = Path(scraped_channels_file)
        self.logger = logger or get_logger('ScrapingProgressTracker')
        self.scraped_channels = self._load_scraped_channels()
    
    def _load_scraped_channels(self) -> set:
        """
        Load list of previously scraped channels.
        
        Returns:
            Set of channel IDs that have been successfully scraped
        """
        if not self.scraped_channels_file.exists():
            self.logger.info("No scraped channels file found, starting fresh")
            return set()
        
        try:
            with open(self.scraped_channels_file, 'r') as f:
                data = json.load(f)
                channels_data = data.get('channels', {})
                completed_channels = {
                    channel_id for channel_id, info in channels_data.items()
                    if info.get('status') in [ScrapingStatus.COMPLETED.value, ScrapingStatus.EMPTY.value]
                }
                self.logger.info(f"Loaded {len(completed_channels)} previously scraped channels")
                return completed_channels
        except Exception as e:
            self.logger.error(f"Error loading scraped channels: {e}")
            return set()
    
    def save_channel_status(
        self,
        channel_id: str,
        status: ScrapingStatus,
        message_count: int = 0,
        error: Optional[str] = None
    ):
        """
        Save channel scraping status to disk.
        
        Args:
            channel_id: Channel ID
            status: Scraping status
            message_count: Number of messages processed
            error: Error message if failed
        """
        try:
            # Create directory if needed
            self.scraped_channels_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing data
            channels_data = {}
            if self.scraped_channels_file.exists():
                try:
                    with open(self.scraped_channels_file, 'r') as f:
                        existing = json.load(f)
                        channels_data = existing.get('channels', {})
                except Exception:
                    pass
            
            # Update channel status
            channels_data[channel_id] = {
                'status': status.value,
                'last_attempt': datetime.now().isoformat(),
                'message_count': message_count,
                'error': error
            }
            
            # Save to file
            with open(self.scraped_channels_file, 'w') as f:
                json.dump({
                    'channels': channels_data,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            
            # Update in-memory set if completed
            if status in [ScrapingStatus.COMPLETED, ScrapingStatus.EMPTY]:
                self.scraped_channels.add(channel_id)
            
            self.logger.debug(f"Saved status for channel {channel_id}: {status.value}")
        except Exception as e:
            self.logger.error(f"Error saving channel status: {e}")
    
    def is_channel_scraped(self, channel_id: str) -> bool:
        """
        Check if channel has been successfully scraped.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            True if channel has been scraped
        """
        return channel_id in self.scraped_channels
    
    def get_channel_status(self, channel_id: str) -> Optional[Dict]:
        """
        Get detailed status for a channel.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Dictionary with channel status or None
        """
        if not self.scraped_channels_file.exists():
            return None
        
        try:
            with open(self.scraped_channels_file, 'r') as f:
                data = json.load(f)
                channels_data = data.get('channels', {})
                return channels_data.get(channel_id)
        except Exception as e:
            self.logger.error(f"Error getting channel status: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """
        Get scraping statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.scraped_channels_file.exists():
            return {
                'total_channels': 0,
                'completed': 0,
                'empty': 0,
                'failed': 0,
                'pending': 0
            }
        
        try:
            with open(self.scraped_channels_file, 'r') as f:
                data = json.load(f)
                channels_data = data.get('channels', {})
                
                stats = {
                    'total_channels': len(channels_data),
                    'completed': 0,
                    'empty': 0,
                    'failed': 0,
                    'pending': 0
                }
                
                for info in channels_data.values():
                    status = info.get('status', 'pending')
                    if status in stats:
                        stats[status] += 1
                
                return stats
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    def mark_channel_completed(self, channel_id: str, message_count: int):
        """Mark channel as completed."""
        status = ScrapingStatus.COMPLETED if message_count > 0 else ScrapingStatus.EMPTY
        self.save_channel_status(channel_id, status, message_count)
    
    def mark_channel_failed(self, channel_id: str, error: str):
        """Mark channel as failed."""
        self.save_channel_status(channel_id, ScrapingStatus.FAILED, error=error)
