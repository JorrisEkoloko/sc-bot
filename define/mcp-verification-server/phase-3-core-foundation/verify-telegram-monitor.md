# Verify TelegramMonitor - Phase 3.1

## Component Focus

**TelegramMonitor** - Real-time Telegram message monitoring with multi-channel support

## Endpoints to Verify

### 1. Connection Management

```python
async def connect() -> bool
```

**Verify**:

- ✓ Connects to Telegram API using credentials from .env
- ✓ Returns True on successful connection
- ✓ Returns False on failure
- ✓ Handles authentication flow (phone + 2FA if needed)

**Check Against Current**:

- Compare with `src/telegram/client.py` line 47-75
- Verify same Telethon client initialization
- Confirm session management preserved

### 2. Channel Validation

```python
async def validate_channel_access(channel_id: str) -> bool
```

**Verify**:

- ✓ Tests channel connectivity
- ✓ Verifies message access permissions
- ✓ Returns True if accessible
- ✓ Logs channel info (title, members)

**Check Against Current**:

- Compare with `src/telegram/client.py` line 106-115
- Verify same validation logic

### 3. Message Handling

```python
async def handle_message(event) -> None
```

**Verify**:

- ✓ Extracts message data (id, text, date, views)
- ✓ Adds to message queue
- ✓ Handles missing fields gracefully
- ✓ Logs message receipt

**Check Against Current**:

- Compare with `src/telegram/client.py` line 237-244
- Verify same message_data structure:
  ```python
  {
      'id': message.id,
      'text': message.text,
      'date': message.date,
      'views': getattr(message, 'views', 0),
      'sender_id': message.sender_id
  }
  ```

### 4. Message Queue

```python
async def get_next_message() -> Dict[str, Any]
```

**Verify**:

- ✓ Returns next message from queue
- ✓ Blocks if queue empty (async wait)
- ✓ Returns properly formatted message_data
- ✓ Thread-safe queue operations

## Logic to Validate

### Authentication Flow

```
1. Initialize Telethon client
2. Connect to Telegram
3. Check if user authorized
4. If not authorized:
   - Start authentication with phone
   - Handle 2FA if needed
   - Save session
5. Return connection status
```

**Verify**: Matches `src/telegram/client.py` line 47-95

### Multi-Channel Setup

```
1. Load channels from config
2. For each enabled channel:
   - Get entity from Telegram
   - Validate access
   - Add event handler
   - Store in active_channels list
3. Log total active channels
```

**Verify**: Matches `src/main.py` line 3

50-390

## Integration Points

### With Configuration

- ✓ Reads TELEGRAM_API_ID from config
- ✓ Reads TELEGRAM_API_HASH from config
- ✓ Reads TELEGRAM_PHONE from config
- ✓ Loads channels from config/channels.json

### With MessageProcessor

- ✓ Provides message_data in correct format
- ✓ Queue interface for async processing
- ✓ No direct coupling (queue-based)

### With Error Handler

- ✓ Handles connection errors
- ✓ Handles authentication errors
- ✓ Logs all errors appropriately
- ✓ Graceful degradation on failures

## Success Criteria

### Functional Requirements

- [ ] Connects to Telegram successfully
- [ ] Authenticates with phone number
- [ ] Validates channel access
- [ ] Receives messages in real-time
- [ ] Queues messages properly
- [ ] Handles multiple channels
- [ ] Manages session persistence

### Preservation Requirements

- [ ] All Telethon functionality preserved
- [ ] Same authentication flow as current
- [ ] Same message_data structure
- [ ] Same channel validation logic
- [ ] Same error handling patterns

### Performance Requirements

- [ ] Connection time < 5 seconds
- [ ] Message queue latency < 100ms
- [ ] Handles 100+ messages/minute
- [ ] Memory usage stable over time

## Verification Commands

### Test Connection

```python
from core.telegram_monitor import TelegramMonitor
from config.settings import Config

config = Config()
monitor = TelegramMonitor(config.telegram)
success = await monitor.connect()
assert success == True, "Connection failed"
```

### Test Channel Validation

```python
channel_id = "@erics_calls"  # From your .env
valid = await monitor.validate_channel_access(channel_id)
assert valid == True, f"Channel {channel_id} not accessible"
```

### Test Message Reception

```python
await monitor.start_monitoring()
message = await monitor.get_next_message()
assert 'id' in message, "Message missing id"
assert 'text' in message, "Message missing text"
assert 'views' in message, "Message missing views"
```

## Common Issues

### Issue 1: Authentication Fails

**Symptom**: Connection returns False
**Check**:

- TELEGRAM_API_ID correct in .env
- TELEGRAM_API_HASH correct in .env
- TELEGRAM_PHONE correct format (+1234567890)
  **Fix**: Verify credentials at https://my.telegram.org/apps

### Issue 2: Channel Not Accessible

**Symptom**: validate_channel_access returns False
**Check**:

- Channel ID format (@channel_name or numeric ID)
- Account has access to channel
- Channel is public or account is member
  **Fix**: Join channel or use correct ID

### Issue 3: No Messages Received

**Symptom**: get_next_message blocks forever
**Check**:

- Event handlers registered correctly
- Channel has recent messages
- Message filters not too restrictive
  **Fix**: Verify event handler setup

## Phase Completion

✅ **Ready for Phase 3.2** when:

- All functional requirements met
- All preservation requirements verified
- All performance requirements satisfied
- Integration with MessageProcessor tested
- No critical issues remaining
