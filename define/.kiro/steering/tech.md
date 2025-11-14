# Technical Stack

## Language & Runtime

- **Python 3.8+**: Primary language for all components
- **Async/Await**: Asyncio-based architecture for concurrent operations

## Core Libraries & Frameworks

### Telegram Integration

- **Telethon**: Telegram client library for real-time message monitoring
- Session management with persistent authentication

### Data Processing

- **Pandas**: Data manipulation and CSV operations
- **gspread**: Google Sheets API integration
- **oauth2client**: Google service account authentication

### API & Networking

- **aiohttp**: Async HTTP client for API calls
- **requests**: Synchronous HTTP fallback
- Rate limiting and caching (TTLCache with 5-minute TTL)

### Intelligence & Analysis

- **NLTK/TextBlob**: Sentiment analysis
- **Regex patterns**: Multi-chain address extraction
- Custom HDRB scoring model (research-compliant)

## Architecture Patterns

### Component Structure

```
core/                    # 6 core components
intelligence/            # 3 intelligence modules
config/                  # Unified configuration
utils/                   # Shared utilities
```

### Design Principles

- **Event-driven**: Message queue-based processing
- **Failover**: Multi-API with intelligent fallback
- **Modular**: Clear component boundaries with single responsibilities
- **Async-first**: Non-blocking I/O for all external operations

## Configuration Management

- **Environment Variables**: `.env` file for credentials
- **JSON Config**: `channels.json` for channel configuration
- **Unified Config Class**: Single source of truth for all settings

## Data Storage

- **CSV Files**: Primary data persistence
- **Google Sheets**: Real-time dashboard output
- **JSON Files**: Tracking data and channel reputation
- **Session Files**: Telegram authentication persistence

## API Integrations

1. **CoinGecko**: Primary price data (50 req/min)
2. **Birdeye**: Solana-focused data (60 req/min)
3. **Moralis**: Multi-chain data (25 req/min)
4. **DexScreener**: DEX price data (no key required)
5. **Telegram API**: Real-time message streaming

## Common Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run system
python main.py

# Run with specific config
python main.py --config config/production.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific component tests
pytest tests/test_telegram_monitor.py

# Run with coverage
pytest --cov=core --cov=intelligence tests/
```

### Validation

```bash
# Validate environment setup
python scripts/validate_env.py

# Check API credentials
python scripts/check_apis.py

# Verify channel access
python scripts/verify_channels.py
```

## Performance Targets

- **Message Processing**: <60 seconds end-to-end
- **API Calls**: 2-5 per message (vs 500-1000 in old system)
- **Memory**: Optimized with proper cleanup
- **Uptime**: 99%+ availability target
