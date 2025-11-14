"""Telegram monitoring component."""
import asyncio
from datetime import datetime
from typing import Optional, Callable
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from config.settings import TelegramConfig, ChannelConfig
from domain.message_event import MessageEvent
from utils.logger import setup_logger


class TelegramMonitor:
    """Monitors Telegram channels for new messages."""
    
    def __init__(self, config: TelegramConfig, channels: list[ChannelConfig], log_level: str = 'INFO'):
        """
        Initialize Telegram monitor.
        
        Args:
            config: Telegram API configuration
            channels: List of channels to monitor
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.config = config
        self.channels = [c for c in channels if c.enabled]
        self.logger = setup_logger('TelegramMonitor', log_level)
        
        # Create Telethon client
        self.client = TelegramClient(
            self.config.session_name,
            self.config.api_id,
            self.config.api_hash
        )
        
        self.connected = False
        self.message_callback = None
        self._channel_entities = {}
        self._event_handler = None
        self._monitoring_active = False
        self._callback_failure_count = 0  # Track consecutive callback failures
        self._extraction_failure_count = 0  # Track consecutive extraction failures
        
        # Initialize async locks (will be created in async context)
        self._disconnect_lock = None
        self._monitoring_lock = None
        self._init_lock = None
        self._locks_initialized = False
    
    async def _ensure_locks_initialized(self):
        """Initialize async locks safely."""
        if self._locks_initialized:
            return
        
        # Create init lock in async context if needed
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            # Double-check after acquiring lock
            if self._locks_initialized:
                return
            
            # Create async locks in async context
            self._disconnect_lock = asyncio.Lock()
            self._monitoring_lock = asyncio.Lock()
            self._locks_initialized = True
            self.logger.debug("Async locks initialized")
    
    async def connect(self) -> bool:
        """
        Connect to Telegram and authenticate.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.connected:
            return True
        
        # Initialize locks in async context
        await self._ensure_locks_initialized()
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            client_started = False
            try:
                # Start the client
                await self.client.start(phone=self.config.phone)
                client_started = True
                
                # Check if we're authorized
                if not await self.client.is_user_authorized():
                    self.logger.error("Client not authorized. Please authenticate first.")
                    return False
                
                # Validate channel access BEFORE setting connected state
                await self._validate_channels()
                
                # Only set connected after validation succeeds
                self.connected = True
                return True
                
            except SessionPasswordNeededError:
                self.logger.error(
                    "Two-factor authentication required. Please run authentication separately "
                    "or disable 2FA for this account."
                )
                return False
                    
            except FloodWaitError as e:
                wait_time = e.seconds
                self.logger.warning(f"Flood wait triggered, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                # Continue to next retry
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}, retrying...")
                    wait_time = retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All connection attempts failed. Last error: {e}", exc_info=True)
            
            finally:
                # Always cleanup if we started but didn't succeed
                if client_started and not self.connected:
                    try:
                        await self.client.disconnect()
                    except Exception as cleanup_error:
                        self.logger.debug(f"Cleanup disconnect failed: {cleanup_error}")
        
        return False
    
    async def _validate_channels(self):
        """Validate access to all configured channels."""
        accessible_channels = []
        failed_channels = []
        
        for channel in self.channels:
            try:
                # Get channel entity
                entity = await self.client.get_entity(channel.id)
                self._channel_entities[channel.id] = entity
                accessible_channels.append(channel.name)
                
            except Exception as e:
                failed_channels.append((channel.name, str(e)))
                self.logger.warning(f"Failed to access channel {channel.name}: {e}")
        
        if failed_channels:
            self.logger.warning(f"Failed to access {len(failed_channels)} channels: {failed_channels}")
        
        if not accessible_channels:
            raise RuntimeError(f"No accessible channels - cannot start monitoring. Failed: {failed_channels}")
    
    async def start_monitoring(self, message_callback: Callable):
        """
        Start monitoring channels for new messages.
        
        Args:
            message_callback: Async function to call when message received
        """
        if not self.connected:
            self.logger.warning("Cannot start monitoring: not connected")
            return
        
        # Ensure locks are initialized
        await self._ensure_locks_initialized()
        
        # Protect against concurrent start_monitoring calls
        monitoring_started = False
        async with self._monitoring_lock:
            # Re-check connection state after acquiring lock
            if not self.connected:
                self.logger.warning("Lost connection before monitoring started")
                return
            
            if self._monitoring_active:
                self.logger.warning("Monitoring already active")
                return
            
            self.message_callback = message_callback
            self._callback_failure_count = 0  # Reset failure counter
            self._monitoring_active = True  # Set inside lock
            monitoring_started = True
        
        # Use try-finally to ensure flag is reset if monitoring fails to start
        try:
            pass  # monitoring_active already set inside lock
            
            # Define event handler with separated error zones
            async def handle_new_message(event):
                """Handle new message event."""
                msg_event = None
                
                # Phase 1: Extract message data
                try:
                    # Get channel info
                    chat = await event.get_chat()
                    channel_name = getattr(chat, 'title', 'Unknown')
                    channel_id = str(chat.id) if hasattr(chat, 'id') else 'unknown'
                    
                    # Extract message data
                    message_text = event.message.message or ""
                    message_id = event.message.id
                    timestamp = event.message.date
                    sender_id = event.message.sender_id
                    
                    # Create message event
                    msg_event = MessageEvent(
                        channel_id=channel_id,
                        channel_name=channel_name,
                        message_id=message_id,
                        message_text=message_text,
                        timestamp=timestamp,
                        sender_id=sender_id,
                        message_obj=event.message  # Pass original message for metrics extraction
                    )
                    
                    # Reset extraction failure count on success
                    self._extraction_failure_count = 0
                    
                except Exception as e:
                    self.logger.error(f"Error extracting message data: {e}", exc_info=True)
                    
                    # Track consecutive extraction failures
                    self._extraction_failure_count += 1
                    
                    if self._extraction_failure_count >= 10:
                        self.logger.critical("Too many consecutive extraction failures (10+), stopping monitoring")
                        raise RuntimeError(f"Message extraction failed 10 consecutive times, last error: {e}") from e
                    
                    # Don't return - let it fall through to allow callback error tracking
                
                # Phase 2: Call the callback only if extraction succeeded
                if msg_event and self.message_callback:
                    try:
                        await self.message_callback(msg_event)
                        # Reset failure count on success
                        self._callback_failure_count = 0
                    except asyncio.CancelledError:
                        # Don't count cancellation as failure, propagate it
                        self.logger.info("Message callback cancelled")
                        raise
                    except (MemoryError, SystemError, KeyboardInterrupt) as fatal_error:
                        # Fatal errors - stop immediately
                        self.logger.critical(f"Fatal error in callback: {fatal_error}")
                        raise
                    except Exception as callback_error:
                        # Log but don't stop monitoring for retryable errors
                        self.logger.error(
                            f"Callback error for message {msg_event.message_id} from {msg_event.channel_name}: {callback_error}",
                            exc_info=True
                        )
                        
                        # Track consecutive failures
                        self._callback_failure_count += 1
                        
                        # Log warning but don't block with sleep (prevents message queue backup)
                        if self._callback_failure_count >= 3:
                            self.logger.warning(f"Callback failure count: {self._callback_failure_count}/10")
                        
                        if self._callback_failure_count >= 10:
                            self.logger.critical("Too many consecutive callback failures (10+), stopping monitoring")
                            # Re-raise to stop monitoring loop
                            raise RuntimeError(f"Callback failed 10 consecutive times, last error: {callback_error}") from callback_error
            
            # Register event handler AFTER definition, OUTSIDE the handler
            self._event_handler = self.client.on(
                events.NewMessage(chats=list(self._channel_entities.values()))
            )(handle_new_message)
            
            self.logger.info(f"Monitoring {len(self._channel_entities)} channels")
            
            # Keep the client running (outside the lock)
            try:
                await self.client.run_until_disconnected()
            except asyncio.CancelledError:
                self.logger.info("Monitoring cancelled, shutting down...")
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}", exc_info=True)
        finally:
            # Unregister event handler to prevent memory leaks
            if self._event_handler:
                try:
                    self.client.remove_event_handler(self._event_handler)
                    self._event_handler = None
                    self._monitoring_active = False
                    self.logger.debug("Event handler removed successfully")
                except Exception as e:
                    self.logger.critical(f"Handler removal failed: {e} - may cause duplicate processing")
                    # Keep reference to allow inspection but mark as inactive
                    self._monitoring_active = False
                    # Re-raise to force reconnection
                    raise
            else:
                self._monitoring_active = False
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        # Ensure locks are initialized
        await self._ensure_locks_initialized()
        
        async with self._disconnect_lock:
            if not self.connected:
                return
            
            self.logger.info("Disconnecting from Telegram...")
            try:
                await self.client.disconnect()
                # Only set disconnected after successful disconnect
                self.connected = False
                self.logger.info("Disconnected successfully")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
                # Force disconnected state even on error to prevent retry loops
                self.connected = False
                raise
    
    def is_connected(self) -> bool:
        """Check if connected to Telegram."""
        return self.connected
