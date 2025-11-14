# Design Document - Part 1: Foundation + Basic Message Flow

## Overview

Part 1 implements the foundational pipeline for the crypto intelligence system. The design focuses on establishing a clean, async architecture that connects to Telegram, monitors channels, and displays messages in real-time. This foundation will support all future enhancements while maintaining simplicity and reliability.

## Architecture

### System Components

```
crypto-intelligence/
├── config/
│   ├── settings.py          # Configuration management
│   └── channels.json        # Channel configuration
├── utils/
│   └── logger.py            # Logging system
├── core/
│   └── telegram_monitor.py  # Telegram connection & monitoring
├── main.py                  # System orchestration
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

### Data Flow

```
.env + channels.json
    ↓
Configuration Manager (settings.py)
    ↓
Logger Initialization (logger.py)
    ↓
Telegram Monitor (telegram_monitor.py)
    ↓
Message Events
    ↓
Console Output (main.py)
```

## Components and Interfaces

### 1. Configuration Manager (config/settings.py)

**Purpose**: Load and validate all system configuration from environment variables and JSON files.

**Key Classes**:

- `Config`: Main configuration container
- `TelegramConfig`: Telegram-specific settings
- `ChannelConfig`: Channel configuration

**Interface**:

```python
class Config:
    @classmethod
    def load(cls, env_file: str = '.env') -> 'Config'

    def validate(self) -> tuple[list[str], list[str]]  # (errors, warnings)

    @property
    def telegram(self) -> TelegramConfig

    @property
    def channels(self) -> list[ChannelConfig]

    @property
    def log_level(self) -> str
```

**Configuration Sources**:

1. Environment variables (.env file)

   - TELEGRAM_API_ID
   - TELEGRAM_API_HASH
   - TELEGRAM_PHONE
   - LOG_LEVEL (default: INFO)

2. JSON files (channels.json)
   - Channel list with IDs and names
   - Enable/disable flags per channel

**Validation Rules**:

- TELEGRAM_API_ID must be integer > 0
- TELEGRAM_API_HASH must be 32 characters
- TELEGRAM_PHONE must match pattern: +[0-9]{10,15}
- At least 1 channel must be configured
- Channel IDs must be non-empty strings

### 2. Logger (utils/logger.py)

**Purpose**: Provide centralized logging with console and file output.

**Key Functions**:

- `setup_logger(name: str, level: str) -> logging.Logger`
- `get_logger(name: str) -> logging.Logger`

**Features**:

- Console output with colored formatting
- File output with daily rotation
- Component-specific loggers
- Timestamp on all log entries
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Log Format**:

```
[2024-01-15 10:30:45] [INFO] [TelegramMonitor] Connected to Telegram successfully
[2024-01-15 10:30:46] [INFO] [TelegramMonitor] Monitoring 3 channels
[2024-01-15 10:30:50] [INFO] [Main] Message received from CryptoSignals: "BTC breaking out!"
```

**File Management**:

- Log directory: `logs/`
- File pattern: `crypto_intelligence_YYYY-MM-DD.log`
- Rotation: Daily at midnight
- Retention: 7 days

### 3. Telegram Monitor (core/telegram_monitor.py)

**Purpose**: Connect to Telegram, authenticate, and monitor channels for new messages.

**Key Classes**:

- `TelegramMonitor`: Main monitoring component
- `MessageEvent`: Message data container

**Interface**:

```python
class TelegramMonitor:
    def __init__(self, config: TelegramConfig, channels: list[ChannelConfig])

    async def connect(self) -> bool

    async def start_monitoring(self, message_callback: Callable) -> None

    async def disconnect(self) -> None

    def is_connected(self) -> bool
```

**Connection Flow**:

1. Initialize Telethon client with API credentials
2. Check for existing session file
3. If no session: prompt for phone authentication
4. If 2FA enabled: prompt for 2FA code
5. Save session file for future use
6. Validate access to all configured channels
7. Register message event handlers

**Message Handling**:

- Async event-driven architecture
- Message callback receives: channel_name, message_text, timestamp, message_id
- Non-blocking message processing
- Automatic reconnection on connection loss

**Error Handling**:

- Connection failures: 3 retries with exponential backoff (1s, 2s, 4s)
- Authentication failures: Log error and exit (requires manual intervention)
- Channel access errors: Log warning, continue with accessible channels
- Network errors: Automatic reconnection attempts

### 4. Main Orchestration (main.py)

**Purpose**: Coordinate all components and manage system lifecycle.

**Key Functions**:

- `async def main()`: Main entry point
- `async def handle_message(...)`: Message callback
- `def signal_handler(...)`: Graceful shutdown handler

**Startup Sequence**:

1. Load configuration from .env and channels.json
2. Validate configuration (exit if errors)
3. Initialize logger with configured level
4. Create TelegramMonitor instance
5. Connect to Telegram (with retries)
6. Start monitoring with message callback
7. Log successful startup
8. Run until shutdown signal

**Message Display**:

```python
async def handle_message(channel_name: str, message_text: str,
                        timestamp: datetime, message_id: int):
    """Display received message in console"""
    formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{formatted_time}] [{channel_name}] (ID: {message_id})")
    print(f"{message_text}")
    print("-" * 80)
