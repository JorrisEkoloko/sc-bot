# Requirements Document - Part 3: Address Extraction & Price Tracking

## Introduction

Part 3 transforms processed messages with crypto mentions into actionable intelligence by extracting blockchain addresses, fetching real-time price data from multiple APIs, tracking 7-day ATH performance, and outputting enriched data to CSV and Google Sheets. This builds on Part 2's crypto detection to provide comprehensive price intelligence and performance tracking for identified tokens.

## Glossary

- **Address Extractor**: Component that extracts and validates blockchain addresses from crypto mentions
- **Price Engine**: Multi-API price fetching system with intelligent failover
- **Performance Tracker**: Component that tracks 7-day all-time-high (ATH) price performance
- **Data Output**: Component that writes enriched message data to CSV and Google Sheets
- **Enriched Message**: ProcessedMessage extended with address, price, and performance data
- **Chain Identification**: Process of determining blockchain type from address format
- **API Failover**: Pattern that tries multiple APIs in sequence until success
- **TTL Cache**: Time-to-live cache that stores data for a specified duration
- **Rate Limiter**: Component that enforces API request limits per time period
- **ATH Multiplier**: Ratio of all-time-high price to initial tracking price

## Requirements

### Requirement 1: Address Extraction and Validation

**User Story:** As a system operator, I want blockchain addresses extracted and validated from crypto mentions, so that I can fetch accurate price data for the correct tokens.

#### Acceptance Criteria

1. WHEN a ProcessedMessage contains crypto_mentions, THE Address Extractor SHALL extract all blockchain addresses from the list
2. WHEN an address is extracted, THE Address Extractor SHALL identify the blockchain chain (ethereum, solana, bsc) based on address format
3. WHEN an Ethereum address is detected, THE Address Extractor SHALL validate the address format (0x followed by 40 hexadecimal characters)
4. WHEN a Solana address is detected, THE Address Extractor SHALL validate the address format (base58 encoded, 32-44 characters)
5. WHEN validation completes, THE Address Extractor SHALL return a list of Address objects with address string, chain type, and validation status

### Requirement 2: Multi-API Price Fetching with Failover

**User Story:** As a system operator, I want price data fetched from multiple APIs with automatic failover, so that price fetching remains reliable even when individual APIs fail.

#### Acceptance Criteria

1. WHEN a validated address is received, THE Price Engine SHALL check the cache for existing price data with valid TTL
2. WHERE cached data exists and TTL is valid, THE Price Engine SHALL return cached price data without making API calls
3. WHERE cached data is missing or expired, THE Price Engine SHALL attempt to fetch price from CoinGecko API first
4. IF CoinGecko fails and chain is Solana, THEN THE Price Engine SHALL attempt to fetch price from Birdeye API
5. IF previous APIs fail, THEN THE Price Engine SHALL attempt Moralis API, then DexScreener API in sequence
6. WHEN price data is successfully fetched, THE Price Engine SHALL cache the data with 300-second TTL
7. WHEN all APIs fail, THE Price Engine SHALL log the failure and return None without crashing

### Requirement 3: API Rate Limiting

**User Story:** As a system operator, I want API rate limits enforced, so that the system does not exceed API quotas and get blocked.

#### Acceptance Criteria

1. WHEN making API requests, THE Price Engine SHALL track requests per minute for each API separately
2. WHEN request count approaches API limit, THE Price Engine SHALL delay subsequent requests to stay within limits
3. WHERE CoinGecko limit is 50 requests per minute, THE Price Engine SHALL enforce maximum 45 requests per minute (90% buffer)
4. WHERE Birdeye limit is 60 requests per minute, THE Price Engine SHALL enforce maximum 54 requests per minute (90% buffer)
5. WHERE Moralis limit is 25 requests per minute, THE Price Engine SHALL enforce maximum 22 requests per minute (90% buffer)
6. WHEN rate limit is reached, THE Price Engine SHALL log a warning with API name and wait time

### Requirement 4: Price Data Structure

**User Story:** As a system operator, I want comprehensive price data returned, so that I can analyze token metrics beyond just price.

#### Acceptance Criteria

1. WHEN price data is fetched successfully, THE Price Engine SHALL return PriceData object with price_usd field
2. WHEN available from API, THE Price Engine SHALL include market_cap in PriceData object
3. WHEN available from API, THE Price Engine SHALL include volume_24h in PriceData object
4. WHEN available from API, THE Price Engine SHALL include price_change_24h in PriceData object
5. WHEN PriceData is created, THE Price Engine SHALL record the source API name and timestamp

