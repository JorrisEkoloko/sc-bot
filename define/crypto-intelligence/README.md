# Crypto Intelligence System - Parts 1, 2 & 3

Real-time cryptocurrency signal monitoring with HDRB scoring, crypto detection, sentiment analysis, confidence scoring, address extraction, multi-API price fetching, 7-day ATH performance tracking, and multi-table data output (CSV + Google Sheets).

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Telegram API

1. Get your Telegram API credentials from https://my.telegram.org/auth
2. Copy `.env.example` to `.env`
3. Fill in your credentials:

```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
LOG_LEVEL=INFO

# Part 2: Message Processing Configuration
CONFIDENCE_THRESHOLD=0.7
HDRB_MAX_IC=1000.0
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY=1.0

# Part 3: Price Engine Configuration
COINGECKO_API_KEY=your_coingecko_key
BIRDEYE_API_KEY=your_birdeye_key
MORALIS_API_KEY=your_moralis_key
PRICE_CACHE_TTL=300

# Part 3: Performance Tracking
PERFORMANCE_TRACKING_DAYS=7
PERFORMANCE_DATA_DIR=data/performance

# Part 3: Data Output
CSV_OUTPUT_DIR=output
GOOGLE_SHEETS_ENABLED=false
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Part 3: Historical Scraper (Task 5)
HISTORICAL_SCRAPER_ENABLED=true
HISTORICAL_SCRAPER_MESSAGE_LIMIT=100
```

### 3. Configure Channels

Edit `config/channels.json` to add channels you want to monitor:

```json
{
  "channels": [
    {
      "id": "@channel_username",
      "name": "Channel Display Name",
      "enabled": true
    }
  ]
}
```

## Running the System

```bash
python main.py
```

On first run, you'll need to:

1. Enter the authentication code sent to your Telegram
2. If 2FA is enabled, enter your password

The system will then:

- Connect to Telegram
- Validate channel access
- Display live messages from monitored channels

## Stopping the System

Press `Ctrl+C` to gracefully shutdown the system.

## Verification

Successful startup shows:

```
✅ Configuration loaded successfully
✅ Processing config: confidence_threshold=0.7
✅ Retry config: max_attempts=3
✅ Message processor initialized
✅ Connected to Telegram successfully
✅ Monitoring X channels
✅ Message monitoring started
```

Messages will appear in console with enhanced output:

```
================================================================================
[2024-11-07 14:32:15] [Eric Cryptomans Journal] (ID: 12345)
================================================================================
📊 HDRB Score: 67.5/100 (IC: 675.0)
   Engagement: 50 forwards, 300 reactions, 25 replies

💰 Crypto Mentions: BTC, ETH

📈 Sentiment: Positive (+0.75)

🎯 Confidence: 🟢 HIGH (0.82)

BTC and ETH looking strong! Breakout incoming 🚀
Targets: BTC $100k, ETH $5k

⏱️  Processed in 23ms
================================================================================
```

## Logs

Log files are stored in `logs/` directory with daily rotation.

## Features

### Part 1: Foundation + Basic Message Flow ✅

- ✅ Configuration management (env + JSON)
- ✅ Logging system (console + file)
- ✅ Telegram connection with authentication
- ✅ Multi-channel monitoring
- ✅ Message display in console
- ✅ Graceful shutdown

### Part 2: Message Processing + HDRB Scoring ✅

- ✅ **HDRB Scoring**: Research-based formula IC = forwards + (2 × reactions) + (0.5 × replies)
- ✅ **Crypto Detection**: Detects 24+ major tickers (BTC, ETH, SOL, etc.) and contract addresses
- ✅ **Sentiment Analysis**: Classifies messages as positive, negative, or neutral
- ✅ **Confidence Scoring**: Holistic confidence calculation with weighted components
- ✅ **Error Handling**: Retry logic with exponential backoff and circuit breaker
- ✅ **Enhanced Console Output**: Rich display with emojis and visual indicators

### Part 3: Address Extraction & Price Intelligence ✅

- ✅ **Address Extraction**: Validates EVM (Ethereum, BSC, Polygon, etc.) and Solana addresses
- ✅ **Multi-API Price Engine**: Fetches prices from 5 APIs with intelligent failover (CoinGecko, Birdeye, Moralis, DefiLlama, DexScreener)
- ✅ **Aggressive Caching**: 5-minute TTL cache reduces API calls by 80%
- ✅ **Rate Limiting**: Token bucket algorithm enforces API limits
- ✅ **7-Day ATH Tracking**: Monitors all-time-high performance since first mention
- ✅ **Multi-Table Data Output**: 4 separate tables (MESSAGES, TOKEN_PRICES, PERFORMANCE, HISTORICAL)
- ✅ **CSV + Google Sheets**: Dual output with conditional formatting
- ✅ **Automatic Historical Scraping**: Scrapes 100 historical messages on first startup for immediate context