```

**Shutdown Sequence**:

1. Catch SIGINT (Ctrl+C) or SIGTERM
2. Log shutdown initiation
3. Stop accepting new messages
4. Disconnect from Telegram
5. Flush logger
6. Exit with code 0

## Data Models

### Configuration Models

```python
@dataclass
class TelegramConfig:
    api_id: int
    api_hash: str
    phone: str
    session_name: str = "crypto_scraper_session"

@dataclass
class ChannelConfig:
    id: str          # Username or numeric ID
    name: str        # Display name
    enabled: bool = True

@dataclass
class Config:
    telegram: TelegramConfig
    channels: list[ChannelConfig]
    log_level: str
```

### Message Models

```python
@dataclass
class MessageEvent:
    channel_id: str
    channel_name: str
    message_id: int
    message_text: str
    timestamp: datetime
    sender_id: Optional[int]
```

## Error Handling

### Configuration Errors

- **Missing credentials**: Log error, exit with code 1
- **Invalid format**: Log error with details, exit with code 1
- **Missing channels.json**: Log error, exit with code 1
- **Empty channel list**: Log error, exit with code 1

### Connection Errors

- **Network timeout**: Retry 3 times with backoff
- **Authentication failure**: Log error, exit (requires manual fix)
- **API rate limit**: Wait and retry
- **Session expired**: Delete session file, re-authenticate

### Runtime Errors

- **Channel access denied**: Log warning, skip channel
- **Message parsing error**: Log error, continue monitoring
- **Unexpected exception**: Log full traceback, attempt recovery

### Error Recovery Strategy

1. **Transient errors**: Automatic retry with exponential backoff
2. **Configuration errors**: Fail fast with clear error message
3. **Runtime errors**: Log and continue (graceful degradation)
4. **Critical errors**: Log, cleanup, exit gracefully

## Testing Strategy

### Unit Tests

- Configuration loading and validation
- Logger initialization and output
- Message event parsing
- Error handling logic

### Integration Tests

- End-to-end configuration loading
- Telegram connection with mock client
- Message flow from event to console
- Graceful shutdown sequence

### Manual Verification Tests

1. **Configuration Test**: Verify .env and channels.json load correctly
2. **Connection Test**: Verify Telegram connection succeeds
3. **Authentication Test**: Verify 2FA handling (if enabled)
4. **Channel Test**: Verify all channels are accessible
5. **Message Test**: Verify messages display in console
6. **Shutdown Test**: Verify Ctrl+C shuts down cleanly

### Pipeline Verification

**Success Criteria**:

- System starts without errors
- Logs show "Connected to Telegram successfully"
- Logs show "Monitoring X channels"
- Messages appear in console with proper formatting
- System runs stable for 60+ seconds
- Ctrl+C triggers clean shutdown
- Logs show "Shutdown complete"

## Performance Considerations

### Startup Performance

- Target: < 5 seconds from start to monitoring
- Configuration loading: < 100ms
- Telegram connection: < 3 seconds
- Channel validation: < 1 second

### Runtime Performance

- Message latency: < 1 second from Telegram to console
- Memory usage: < 100MB for monitoring
- CPU usage: < 5% idle, < 20% during message bursts
- No memory leaks during extended operation

### Resource Management

- Single Telegram connection (reused)
- Async I/O for non-blocking operations
- Minimal memory footprint
- Efficient log file rotation

## Security Considerations

### Credential Protection

- .env file in .gitignore
- Session file in .gitignore
- File permissions: 600 for .env and session
- No credentials in logs
- No credentials in error messages

### Session Management

- Session file encrypted by Telethon
- Session reuse to avoid repeated authentication
- Session invalidation on authentication errors
- Secure session file storage

### Network Security

- HTTPS/TLS for all Telegram connections
- No plaintext credential transmission
- Secure token storage
- Connection timeout limits

## Dependencies

### Python Packages (requirements.txt)

```
telethon>=1.34.0        # Telegram client library
python-dotenv>=1.0.0    # Environment variable loading
asyncio>=3.4.3          # Async operations (built-in)
```

### System Requirements

- Python 3.8+
- Internet connection
- Telegram account with API credentials
- Access to monitored channels

## Future Extensibility

This foundation design supports future enhancements:

1. **Message Processing**: Add message_processor.py to pipeline
2. **Data Storage**: Add data output components
3. **Intelligence**: Add analysis components
4. **Monitoring**: Add health checks and metrics
5. **Scaling**: Add message queue for high-volume channels

The async architecture and clean interfaces ensure easy integration of additional components without modifying the foundation.
