"""Bootstrap status data model for progress tracking.

Task 5: Progress persistence for resumability after crashes.
MCP-Validated: Checkpoint/restart pattern from Wikipedia.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BootstrapStatus:
    """Progress tracking for historical bootstrap process.
    
    Enables resumability: If bootstrap crashes, resume from last checkpoint.
    """
    # Progress tracking
    total_messages: int = 0
    processed_messages: int = 0
    total_tokens: int = 0
    processed_tokens: int = 0
    
    # Outcome tracking
    successful_outcomes: int = 0
    failed_outcomes: int = 0
    api_calls_made: int = 0
    
    # Checkpoint data
    last_processed_message_id: Optional[int] = None
    last_processed_timestamp: Optional[datetime] = None
    last_checkpoint_time: Optional[datetime] = None
    
    # Metadata
    channel_name: str = ""
    started_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_messages': self.total_messages,
            'processed_messages': self.processed_messages,
            'total_tokens': self.total_tokens,
            'processed_tokens': self.processed_tokens,
            'successful_outcomes': self.successful_outcomes,
            'failed_outcomes': self.failed_outcomes,
            'api_calls_made': self.api_calls_made,
            'last_processed_message_id': self.last_processed_message_id,
            'last_processed_timestamp': self.last_processed_timestamp.isoformat() if self.last_processed_timestamp else None,
            'last_checkpoint_time': self.last_checkpoint_time.isoformat() if self.last_checkpoint_time else None,
            'channel_name': self.channel_name,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BootstrapStatus':
        """Create from dictionary."""
        return cls(
            total_messages=data.get('total_messages', 0),
            processed_messages=data.get('processed_messages', 0),
            total_tokens=data.get('total_tokens', 0),
            processed_tokens=data.get('processed_tokens', 0),
            successful_outcomes=data.get('successful_outcomes', 0),
            failed_outcomes=data.get('failed_outcomes', 0),
            api_calls_made=data.get('api_calls_made', 0),
            last_processed_message_id=data.get('last_processed_message_id'),
            last_processed_timestamp=datetime.fromisoformat(data['last_processed_timestamp']) if data.get('last_processed_timestamp') else None,
            last_checkpoint_time=datetime.fromisoformat(data['last_checkpoint_time']) if data.get('last_checkpoint_time') else None,
            channel_name=data.get('channel_name', ''),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
        )
