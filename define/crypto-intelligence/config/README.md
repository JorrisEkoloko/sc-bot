# Configuration Files

## crypto_patterns.json

This file contains all cryptocurrency detection and sentiment analysis patterns used by the message processor.

### Structure

```json
{
  "tickers": {
    "major": [...]  // List of cryptocurrency ticker symbols
  },
  "address_patterns": {
    "ethereum": {...},  // Ethereum address regex pattern
    "solana": {...}     // Solana address regex pattern
  },
  "sentiment_indicators": {
    "positive": [...],  // Positive sentiment keywords
    "negative": [...]   // Negative sentiment keywords
  }
}
```

### Tickers

Currently tracking **40 major cryptocurrencies**:

- Layer 1: BTC, ETH, SOL, ADA, DOT, AVAX, NEAR, FTM, ALGO, ICP, etc.
- DeFi: UNI, LINK, MATIC, ARB, OP, etc.
- Meme coins: DOGE, SHIB, PEPE, WIF, BONK, etc.
- Stablecoins: USDT, USDC, DAI, BUSD

**To add a new ticker:**

1. Open `crypto_patterns.json`
2. Add the ticker symbol to the `tickers.major` array
3. Save the file
4. Restart the application (patterns are loaded at startup)

### Address Patterns

**Ethereum Addresses:**

- Pattern: `0x[a-fA-F0-9]{40}`
- Format: 0x followed by 40 hexadecimal characters
- Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0`

**Solana Addresses:**

- Pattern: `\b[1-9A-HJ-NP-Za-km-z]{32,44}\b`
- Format: Base58 encoded, 32-44 characters, no 0OIl
- Example: `7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`

### Sentiment Indicators

**Positive Indicators (29 patterns):**

- Bullish terms: moon, bullish, pump, breakout, rally, surge, etc.
- Action terms: buy, long, accumulate, hodl, etc.
- Emojis: 🚀, 📈
- Descriptors: strong, green, gains, profit, etc.

**Negative Indicators (28 patterns):**

- Bearish terms: dump, bearish, crash, rug, scam, etc.
- Action terms: sell, short, exit, avoid, etc.
- Emojis: 📉
- Descriptors: weak, red, loss, dead, etc.

**To add new sentiment indicators:**

1. Open `crypto_patterns.json`
2. Add keywords to `sentiment_indicators.positive` or `sentiment_indicators.negative`
3. Save the file
4. Restart the application

### Benefits of JSON Configuration

✅ **Easy Maintenance**: Update tickers and patterns without touching code
✅ **Version Control**: Track changes to patterns over time
✅ **Non-Developer Friendly**: Anyone can update the ticker list
✅ **Documentation**: Patterns include descriptions and examples
✅ **Flexibility**: Add new patterns or modify existing ones easily
✅ **Testing**: Easy to test with different pattern sets

### Usage in Code

The patterns are automatically loaded by:

- `CryptoDetector` class (loads tickers and address patterns)
- `SentimentAnalyzer` class (loads sentiment indicators)

```python
# Patterns are loaded automatically
detector = CryptoDetector()  # Loads from config/crypto_patterns.json
analyzer = SentimentAnalyzer()  # Loads from config/crypto_patterns.json

# Custom patterns file (optional)
detector = CryptoDetector(patterns_file="custom_patterns.json")
```

### Fallback Behavior

If `crypto_patterns.json` is not found or contains errors:

- **CryptoDetector**: Falls back to BTC, ETH, SOL only
- **SentimentAnalyzer**: Falls back to basic patterns (moon, bullish, pump, dump, bearish, crash)
- Warning is logged but system continues to operate

### Performance

- Patterns are loaded once at initialization
- Regex patterns are compiled for efficient matching
- No performance impact from JSON loading during message processing
- Typical processing time: < 1ms per message