### Requirement 5: Performance Tracking Initialization

**User Story:** As a system operator, I want new addresses automatically tracked for 7-day performance, so that I can identify high-performing tokens early.

#### Acceptance Criteria

1. WHEN an address receives price data for the first time, THE Performance Tracker SHALL create a new tracking entry
2. WHEN creating tracking entry, THE Performance Tracker SHALL record address, chain, start_price, and start_time
3. WHEN tracking entry is created, THE Performance Tracker SHALL initialize ath_price equal to start_price
4. WHEN tracking entry is created, THE Performance Tracker SHALL initialize ath_time equal to start_time
5. WHEN tracking entry is created, THE Performance Tracker SHALL persist the entry to disk immediately

### Requirement 6: Performance Tracking Updates

**User Story:** As a system operator, I want tracked addresses updated with current prices, so that ATH performance is accurately calculated.

#### Acceptance Criteria

1. WHEN a tracked address receives new price data, THE Performance Tracker SHALL update current_price field
2. WHEN current_price exceeds ath_price, THE Performance Tracker SHALL update ath_price to current_price
3. WHEN ath_price is updated, THE Performance Tracker SHALL update ath_time to current timestamp
4. WHEN price update completes, THE Performance Tracker SHALL calculate ath_multiplier as ath_price divided by start_price
5. WHEN price update completes, THE Performance Tracker SHALL calculate current_multiplier as current_price divided by start_price
6. WHEN any tracking data changes, THE Performance Tracker SHALL persist updated data to disk

### Requirement 7: Performance Data Cleanup

**User Story:** As a system operator, I want old tracking entries removed automatically, so that the system does not accumulate stale data indefinitely.

#### Acceptance Criteria

1. WHEN Performance Tracker starts, THE Performance Tracker SHALL load existing tracking data from disk
2. WHEN cleanup is triggered, THE Performance Tracker SHALL identify entries older than 7 days from start_time
3. WHEN old entries are identified, THE Performance Tracker SHALL remove them from tracking data
4. WHEN entries are removed, THE Performance Tracker SHALL persist updated tracking data to disk
5. WHILE system is running, THE Performance Tracker SHALL execute cleanup every 24 hours

### Requirement 8: CSV Data Output

**User Story:** As a system operator, I want enriched message data written to CSV files, so that I can analyze historical data offline.

#### Acceptance Criteria

1. WHEN an EnrichedMessage is ready for output, THE Data Output SHALL write a row to the current CSV file
2. WHEN writing CSV row, THE Data Output SHALL include all 23 columns in specified order
3. WHERE CSV file does not exist for current date, THE Data Output SHALL create new file with header row
4. WHEN date changes, THE Data Output SHALL rotate to new CSV file with current date in filename
5. WHEN CSV write fails, THE Data Output SHALL log error and continue without crashing

### Requirement 9: Google Sheets Data Output

**User Story:** As a system operator, I want enriched message data written to Google Sheets, so that I can view real-time data in a shareable dashboard.

#### Acceptance Criteria

1. WHEN Google Sheets is enabled in configuration, THE Data Output SHALL authenticate using service account credentials
2. WHEN an EnrichedMessage is ready for output, THE Data Output SHALL append a row to the configured spreadsheet
3. WHEN writing to Google Sheets, THE Data Output SHALL include all 23 columns matching CSV format
4. WHERE Google Sheets write fails, THE Data Output SHALL log error and continue with CSV-only output
5. WHEN spreadsheet is first accessed, THE Data Output SHALL verify header row exists and create if missing

### Requirement 10: Conditional Formatting

**User Story:** As a system operator, I want visual formatting applied to Google Sheets data, so that I can quickly identify high-value signals.

#### Acceptance Criteria

1. WHERE message has is_high_confidence equal to true, THE Data Output SHALL apply green background to the row
2. WHERE message has is_crypto_relevant equal to true, THE Data Output SHALL apply blue text color to crypto_mentions column
3. WHERE message has hdrb_score greater than 50, THE Data Output SHALL apply bold formatting to hdrb_score column
4. WHERE message has ath_multiplier greater than 2.0, THE Data Output SHALL apply gold background to ath_multiplier column
5. WHEN formatting rules are applied, THE Data Output SHALL handle API errors gracefully without blocking data writes

