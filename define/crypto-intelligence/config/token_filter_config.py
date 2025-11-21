"""Configuration for token filtering system.

Adjust these values to control which tokens are filtered out.
"""

# Minimum market cap for regular tokens (not major tokens like ETH/BTC)
# Default: $10,000
# Lower values will allow smaller cap tokens (more risky)
# Higher values will filter out more tokens (more conservative)
# Set to 0 to disable market cap filtering (will process all tokens with valid price)
MIN_MARKET_CAP = 0  # Changed from 10_000 to catch all tokens

# Minimum price for any token
# Default: $0.000001
# Tokens below this price are considered invalid/dead
MIN_PRICE = 0.000001

# Enable/disable market commentary detection
# If True, messages like "ETH rally coming" will be skipped
# If False, all messages will be processed
ENABLE_COMMENTARY_DETECTION = True

# Enable/disable token filtering
# If True, scam tokens and low market cap tokens will be filtered
# If False, all tokens will be processed (not recommended)
ENABLE_TOKEN_FILTERING = True

# Allow tokens with missing market cap data
# If True, tokens without market cap data will be processed (if they have valid price)
# If False, tokens without market cap data will be filtered out
ALLOW_MISSING_MARKET_CAP = True

# Major token price thresholds
# These prevent processing scam tokens with major token symbols
MAJOR_TOKEN_THRESHOLDS = {
    "ETH": {
        "min_price": 1000.0,
        "min_market_cap": 100_000_000,
    },
    "BTC": {
        "min_price": 10000.0,
        "min_market_cap": 1_000_000_000,
    },
    "SOL": {
        "min_price": 10.0,
        "min_market_cap": 10_000_000_000,
    },
    "USDC": {
        "min_price": 0.95,
        "max_price": 1.05,
        "min_market_cap": 10_000_000_000,
    },
    "USDT": {
        "min_price": 0.95,
        "max_price": 1.05,
        "min_market_cap": 50_000_000_000,
    }
}

# Logging verbosity for filtering
# 0 = Minimal (only show filtered counts)
# 1 = Normal (show filtering decisions)
# 2 = Verbose (show all filtering details)
FILTER_LOG_LEVEL = 1
