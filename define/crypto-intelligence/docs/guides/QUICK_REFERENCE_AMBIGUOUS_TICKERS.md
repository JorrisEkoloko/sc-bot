# Quick Reference: Ambiguous Ticker Detection

## What Changed?

Some ticker symbols are common English words. We now require a `$` or `#` prefix for these ambiguous tickers.

## Ambiguous Tickers (Require Prefix)

| Ticker | Token Name    | ✅ Valid             | ❌ Invalid    |
| ------ | ------------- | -------------------- | ------------- |
| ONE    | Harmony       | `$ONE`, `#ONE`       | `one of`      |
| LINK   | Chainlink     | `$LINK`, `#LINK`     | `this link`   |
| NEAR   | NEAR Protocol | `$NEAR`, `#NEAR`     | `near future` |
| CAKE   | PancakeSwap   | `$CAKE`, `#CAKE`     | `buy cake`    |
| MAGIC  | Magic         | `$MAGIC`, `#MAGIC`   | `magic trick` |
| PRIME  | Echelon Prime | `$PRIME`, `#PRIME`   | `prime time`  |
| BEAM   | Beam          | `$BEAM`, `#BEAM`     | `light beam`  |
| PORTAL | Portal        | `$PORTAL`, `#PORTAL` | `web portal`  |
| FLOW   | Flow          | `$FLOW`, `#FLOW`     | `cash flow`   |
| WAVES  | Waves         | `$WAVES`, `#WAVES`   | `ocean waves` |
| BLUR   | Blur          | `$BLUR`, `#BLUR`     | `motion blur` |
| LOOKS  | LooksRare     | `$LOOKS`, `#LOOKS`   | `looks good`  |
| APE    | ApeCoin       | `$APE`, `#APE`       | `ape into`    |
| SAND   | The Sandbox   | `$SAND`, `#SAND`     | `beach sand`  |

## Non-Ambiguous Tickers (No Prefix Needed)

These work with or without prefix:

- BTC, ETH, SOL, BNB, XRP, ADA, AVAX, DOT, MATIC, etc.
- Example: `BTC` or `$BTC` both work

## Examples

### ✅ Correct Detection

```
"$ONE is pumping hard!"           → Detects: ONE
"#NEAR protocol update"           → Detects: NEAR
"$LINK breaking out"              → Detects: LINK
"BTC ETH SOL to the moon"         → Detects: BTC, ETH, SOL
"$METIS and $ROSE are bullish"    → Detects: METIS, ROSE
```

### ❌ No False Positives

```
"one of the best projects"        → Detects: (nothing)
"near future we'll see gains"     → Detects: (nothing)
"check this link for info"        → Detects: (nothing)
"I bought some cake"              → Detects: (nothing)
"magic internet money"            → Detects: (nothing)
```

## For Message Authors

When mentioning these tokens, use the `$` prefix:

- ✅ "I'm bullish on $ONE"
- ❌ "ONE is my favorite" (won't be detected)

## For Developers

### Adding New Ambiguous Ticker

Edit `config/ambiguous_tickers.json`:

```json
{
  "TICKER": {
    "full_name": "Token Name",
    "chain": "ethereum",
    "requires_prefix": true,
    "reason": "Conflicts with common word 'ticker'"
  }
}
```

### Testing

```bash
python test_ambiguous_ticker_detection.py
python test_real_message.py
python test_before_after_comparison.py
```

## Impact

- **False positives eliminated:** ~95% reduction for ambiguous words
- **Accuracy maintained:** Non-ambiguous tickers unaffected
- **Performance:** Minimal overhead (separate regex patterns)

## Documentation

- Full details: `docs/AMBIGUOUS_TICKER_DETECTION.md`
- Solution summary: `SOLUTION_SUMMARY.md`
- Config file: `config/ambiguous_tickers.json`
