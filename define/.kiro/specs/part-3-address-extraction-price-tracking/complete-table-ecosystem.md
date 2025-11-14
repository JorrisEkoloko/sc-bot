# Complete Multi-Table Ecosystem

## Current Architecture (4 Tables)

```
┌─────────────────────────────────────────────────────────────┐
│                   CRYPTO INTELLIGENCE                        │
│                   Multi-Table System                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MESSAGES   │    │ TOKEN_PRICES │    │ PERFORMANCE  │
│  (8 columns) │    │  (9 columns) │    │ (10 columns) │
│              │    │              │    │              │
│ Append-only  │    │ Update/Insert│    │ Update/Insert│
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  HISTORICAL  │
                    │  (8 columns) │
                    │              │
                    │ Update/Insert│
                    └──────────────┘
```

---

## Future Ecosystem (14+ Tables)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CRYPTO INTELLIGENCE ECOSYSTEM                         │
│                         Multi-Table System                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  CORE TRACKING  │      │   ANALYTICS     │      │  RISK & ALERTS  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                           │                           │
        │                           │                           │
┌───────┴────────┐      ┌───────────┴────────┐      ┌──────────┴──────────┐
│                │      │                    │      │                     │
▼                ▼      ▼                    ▼      ▼                     ▼

MESSAGES      TOKEN_PRICES    ROI_ANALYSIS    CHANNEL_REP    LIQUIDITY_EVENTS
(8 cols)      (9 cols)        (10 cols)       (12 cols)      (9 cols)

PERFORMANCE   HISTORICAL      TRADING_SIGNALS  ALERTS_LOG     WHALE_ACTIVITY
(10 cols)     (8 cols)        (13 cols)       (9 cols)       (10 cols)

                              PORTFOLIO        SOCIAL_SENT    MARKET_COND
                              (11 cols)        (11 cols)      (10 cols)

                              CORRELATION
                              (8 cols)
```

---

## Table Relationships

### Core Data Flow

```
Message Arrives
    ↓
MESSAGES (store message)
    ↓
Extract Addresses
    ↓
    ├─→ TOKEN_PRICES (current price)
    │       ↓
    ├─→ PERFORMANCE (7-day ATH tracking)
    │       ↓
    ├─→ HISTORICAL (all-time context)
    │       ↓
    └─→ LIQUIDITY_EVENTS (safety check)
            ↓
        ALERTS_LOG (if suspicious)
```

### Analytics Flow

```
PERFORMANCE (tracking complete)
    ↓
ROI_ANALYSIS (calculate outcome)
    ↓
CHANNEL_REPUTATION (update metrics)
    ↓
TRADING_SIGNALS (generate new signals)
```

### Risk Management Flow

```
TOKEN_PRICES (price update)
    ↓
    ├─→ LIQUIDITY_EVENTS (check liquidity)
    ├─→ WHALE_ACTIVITY (check large movements)
    └─→ SOCIAL_SENTIMENT (check sentiment)
            ↓
        ALERTS_LOG (if risk detected)
```

---

## Complete Table Catalog

### 1. MESSAGES (Core) ✅ Implemented

**Purpose:** Store all crypto-relevant messages  
**Columns:** 8  
**Pattern:** Append-only  
**Key:** message_id

```
message_id, timestamp, channel_name, message_text,
hdrb_score, crypto_mentions, sentiment, confidence
```

---

### 2. TOKEN_PRICES (Core) ✅ Implemented

**Purpose:** Current market data for tokens  
**Columns:** 9  
**Pattern:** Update or insert  
**Key:** address

```
address, chain, symbol, price_usd, market_cap,
volume_24h, price_change_24h, liquidity_usd, pair_created_at
```

---

### 3. PERFORMANCE (Core) ✅ Implemented

**Purpose:** 7-day ATH performance tracking  
**Columns:** 10  
**Pattern:** Update or insert  
**Key:** address

```
address, chain, first_message_id, start_price, start_time,
ath_since_mention, ath_time, ath_multiplier, current_multiplier, days_tracked
```

---

### 4. HISTORICAL (Core) ✅ Implemented

**Purpose:** All-time ATH/ATL context  
**Columns:** 8  
**Pattern:** Update or insert  
**Key:** address

```
address, chain, all_time_ath, all_time_ath_date, distance_from_ath,
all_time_atl, all_time_atl_date, distance_from_atl
```

---

### 5. ROI_ANALYSIS (Analytics) ⭐⭐⭐⭐⭐

**Purpose:** Track completed trades and outcomes  
**Columns:** 10  
**Pattern:** Update or insert  
**Key:** address + channel_name (composite)

```
address, channel_name, entry_date, exit_date, entry_price,
exit_price, roi_percent, hold_duration_days, trade_status, profit_loss_usd
```

**Queries:**

```sql
-- Best performing channels
SELECT channel_name, AVG(roi_percent) as avg_roi
FROM roi_analysis
WHERE trade_status = 'completed'
GROUP BY channel_name
ORDER BY avg_roi DESC