### Requirement 11: Pipeline Integration

**User Story:** As a system operator, I want Part 3 components integrated into the message processing pipeline, so that all crypto-relevant messages are automatically enriched.

#### Acceptance Criteria

1. WHEN a ProcessedMessage is crypto-relevant, THE System SHALL pass the message to Address Extractor
2. WHEN Address Extractor returns addresses, THE System SHALL pass each address to Price Engine
3. WHEN Price Engine returns price data, THE System SHALL pass address and price to Performance Tracker
4. WHEN Performance Tracker returns performance data, THE System SHALL create EnrichedMessage with all data
5. WHEN EnrichedMessage is created, THE System SHALL pass it to Data Output for CSV and Google Sheets writing

### Requirement 12: Configuration Management

**User Story:** As a system operator, I want all Part 3 components configurable via environment variables, so that I can adjust behavior without code changes.

#### Acceptance Criteria

1. WHEN System starts, THE Configuration Manager SHALL load API keys for CoinGecko, Birdeye, and Moralis from environment
2. WHEN System starts, THE Configuration Manager SHALL load Google Sheets credentials path and spreadsheet ID from environment
3. WHEN System starts, THE Configuration Manager SHALL load cache TTL with default value of 300 seconds
4. WHEN System starts, THE Configuration Manager SHALL load performance tracking days with default value of 7
5. WHERE any required configuration is missing, THE Configuration Manager SHALL log error and use safe defaults or disable optional features

### Requirement 13: Error Handling and Resilience

**User Story:** As a system operator, I want comprehensive error handling throughout Part 3, so that individual failures do not crash the entire system.

#### Acceptance Criteria

1. WHEN any API call fails, THE Price Engine SHALL log the error with API name and error details
2. WHEN address validation fails, THE Address Extractor SHALL mark address as invalid and continue processing
3. WHEN price fetching fails for an address, THE System SHALL continue processing other addresses
4. WHEN Google Sheets write fails, THE System SHALL continue with CSV-only output
5. WHEN any component encounters an error, THE System SHALL include error details in EnrichedMessage error field

### Requirement 14: Performance Requirements

**User Story:** As a system operator, I want Part 3 processing to complete quickly, so that the system can handle high-volume message streams.

#### Acceptance Criteria

1. WHEN processing a message with addresses, THE System SHALL complete address extraction within 10 milliseconds
2. WHEN fetching price from cache, THE Price Engine SHALL return data within 1 millisecond
3. WHEN fetching price from API, THE Price Engine SHALL complete within 300 milliseconds per address
4. WHEN updating performance tracking, THE Performance Tracker SHALL complete within 50 milliseconds per address
5. WHEN writing to CSV and Google Sheets, THE Data Output SHALL complete within 150 milliseconds total

### Requirement 15: Data Persistence and Recovery

**User Story:** As a system operator, I want performance tracking data persisted to disk, so that tracking continues across system restarts.

#### Acceptance Criteria

1. WHEN Performance Tracker starts, THE Performance Tracker SHALL load tracking data from JSON file if it exists
2. WHEN tracking data file is corrupted, THE Performance Tracker SHALL log error and start with empty tracking data
3. WHEN any tracking data changes, THE Performance Tracker SHALL save complete tracking data to JSON file
4. WHEN system shuts down, THE Performance Tracker SHALL perform final save of tracking data
5. WHERE data directory does not exist, THE Performance Tracker SHALL create the directory before saving

### Requirement 16: Automatic Historical Scraping for New Channels

**User Story:** As a system operator, I want new channels to be automatically scraped for historical messages on first run, so that the system has immediate data and context before monitoring real-time messages.

#### Acceptance Criteria

1. WHEN System starts, THE System SHALL check if each enabled channel has been previously scraped
2. WHERE channel has not been scraped, THE System SHALL fetch historical messages from the channel before starting real-time monitoring
3. WHEN fetching historical messages, THE System SHALL process a configurable number of messages (default: 100) through the complete pipeline
4. WHEN historical scraping completes, THE System SHALL mark the channel as scraped in persistent storage
5. WHERE channel has been previously scraped, THE System SHALL skip historical scraping and start real-time monitoring immediately
6. WHEN historical scraping fails, THE System SHALL log error and continue with real-time monitoring
7. WHILE historical scraping is in progress, THE System SHALL log progress updates every 10 messages
