# Timeout Configuration Guide

## Overview

The signal processing service includes configurable timeouts for async operations to prevent blocking and ensure system responsiveness. These timeouts can be adjusted based on your environment and API performance.

## Configuration Options

### 1. Historical Price Timeout

**Environment Variable**: `HISTORICAL_PRICE_TIMEOUT`  
**Default**: `30.0` seconds  
**Location**: `config/processing_config.py`

Controls the maximum time to wait for historical price data fetches when processing old messages (>1 hour old).

**When to adjust:**
- **Increase** if you have slow API connections or frequently see timeout warnings
- **Decrease** if you want faster processing and can tolerate missing historical data
- **Recommended range**: 15-60 seconds

**Example:**
```bash
# .env file
HISTORICAL_PRICE_TIMEOUT=45.0  # Wait up to 45 seconds
```

### 2. OHLC Fetch Timeout

**Environment Variable**: `OHLC_FETCH_TIMEOUT`  
**Default**: `20.0` seconds  
**Location**: `config/processing_config.py`

Controls the maximum time to wait for OHLC (Open-High-Low-Close) data fetches when updating ATH data for signals older than 7 days.

**When to adjust:**
- **Increase** if OHLC fetches frequently timeout
- **Decrease** for faster processing with less complete data
- **Recommended range**: 10-30 seconds

**Example:**
```bash
# .env file
OHLC_FETCH_TIMEOUT=25.0  # Wait up to 25 seconds
```

## Usage in Code

The timeouts are automatically loaded from environment variables and used throughout the signal processing service:

```python
from config.processing_config import ProcessingConfig

# Load configuration
config = ProcessingConfig.load_from_env()

# Use in async operations
historical_price = await asyncio.wait_for(
    fetch_historical_price(...),
    timeout=config.historical_price_timeout
)
```

## Monitoring Timeouts

The system logs timeout events with detailed information:

```
⏱️  Historical entry price fetch TIMED OUT after 30000ms (timeout: 30.0s)
⏱️  OHLC ATH update TIMED OUT after 20000ms (timeout: 20.0s), skipping
```

**What to do if you see frequent timeouts:**

1. **Check API performance**: Verify your API keys are valid and rate limits aren't exceeded
2. **Increase timeout values**: Adjust the environment variables
3. **Check network connectivity**: Ensure stable internet connection
4. **Review API quotas**: Some APIs have daily/monthly limits

## Performance Impact

### Historical Price Timeout
- **Affects**: Messages older than 1 hour
- **Fallback**: Uses current price if timeout occurs
- **Impact**: Minimal - only affects entry price accuracy for old messages

### OHLC Fetch Timeout
- **Affects**: Signals older than 7 days
- **Fallback**: Uses known ATH from price data
- **Impact**: Moderate - may miss accurate ATH data for older signals

## Best Practices

1. **Start with defaults**: The default values (30s and 20s) work well for most setups
2. **Monitor logs**: Watch for timeout warnings in production
3. **Adjust gradually**: Increase timeouts by 5-10 seconds at a time
4. **Balance speed vs accuracy**: Longer timeouts = more accurate data but slower processing
5. **Environment-specific**: Use different values for dev/staging/production

## Example Configurations

### Fast Processing (Less Accurate)
```bash
HISTORICAL_PRICE_TIMEOUT=15.0
OHLC_FETCH_TIMEOUT=10.0
```

### Balanced (Default)
```bash
HISTORICAL_PRICE_TIMEOUT=30.0
OHLC_FETCH_TIMEOUT=20.0
```

### Maximum Accuracy (Slower)
```bash
HISTORICAL_PRICE_TIMEOUT=60.0
OHLC_FETCH_TIMEOUT=30.0
```

## Related Configuration

These timeout settings work alongside other processing configurations:

- `CONFIDENCE_THRESHOLD`: Minimum confidence for signal processing
- `MAX_PROCESSING_TIME_MS`: Maximum time per message
- `QUEUE_MESSAGES_PER_SECOND`: Global rate limit

See `.env.example` for complete configuration options.

## Troubleshooting

### Problem: Frequent timeouts for historical prices
**Solution**: 
- Increase `HISTORICAL_PRICE_TIMEOUT` to 45-60 seconds
- Check CryptoCompare/TwelveData API status
- Verify API keys are valid

### Problem: OHLC fetches always timeout
**Solution**:
- Increase `OHLC_FETCH_TIMEOUT` to 30 seconds
- Check if symbols are valid (invalid symbols cause slow lookups)
- Verify historical data APIs are accessible

### Problem: Processing is too slow
**Solution**:
- Decrease timeout values to 15-20 seconds
- Accept that some historical data may be missing
- Focus on real-time signals instead of historical backfill

## Implementation Details

**File**: `crypto-intelligence/services/orchestration/signal_processing_service.py`

The timeouts are applied using `asyncio.wait_for()`:

```python
try:
    result = await asyncio.wait_for(
        async_operation(),
        timeout=self.processing_config.historical_price_timeout
    )
except asyncio.TimeoutError:
    # Graceful fallback
    result = None
```

This ensures:
- ✅ Non-blocking operation
- ✅ Graceful degradation
- ✅ Detailed logging
- ✅ System continues processing other signals
