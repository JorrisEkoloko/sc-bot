"""Message event domain model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class MessageEvent:
    """Container for message event data."""
    channel_id: str
    channel_name: str
    message_id: int
    message_text: str
    timestamp: datetime
    sender_id: Optional[int]
    message_obj: Optional[Any] = None  # Original Telethon message object for metrics extraction