## Architecture

```
crypto-intelligence/
├── config/
│   ├── settings.py                      # Configuration management
│   ├── price_config.py                  # Part 3: Price engine config
│   ├── performance_config.py            # Part 3: Performance tracking config
│   ├── output_config.py                 # Part 3: Data output config
│   ├── historical_scraper_config.py     # Part 3: Historical scraper config
│   └── channels.json                    # Channel configuration
├── core/
│   ├── telegram_monitor.py              # Telegram connection & monitoring
│   ├── message_processor.py             # Message processing coordinator
│   ├── crypto_detector.py               # Cryptocurrency detection
│   ├── sentiment_analyzer.py            # Sentiment analysis
│   ├── address_extractor.py             # Part 3: Address extraction & validation
│   ├── price_engine.py                  # Part 3: Multi-API price fetching
│   ├── performance_tracker.py           # Part 3: 7-day ATH tracking
│   ├── data_output.py                   # Part 3: Multi-table data output
│   ├── historical_scraper.py            # Part 3: Automatic historical scraping
│   └── api_clients/                     # Part 3: API client implementations
│       ├── coingecko_client.py
│       ├── birdeye_client.py
│       ├── moralis_client.py
│       ├── defillama_client.py
│       └── dexscreener_client.py
├── utils/
│   ├── logger.py                        # Logging system
│   └── error_handler.py                 # Error handling & retry logic
├── data/
│   ├── performance/                     # Part 3: Performance tracking data
│   └── scraped_channels.json            # Part 3: Scraped channels tracking
├── output/                              # Part 3: CSV output directory
│   └── YYYY-MM-DD/                      # Daily CSV files
│       ├── messages.csv
│       ├── token_prices.csv
│       ├── performance.csv
│       └── historical.csv
├── scripts/
│   └── historical_scraper.py            # Manual historical scraper for testing
├── main.py                              # System orchestration
└── requirements.txt                     # Dependencies
```

## Configuration Options

### Processing Configuration

- `CONFIDENCE_THRESHOLD`: Threshold for high-confidence classification (default: 0.7)
- `HDRB_MAX_IC`: Maximum IC value for normalization (default: 1000.0)
- `MIN_MESSAGE_LENGTH`: Minimum message length to process (default: 10)
- `MAX_PROCESSING_TIME_MS`: Maximum processing time target (default: 100.0)

### Retry Configuration

- `MAX_RETRY_ATTEMPTS`: Maximum retry attempts for failed operations (default: 3)
- `RETRY_BASE_DELAY`: Base delay for exponential backoff (default: 1.0)
- `RETRY_EXPONENTIAL_BASE`: Exponential base for backoff calculation (default: 2.0)
- `RETRY_JITTER`: Enable jitter to prevent thundering herd (default: true)

## Performance

- Message processing: < 100ms per message
- HDRB calculation: < 10ms
- Crypto detection: < 20ms
- Sentiment analysis: < 20ms
- Confidence calculation: < 5ms

## Verification

### Historical Scraper

To verify the complete Part 2 pipeline with real historical data:

```bash
# Scrape 100 messages from configured channel
python scripts/historical_scraper.py

# Scrape from specific channel
python scripts/historical_scraper.py --channel @erics_calls --limit 50
```

The scraper will:

- Fetch historical messages from Telegram
- Process through complete pipeline
- Generate comprehensive statistics
- Create verification report in `scripts/verification_report.md`

See `scripts/README.md` for detailed usage instructions.

## Part 3 Data Output

The system outputs data to 4 separate tables in both CSV and Google Sheets:

### 1. MESSAGES Table (8 columns)

- message_id, timestamp, channel_name, message_text
- hdrb_score, crypto_mentions, sentiment, confidence

### 2. TOKEN_PRICES Table (9 columns)

- address, chain, symbol, price_usd, market_cap
- volume_24h, price_change_24h, liquidity_usd, pair_created_at

### 3. PERFORMANCE Table (10 columns)

- address, chain, first_message_id, start_price, start_time
- ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked

### 4. HISTORICAL Table (8 columns)

- address, chain, all_time_ath, all_time_ath_date, distance_from_ath
- all_time_atl, all_time_atl_date, distance_from_atl

## Automatic Historical Scraping

On first startup, the system automatically:

1. Checks which channels have been scraped before
2. Fetches 100 historical messages from new channels
3. Processes them through the complete pipeline
4. Marks channels as scraped in `data/scraped_channels.json`
5. Skips already-scraped channels on subsequent startups

This provides immediate data context before real-time monitoring begins.

## Next Steps

Ready for Part 4: Intelligence Layer (Market Analysis, Channel Reputation, Signal Scoring)