-- Optimal hold duration
SELECT hold_duration_days, AVG(roi_percent) as avg_roi
FROM roi_analysis
GROUP BY hold_duration_days
ORDER BY avg_roi DESC
```

---

### 6. CHANNEL_REPUTATION (Analytics) ⭐⭐⭐⭐⭐

**Purpose:** Channel performance metrics  
**Columns:** 12  
**Pattern:** Update or insert  
**Key:** channel_name

```
channel_name, total_signals, successful_signals, success_rate,
average_roi, total_profit_usd, best_roi, worst_roi,
avg_hold_duration, last_updated, tier_performance, reputation_score
```

**Queries:**

```sql
-- Top channels by success rate
SELECT channel_name, success_rate, average_roi, total_signals
FROM channel_reputation
WHERE total_signals >= 10
ORDER BY success_rate DESC, average_roi DESC

-- Channel tier performance
SELECT tier_performance, AVG(success_rate) as avg_success
FROM channel_reputation
GROUP BY tier_performance
```

---

### 7. TRADING_SIGNALS (Analytics) ⭐⭐⭐⭐

**Purpose:** Actionable trading signals  
**Columns:** 13  
**Pattern:** Update or insert  
**Key:** signal_id

```
signal_id, timestamp, address, chain, signal_type, entry_price,
target_price, stop_loss, confidence, channel_name, status,
actual_outcome, notes
```

**Queries:**

```sql
-- Active signals by confidence
SELECT * FROM trading_signals
WHERE status = 'active'
ORDER BY confidence DESC

-- Signal accuracy by channel
SELECT channel_name,
       COUNT(*) as total,
       SUM(CASE WHEN actual_outcome = 'success' THEN 1 ELSE 0 END) as successful
FROM trading_signals
WHERE status = 'completed'
GROUP BY channel_name
```

---

### 8. ALERTS_LOG (Risk) ⭐⭐⭐⭐

**Purpose:** System alerts and notifications  
**Columns:** 9  
**Pattern:** Append-only  
**Key:** alert_id

```
alert_id, timestamp, alert_type, severity, address, channel_name,
message, action_taken, resolved
```

**Queries:**

```sql
-- Recent critical alerts
SELECT * FROM alerts_log
WHERE severity = 'critical'
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC

-- Alert frequency by type
SELECT alert_type, COUNT(*) as count
FROM alerts_log
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY alert_type
```

---

### 9. LIQUIDITY_EVENTS (Risk) ⭐⭐⭐⭐

**Purpose:** Liquidity changes and rug pull detection  
**Columns:** 9  
**Pattern:** Append-only  
**Key:** address + timestamp (composite)

```
address, chain, timestamp, liquidity_before, liquidity_after,
change_percent, event_type, is_suspicious, alert_triggered
```

**Queries:**

```sql
-- Suspicious liquidity drops
SELECT * FROM liquidity_events
WHERE is_suspicious = true
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY change_percent ASC

-- Liquidity health by token
SELECT address,
       AVG(liquidity_after) as avg_liquidity,
       COUNT(CASE WHEN is_suspicious THEN 1 END) as suspicious_events
FROM liquidity_events
GROUP BY address
```

---

### 10. WHALE_ACTIVITY (Risk) ⭐⭐⭐⭐

**Purpose:** Large holder movements  
**Columns:** 10  
**Pattern:** Append-only  
**Key:** address + whale_address + timestamp (composite)

```
address, chain, timestamp, whale_address, transaction_type,
amount, amount_usd, percentage_of_supply, impact_on_price, alert_level
```

**Queries:**

```sql
-- Recent whale movements
SELECT * FROM whale_activity
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND alert_level IN ('high', 'critical')
ORDER BY amount_usd DESC

-- Whale accumulation patterns
SELECT address,
       SUM(CASE WHEN transaction_type = 'buy' THEN amount ELSE 0 END) as total_bought,
       SUM(CASE WHEN transaction_type = 'sell' THEN amount ELSE 0 END) as total_sold
FROM whale_activity
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY address
```

---

### 11. SOCIAL_SENTIMENT (Context) ⭐⭐⭐

**Purpose:** Multi-platform sentiment aggregation  
**Columns:** 11  
**Pattern:** Update or insert  
**Key:** address + timestamp (hourly)

```
address, symbol, timestamp, twitter_sentiment, telegram_sentiment,
reddit_sentiment, overall_sentiment, mention_volume, trending_score,
sentiment_change_24h, alert_triggered
```

**Queries:**

```sql
-- Trending tokens by sentiment
SELECT address, symbol, overall_sentiment, mention_volume
FROM social_sentiment
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY trending_score DESC

-- Sentiment divergence (contrarian indicator)
SELECT address,
       overall_sentiment,
       (SELECT roi_percent FROM roi_analysis WHERE roi_analysis.address = social_sentiment.address) as actual_roi
