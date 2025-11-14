# Symbol Mapping System

## Problem Statement

Different APIs use different symbols for the same token, causing lookup failures and data inconsistencies.

### Example: OPTIMUS AI Token

| API           | Symbol  | Name       | Contract (last 6) | Status      |
| ------------- | ------- | ---------- | ----------------- | ----------- |
| CoinMarketCap | OPTI    | Optimus AI | 2d215d            | ✅ Verified |
| CryptoCompare | OPTI    | -          | -                 | ✅ Verified |
| DexScreener   | OPTIMUS | Optimus    | 2d215d            | ✅ Verified |
| User Input    | OPTIMUS | Optimus AI | -                 | -           |

**Contract Address (Source of Truth):** `0x562e362876c8aee4744fc2c6aac8394c312d215d`

## Solution

A two-part system:

1. **Symbol Mapping Builder** (`build_symbol_mapping.py`) - Discovers and maps symbols across APIs
2. **Symbol Mapper Utility** (`symbol_mapper.py`) - Runtime utility to resolve symbols

## How It Works

### Step 1: Build the Mapping

The builder script:

1. Fetches token lists from CoinGecko (Ethereum, Solana, Base)
2. Searches DexScreener for popular tokens
3. Compares symbols by contract address (the source of truth)
4. Identifies discrepancies
5. Generates `symbol_mapping.json`

```bash
python crypto-intelligence/scripts/build_symbol_mapping.py
```

### Step 2: Use the Mapping

The utility class provides easy access to correct symbols:

```python
from utils.symbol_mapper import SymbolMapper

mapper = SymbolMapper()

# Get symbol for specific API
cmc_symbol = mapper.get_symbol_for_api(
    address="0x562e362876c8aee4744fc2c6aac8394c312d215d",
    api="coinmarketcap"
)
# Returns: "OPTI"

dex_symbol = mapper.get_symbol_for_api(
    address="0x562e362876c8aee4744fc2c6aac8394c312d215d",
    api="dexscreener"
)
# Returns: "OPTIMUS"
```

## Integration with Existing Code

### In CoinMarketCapClient

```python
from utils.symbol_mapper import SymbolMapper

class CoinMarketCapClient:
    def __init__(self):
        self.symbol_mapper = SymbolMapper()
        # ... rest of init

    def get_token_info(self, address: str, user_symbol: str):
        # Get the correct symbol for CoinMarketCap
        cmc_symbol = self.symbol_mapper.get_symbol_for_api(
            address=address,
            api="coinmarketcap",
            fallback_symbol=user_symbol
        )

        # Use cmc_symbol for API call
        return self._fetch_from_api(cmc_symbol)
```

### In HistoricalPriceRetriever

```python
from utils.symbol_mapper import SymbolMapper

class HistoricalPriceRetriever:
    def __init__(self):
        self.symbol_mapper = SymbolMapper()
        # ... rest of init

    def fetch_price(self, address: str, symbol: str, api: str):
        # Get correct symbol for the API being used
        correct_symbol = self.symbol_mapper.get_symbol_for_api(
            address=address,
            api=api,
            fallback_symbol=symbol
        )

        # Use correct_symbol for API call
        return self._fetch_from_api(correct_symbol, api)
```

## Mapping File Structure

```json
{
  "0x562e362876c8aee4744fc2c6aac8394c312d215d": {
    "chain": "ethereum",
    "names": ["Optimus AI", "OPTIMUS", "Optimus"],
    "symbols": {
      "coinmarketcap": "OPTI",
      "cryptocompare": "OPTI",
      "dexscreener": "OPTIMUS",
      "coingecko": "optimus-ai"
    },
    "primary_symbol": "OPTI"
  }
}
```

## API Methods

### SymbolMapper Class

#### `get_symbol_for_api(address, api, chain="ethereum", fallback_symbol=None)`

Get the correct symbol for a specific API.

**Parameters:**

- `address`: Token contract address
- `api`: API name (coinmarketcap, dexscreener, coingecko, etc.)
- `chain`: Blockchain (ethereum, solana, base)
- `fallback_symbol`: Symbol to return if not found

**Returns:** Correct symbol string

#### `get_all_symbols(address, chain="ethereum")`

Get all known symbols across all APIs.

**Returns:** Dictionary mapping API names to symbols

#### `get_primary_symbol(address, chain="ethereum")`

Get the primary (most common) symbol.

**Returns:** Primary symbol string

#### `has_symbol_discrepancy(address, chain="ethereum")`

Check if symbols differ across APIs.

**Returns:** Boolean

## Maintenance

### Updating the Mapping

Run the builder script periodically to keep mappings current:

```bash
# Weekly or when adding new tokens
python crypto-intelligence/scripts/build_symbol_mapping.py
```

### Adding New APIs

To add support for a new API:

1. Update `build_symbol_mapping.py`:

   - Add fetch method for the new API
   - Store symbols with API name as key

2. Use in code:
   ```python
   symbol = mapper.get_symbol_for_api(address, "new_api_name")
   ```

## Benefits

1. **Automatic Resolution**: No manual symbol mapping needed
2. **Centralized**: Single source of truth for symbol discrepancies
3. **Extensible**: Easy to add new APIs
4. **Maintainable**: Simple JSON format
5. **Fallback Support**: Gracefully handles missing mappings

## Common Discrepancies Found

Based on initial analysis, common patterns include:

- **Shortened symbols**: OPTIMUS → OPTI
- **Case differences**: wif → WIF
- **Suffix variations**: PEPE → PEPE2.0
- **Platform prefixes**: BTC → WBTC (wrapped versions)

## Troubleshooting

### Mapping file not found

```
Warning: Symbol mapping file not found at data/symbol_mapping.json
Run build_symbol_mapping.py to generate it.
```

**Solution:** Run the builder script first.

### Symbol not in mapping

The utility will return the fallback_symbol if provided, or None.

**Solution:**

1. Check if address is correct
2. Run builder script to update mappings
3. Manually add to mapping file if needed

### API rate limits

The builder script includes rate limiting (1-2 second delays).

**Solution:** Increase delays in the script if needed.
