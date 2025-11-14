# Implementation Checklist: 24h Lookback + Forward OHLC

## Overview

This checklist provides step-by-step implementation tasks for accurate historical ROI calculation.

---

## ✅ Pre-Implementation Verification

### Infrastructure Check

- [x] CryptoCompare client exists with OHLC methods
- [x] Twelve Data client exists with OHLC methods
- [x] HistoricalPriceRetriever exists with base methods
- [x] OutcomeTracker supports checkpoint data
- [x] Integration points exist in historical_scraper.py
- [x] API keys configured in .env

### API Keys Required

- [ ] CRYPTOCOMPARE_API_KEY (get from https://www.cryptocompare.com/cryptopian/api-keys)
- [ ] TWELVEDATA_API_KEY (get from https://twelvedata.com/apikey)

---

## 📝 Phase 1: Enhance HistoricalPriceRetriever

**File**: `crypto-intelligence/services/pricing/historical_price_retriever.py`

### Task 1.1: Add 24-Hour Lookback Method

- [ ] Create `fetch_entry_price_with_24h_lookback()` method
- [ ] Implement 24h → 12h → 0h fallback logic
- [ ] Add CryptoCompare as primary source
- [ ] Add Twelve Data as fallback
- [ ] Add current price as final fallback
- [ ] Add logging for each attempt
- [ ] Add error handling

**Estimated time**: 1 hour

### Task 1.2: Add Forward OHLC ATH Calculation

- [ ] Create `fetch_ath_from_forward_ohlc()` method
- [ ] Fetch 30 days of OHLC from CryptoCompare
- [ ] Parse OHLC candles into OHLCCandle objects
- [ ] Find max(high) across all candles for ATH
- [ ] Record ATH timestamp and days_to_ath
- [ ] Add Twelve Data fallback
- [ ] Add error handling for missing data
- [ ] Add caching for OHLC data

**Estimated time**: 1.5 hours

### Task 1.3: Add Checkpoint ROI Calculation from OHLC

- [ ] Create `calculate_checkpoint_rois_from_ohlc()` method
- [ ] For each checkpoint, find matching OHLC candle
- [ ] Use candle's close price for checkpoint
- [ ] Calculate ROI = close_price / entry_price
- [ ] Handle missing candles gracefully
- [ ] Return Dict[checkpoint_name, roi_multiplier]
- [ ] Add logging for each checkpoint

**Estimated time**: 1 hour

### Task 1.4: Update Existing Methods

- [ ] Update `fetch_ohlc_window()` to use CryptoCompare client methods
- [ ] Add data completeness tracking
- [ ] Add quality flags for partial data
- [ ] Update caching to include OHLC candles

**Estimated time**: 30 minutes

---

## 📝 Phase 2: Update historical_scraper.py Integration

**File**: `crypto-intelligence/scripts/historical_scraper.py`

### Task 2.1: Update Entry Price Logic

- [ ] Replace current entry price with 24h lookback
- [ ] Update call to `fetch_entry_price_with_24h_lookback()`
- [ ] Add logging for entry price source
- [ ] Handle fallback to current price

**Estimated time**: 30 minutes

### Task 2.2: Update Checkpoint Calculation

- [ ] Replace `fetch_checkpoint_prices()` with OHLC-based calculation
- [ ] Call `fetch_ath_from_forward_ohlc()` for ATH
- [ ] Call `calculate_checkpoint_rois_from_ohlc()` for checkpoints
- [ ] Update SignalOutcome with OHLC-based data
- [ ] Add data completeness validation

**Estimated time**: 1 hour

### Task 2.3: Update Statistics Tracking

- [ ] Add stat for 24h lookback success rate
- [ ] Add stat for OHLC data availability
- [ ] Add stat for data completeness
- [ ] Update report generation with new stats

**Estimated time**: 30 minutes

---

## 📝 Phase 3: Testing & Validation

### Task 3.1: Unit Tests

- [ ] Test 24h lookback with various timestamps
- [ ] Test OHLC ATH calculation with sample data
- [ ] Test checkpoint ROI calculation
- [ ] Test API fallback chain
- [ ] Test error handling for missing data
- [ ] Test caching behavior

**Estimated time**: 2 hours

### Task 3.2: Integration Tests

- [ ] Test with 10 real historical messages (30+ days old)
- [ ] Verify entry price accuracy vs current price
- [ ] Verify ATH calculation vs manual calculation
- [ ] Test batch processing (50 signals)
- [ ] Verify API usage stays within limits

**Estimated time**: 1 hour

### Task 3.3: Manual Validation

- [ ] Pick 5 known signals with known outcomes
- [ ] Calculate expected ROI manually
- [ ] Compare with system calculation
- [ ] Verify accuracy within 5%
- [ ] Document any discrepancies

**Estimated time**: 1 hour

---

## 📝 Phase 4: Configuration & Documentation

### Task 4.1: Update Configuration

- [ ] Add ENTRY_PRICE_LOOKBACK_HOURS to .env.example
- [ ] Add FORWARD_OHLC_WINDOW_DAYS to .env.example
- [ ] Add rate limit configs
- [ ] Update README with new features

**Estimated time**: 30 minutes

### Task 4.2: Update Documentation

- [ ] Document 24h lookback logic
- [ ] Document OHLC ATH calculation
- [ ] Document API fallback chain
- [ ] Add examples to docstrings
- [ ] Update architecture diagrams

**Estimated time**: 1 hour

---

## 📝 Phase 5: Deployment & Monitoring

### Task 5.1: Deploy to Production

- [ ] Merge changes to main branch
- [ ] Update production .env with API keys
- [ ] Run backfill on existing signals
- [ ] Monitor API usage
- [ ] Monitor error rates

**Estimated time**: 1 hour

### Task 5.2: Monitoring & Optimization

- [ ] Track 24h lookback success rate
- [ ] Track OHLC data availability
- [ ] Track API call usage
- [ ] Optimize caching strategy
- [ ] Tune rate limiting

**Estimated time**: Ongoing

---

## 🎯 Success Criteria

### Accuracy Metrics

- [ ] Entry price accuracy: ≥95% (vs current price baseline)
- [ ] ATH accuracy: ≥98% (vs manual calculation)
- [ ] Checkpoint ROI accuracy: ≥95%
- [ ] Data completeness: ≥80% of signals

### Performance Metrics

- [ ] API calls per signal: ≤2
- [ ] Processing time per signal: ≤1 second
- [ ] Batch processing: ≥50 signals/minute
- [ ] Cache hit rate: ≥70%

### Reliability Metrics

- [ ] API fallback success rate: ≥95%
- [ ] Error rate: ≤5%
- [ ] Uptime: ≥99%

---

## 📊 Estimated Timeline

| Phase     | Tasks                            | Time           | Dependencies |
| --------- | -------------------------------- | -------------- | ------------ |
| Phase 1   | Enhance HistoricalPriceRetriever | 4 hours        | API keys     |
| Phase 2   | Update historical_scraper        | 2 hours        | Phase 1      |
| Phase 3   | Testing & Validation             | 4 hours        | Phase 2      |
| Phase 4   | Configuration & Docs             | 1.5 hours      | Phase 3      |
| Phase 5   | Deployment                       | 1 hour         | Phase 4      |
| **Total** |                                  | **12.5 hours** | **~2 days**  |

---

## 🚨 Risk Mitigation

### Risk 1: API Rate Limits

**Mitigation**:

- Implement exponential backoff
- Use caching aggressively
- Monitor usage daily
- Have fallback APIs ready

### Risk 2: Missing Historical Data

**Mitigation**:

- Implement 24h → 12h → 0h fallback
- Track data completeness
- Flag incomplete signals
- Use current price as last resort

### Risk 3: Symbol Mapping Issues

**Mitigation**:

- Use CryptoCompare (symbol-based)
- Maintain symbol mapping table
- Log unmapped symbols
- Add manual mapping for common tokens

### Risk 4: Performance Degradation

**Mitigation**:

- Batch process signals
- Use async/await properly
- Implement caching
- Monitor processing times

---

## 📞 Support & Resources

### API Documentation

- CryptoCompare: https://min-api.cryptocompare.com/documentation
- Twelve Data: https://twelvedata.com/docs
- CoinGecko: https://docs.coingecko.com/

### Internal Documentation

- Architecture: `docs/24h-lookback-ohlc-analysis.md`
- API Comparison: `docs/api-comparison-summary.md`
- Code: `services/pricing/historical_price_retriever.py`

### Key Files

- HistoricalPriceRetriever: `services/pricing/historical_price_retriever.py`
- CryptoCompare Client: `repositories/api_clients/cryptocompare_client.py`
- Twelve Data Client: `repositories/api_clients/twelvedata_client.py`
- Historical Scraper: `scripts/historical_scraper.py`
- Outcome Tracker: `services/tracking/outcome_tracker.py`

---

## ✅ Final Checklist

Before marking complete:

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Manual validation complete
- [ ] Documentation updated
- [ ] Configuration updated
- [ ] Deployed to production
- [ ] Monitoring in place
- [ ] Success metrics met
- [ ] Team trained on new features
- [ ] Runbook created for troubleshooting

---

## 🎉 Completion

**Date completed**: ******\_\_\_******

**Completed by**: ******\_\_\_******

**Notes**: **********************\_\_\_**********************

**Next steps**: **********************\_\_\_**********************