FROM social_sentiment
WHERE overall_sentiment < -0.5  -- Very negative
  AND actual_roi > 50  -- But performed well
```

---

### 12. MARKET_CONDITIONS (Context) ⭐⭐⭐

**Purpose:** Overall market context  
**Columns:** 10  
**Pattern:** Append-only (hourly)  
**Key:** timestamp

```
timestamp, btc_price, eth_price, market_cap_total, volume_24h_total,
fear_greed_index, trending_narrative, market_phase, volatility_index,
risk_level
```

**Queries:**

```sql
-- Current market conditions
SELECT * FROM market_conditions
ORDER BY timestamp DESC
LIMIT 1

-- Market phase performance
SELECT mc.market_phase, AVG(ra.roi_percent) as avg_roi
FROM market_conditions mc
JOIN roi_analysis ra ON DATE(ra.entry_date) = DATE(mc.timestamp)
GROUP BY mc.market_phase
```

---

### 13. PORTFOLIO_TRACKING (Management) ⭐⭐⭐

**Purpose:** Position management  
**Columns:** 11  
**Pattern:** Update or insert  
**Key:** position_id

```
position_id, address, entry_date, entry_price, quantity,
current_value, unrealized_pnl, realized_pnl, position_status,
allocation_percent, last_updated
```

**Queries:**

```sql
-- Current portfolio value
SELECT SUM(current_value) as total_value,
       SUM(unrealized_pnl) as total_unrealized_pnl
FROM portfolio_tracking
WHERE position_status = 'open'

-- Position allocation
SELECT address, allocation_percent, unrealized_pnl
FROM portfolio_tracking
WHERE position_status = 'open'
ORDER BY allocation_percent DESC
```

---

### 14. CORRELATION_ANALYSIS (Advanced) ⭐⭐⭐

**Purpose:** Token correlation tracking  
**Columns:** 8  
**Pattern:** Update or insert  
**Key:** token_a + token_b (composite)

```
token_a, token_b, correlation_coefficient, timeframe,
last_updated, correlation_strength, divergence_alert, notes
```

**Queries:**

```sql
-- Highly correlated pairs
SELECT token_a, token_b, correlation_coefficient
FROM correlation_analysis
WHERE correlation_coefficient > 0.8
  AND timeframe = '7d'

-- Diversification opportunities
SELECT token_a, token_b, correlation_coefficient
FROM correlation_analysis
WHERE correlation_coefficient < 0.2
  AND timeframe = '7d'
```

---

## Implementation Roadmap

### Phase 1: Foundation (Current) ✅

- MESSAGES
- TOKEN_PRICES
- PERFORMANCE
- HISTORICAL

**Status:** Implemented  
**Time:** Completed

---

### Phase 2: Core Analytics (Next)

- ROI_ANALYSIS
- CHANNEL_REPUTATION
- ALERTS_LOG

**Time:** 1.5 hours  
**Priority:** High

---

### Phase 3: Risk Management

- LIQUIDITY_EVENTS
- TRADING_SIGNALS
- WHALE_ACTIVITY

**Time:** 3 hours  
**Priority:** Medium-High

---

### Phase 4: Advanced Analytics

- SOCIAL_SENTIMENT
- MARKET_CONDITIONS
- PORTFOLIO_TRACKING

**Time:** 3 hours  
**Priority:** Medium

---

### Phase 5: Optimization

- CORRELATION_ANALYSIS

**Time:** 1.5 hours  
**Priority:** Low

---

## Total Ecosystem Stats

| Metric                  | Value                         |
| ----------------------- | ----------------------------- |
| **Total Tables**        | 14                            |
| **Total Columns**       | 138                           |
| **Core Tables**         | 4 (implemented)               |
| **Analytics Tables**    | 4                             |
| **Risk Tables**         | 3                             |
| **Context Tables**      | 2                             |
| **Management Tables**   | 1                             |
| **Implementation Time** | ~9 hours (from current state) |

---

## Benefits of Complete Ecosystem

### 1. Comprehensive Intelligence

- Track every aspect of crypto signals
- From message to outcome
- Risk management at every step

### 2. Outcome-Based Learning

- ROI tracking feeds channel reputation
- Channel reputation improves signal quality
- Continuous improvement loop

### 3. Risk Mitigation

- Liquidity monitoring
- Whale activity tracking
- Multi-signal alerts

### 4. Portfolio Management

- Position tracking
- Performance attribution
- Risk-adjusted returns

### 5. Market Context

- Sentiment analysis
- Market conditions
- Correlation insights

---

## Conclusion

The multi-table architecture supports a **complete crypto intelligence ecosystem** with:

✅ **Easy extensibility** (30-60 min per table)  
✅ **Comprehensive coverage** (14+ tables)  
✅ **Clear relationships** (normalized structure)  
✅ **Flexible querying** (join as needed)  
✅ **Scalable design** (unlimited growth)

**Start with 4 core tables, expand to 14+ as needed!** 🚀
