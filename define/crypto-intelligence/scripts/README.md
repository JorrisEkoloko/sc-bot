# Scripts

Utility scripts for the crypto intelligence system.

## Historical Scraper

The historical scraper fetches past messages from Telegram channels and processes them through the complete Part 2 pipeline to verify all components work correctly with real data.

### Usage

```bash
# Scrape 100 messages from the first configured channel
python scripts/historical_scraper.py

# Scrape from a specific channel
python scripts/historical_scraper.py --channel @erics_calls

# Scrape a specific number of messages
python scripts/historical_scraper.py --channel @erics_calls --limit 50
```

### What It Does

1. Connects to Telegram using your configured credentials
2. Fetches historical messages from the specified channel
3. Processes each message through the complete pipeline:
   - Extracts engagement metrics
   - Calculates HDRB scores
   - Detects crypto mentions
   - Analyzes sentiment
   - Calculates confidence scores
4. Generates comprehensive statistics
5. Creates a verification report

### Output

The scraper generates a verification report that includes:

- **Summary Statistics**: Total messages, success rate, errors
- **HDRB Score Statistics**: Min, max, average scores
- **Crypto Detection Statistics**: Relevance rate
- **Sentiment Analysis Statistics**: Positive, negative, neutral counts
- **Confidence Statistics**: High confidence rate, average confidence
- **Performance Statistics**: Processing times, performance targets
- **Verification Status**: Pass/fail for all checks

The report is saved to `scripts/verification_report.md` and displayed in the console.

### Example Output

```
================================================================================
HISTORICAL SCRAPER VERIFICATION REPORT
================================================================================

Generated: 2024-11-07 21:30:00

================================================================================
SUMMARY STATISTICS
================================================================================
Total messages fetched: 100
Successfully processed: 100
Processing errors: 0
Success rate: 100.0%

================================================================================
HDRB SCORE STATISTICS
================================================================================
Minimum: 0.00/100
Maximum: 85.50/100
Average: 12.35/100

================================================================================
CRYPTO DETECTION STATISTICS
================================================================================
Crypto relevant messages: 45/100
Crypto relevance rate: 45.0%

================================================================================
SENTIMENT ANALYSIS STATISTICS
================================================================================
Positive: 32
Negative: 18
Neutral: 50

================================================================================
CONFIDENCE STATISTICS
================================================================================
High confidence messages: 15/100
High confidence rate: 15.0%
Average confidence: 0.42

================================================================================
PERFORMANCE STATISTICS
================================================================================
Average processing time: 1.25ms
Minimum processing time: 0.50ms
Maximum processing time: 3.20ms
✓ Performance target met (< 100ms)

================================================================================
VERIFICATION STATUS
================================================================================
✓ Messages processed successfully
✓ HDRB scores calculated
✓ Crypto detection working
✓ Sentiment analysis working
✓ Confidence scores calculated
✓ Performance targets met

Verification: 6/6 checks passed

✓ ALL VERIFICATION CHECKS PASSED!
================================================================================
```

### Requirements

- Telegram connection must be configured (`.env` file)
- At least one channel must be configured in `config/channels.json`
- You must have access to the channel you're scraping

### Notes

- The scraper only processes text messages (skips media-only messages)
- Processing is done sequentially to avoid rate limits
- All logging is output to console and log files
- The verification report is saved for future reference
