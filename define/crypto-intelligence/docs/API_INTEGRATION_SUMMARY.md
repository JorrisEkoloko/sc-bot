# API Integration Summary

## Overview

The crypto intelligence system now integrates **7 external APIs** with intelligent failover and data enrichment strategies.

## Integrated APIs

### 1. **CoinGecko** (Primary Price Source)

- **Purpose**: Price, market cap, volume, historical data
- **Rate Limit**: 50 req/min (demo key)
- **Key Feature**: Fast price endpoint (`/simple/token_price`)
- **Limitation**: Doesn't return symbol in simple endpoint
- **Cost**: Free tier available

### 2. **Birdeye** (Solana Specialist)

- **Purpose**: Solana token prices and metadata
- **Rate Limit**: 60 req/min
- **Key Feature**: Best for Solana ecosystem
- **Cost**: API key required

### 3. **Moralis** (Multi-chain)

- **Purpose**: EVM chain prices and NFT data
- **Rate Limit**: 25 req/min
- **Key Feature**: Multi-chain support
- **Cost**: API key required

### 4. **DefiLlama** (DeFi Focus)

- **Purpose**: DeFi protocol prices
- **Rate Limit**: ~100 req/min (conservative)
- **Key Feature**: No API key required
- **Cost**: Free

### 5. **DexScreener** (DEX Aggregator)

- **Purpose**: DEX pair data, liquidity, volume
- **Rate Limit**: 300 req/min
- **Key Feature**: Real-time DEX data, no API key
- **Limitation**: Only indexes liquid pairs (>$10K liquidity typically)
- **Cost**: Free

### 6. **Blockscout** (Blockchain Explorer) ⭐ NEW

- **Purpose**: Token metadata from blockchain
- **Rate Limit**: 10 req/sec
- **Key Feature**: Indexes ALL on-chain tokens (no liquidity threshold)
- **Use Case**: Fallback for low-liquidity tokens
- **Cost**: Free

### 7. **GoPlus Labs** (Security Analysis) ⭐ NEW

- **Purpose**: Token security analysis and metadata
- **Rate Limit**: ~90 req/min (conservative)
- **Key Features**:
  - Honeypot detection
  - Buy/sell tax analysis
  - Holder count
  - DEX liquidity info
  - Contract security flags
- **Use Case**: Final fallback for symbol + security validation
- **Cost**: Free

## Data Enrichment Strategy

### Price Fetching Flow

```
1. Try primary APIs for price (CoinGecko → Moralis → DefiLlama → DexScreener)
   ↓
2. If price found but symbol missing:
   ↓
3. Try DexScreener for enrichment (symbol, market cap, volume, liquidity)
   ↓
4. If symbol still missing (EVM chains):
   ↓
5. Try Blockscout for symbol (reads from blockchain)
   ↓
6. If symbol STILL missing (all chains):
   ↓
7. Try GoPlus for symbol (final fallback)
```

### Why This Strategy Works

**Example: TOR Token (0x21e133e07b6cb3ff846b5a32fa9869a1e5040da1)**

| API         | Result                                 | Reason                                 |
| ----------- | -------------------------------------- | -------------------------------------- |
| CoinGecko   | ✅ Price: $0.000457<br>❌ Symbol: null | Uses fast endpoint without symbol      |
| DexScreener | ❌ No data                             | Pair not indexed (low liquidity: $18K) |
| Blockscout  | ✅ Symbol: TOR                         | Reads directly from blockchain         |
| GoPlus      | ✅ Symbol: TOR<br>✅ Security: Safe    | Comprehensive token analysis           |

**Final Result**: `coingecko+blockscout` source with complete data

## API Comparison Matrix

| Feature                  | CoinGecko              | DexScreener | Blockscout | GoPlus |
| ------------------------ | ---------------------- | ----------- | ---------- | ------ |
| **Price**                | ✅                     | ✅          | ❌         | ❌     |
| **Symbol**               | ⚠️ (separate endpoint) | ✅          | ✅         | ✅     |
| **Market Cap**           | ✅                     | ✅          | ❌         | ❌     |
| **Volume**               | ✅                     | ✅          | ❌         | ❌     |
| **Liquidity**            | ❌                     | ✅          | ❌         | ✅     |
| **Holder Count**         | ❌                     | ❌          | ✅         | ✅     |
| **Security Analysis**    | ❌                     | ❌          | ❌         | ✅     |
| **Honeypot Detection**   | ❌                     | ❌          | ❌         | ✅     |
| **Low Liquidity Tokens** | ✅                     | ❌          | ✅         | ✅     |
| **API Key Required**     | ✅                     | ❌          | ❌         | ❌     |

## Configuration Files

### Chain Mappings

1. **DexScreener**: `config/dexscreener_chain_mapping.json`

   - Maps generic chain names to DexScreener chain IDs
   - Example: `"ethereum" → "ethereum"`

2. **Blockscout**: `config/blockscout_chain_mapping.json`

   - Maps generic chain names to Blockscout base URLs
   - Example: `"ethereum" → "https://blockscout.com/eth/mainnet"`

3. **GoPlus**: `config/goplus_chain_mapping.json`
   - Maps generic chain names to numeric chain IDs
   - Example: `"ethereum" → "1"`

## Rate Limiting

All APIs use rate limiters with 90% buffer:

```python
rate_limiters = {
    'coingecko': 50 req/min,
    'birdeye': 60 req/min,
    'moralis': 25 req/min,
    'defillama': 100 req/min,
    'dexscreener': 300 req/min,
    'blockscout': 10 req/sec (9 with buffer),
    'goplus': 90 req/min,
    'cryptocompare': 55 req/min
}
```

## Testing

### Test Files

1. `test_blockscout.py` - Test Blockscout client
2. `test_goplus.py` - Test GoPlus client
3. `test_price_engine_blockscout.py` - Test Blockscout integration
4. `test_all_apis.py` - Test complete multi-API flow

### Run Tests

```bash
# Test individual APIs
python test_blockscout.py
python test_goplus.py

# Test full integration
python test_all_apis.py
```

## Benefits of Multi-API Strategy

1. **Resilience**: If one API fails, others provide fallback
2. **Completeness**: Combine data from multiple sources
3. **Coverage**: Handle both high-liquidity and low-liquidity tokens
4. **Security**: Validate tokens with GoPlus security analysis
5. **Cost**: Mix of free and paid APIs optimizes cost

## Use Cases

### High-Liquidity Token

- CoinGecko provides price
- DexScreener provides symbol + liquidity
- Result: Fast, complete data

### Low-Liquidity Token

- CoinGecko provides price
- DexScreener has no data (not indexed)
- Blockscout provides symbol (from blockchain)
- GoPlus provides security validation
- Result: Complete data even for obscure tokens

### Scam Detection

- GoPlus flags honeypots
- System can warn users or skip processing
- Prevents wasted API calls on malicious tokens

## Future Enhancements

1. **Add CoinGecko `/coins/{platform}/contract/{address}` endpoint** for symbol in one call
2. **Cache security analysis** from GoPlus (rarely changes)
3. **Add more chains** to mapping files as needed
4. **Implement circuit breaker** for consistently failing APIs
5. **Add metrics** to track which APIs are most reliable

## Conclusion

The 7-API integration provides robust, comprehensive token data with intelligent failover. The addition of Blockscout and GoPlus fills critical gaps for low-liquidity tokens and security validation.
