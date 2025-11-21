"""Message queue infrastructure."""
from .priority_message_queue import PriorityMessageQueue, PrioritizedMessage

__all__ = ['PriorityMessageQueue', 'PrioritizedMessage']
