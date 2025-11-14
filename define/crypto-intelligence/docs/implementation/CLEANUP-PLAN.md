# Architecture Cleanup Plan

## Objective

Safely remove old architecture files after verifying the new architecture works correctly.

## Pre-Cleanup Checklist

### ✅ Verification Steps (MUST PASS)

1. [ ] All new architecture imports work
2. [ ] Test suite passes (7/7 tests)
3. [ ] Main system can start
4. [ ] No references to old file locations in new code

### ✅ Safety Measures

1. [ ] Create backup of all files before deletion
2. [ ] Verify after each deletion step
3. [ ] Keep rollback plan ready

---

## Phase 1: Analysis & Mapping

### Step 1.1: Identify All Files to Remove

**Action**: List all files that have been moved to new locations

**Old Location** → **New Location**

#### From core/ to services/analytics/

- `core/sentiment_analyzer.py` → `services/analytics/sentiment_analyzer.py`
- `core/hdrb_scorer.py` → `services/analytics/hdrb_scorer.py`

#### From core/ to services/message_processing/

- `core/message_processor.py` → `services/message_processing/message_processor.py`
- `core/address_extractor.py` → `services/message_processing/address_extractor.py`
- `core/crypto_detector.py` → `services/message_processing/crypto_detector.py`

#### From core/ to services/pricing/

- `core/price_engine.py` → `services/pricing/price_engine.py`
- `core/data_enrichment_service.py` → `services/pricing/data_enrichment.py`

#### From core/ to services/tracking/

- `core/performance_tracker.py` → `services/tracking/performance_tracker.py`

#### From core/ to infrastructure/

- `core/telegram_monitor.py` → `infrastructure/telegram/telegram_monitor.py`
- `core/data_output.py` → `infrastructure/output/data_output.py`
- `core/historical_scraper.py` → `infrastructure/scrapers/historical_scraper.py`

#### From core/ to repositories/writers/

- `core/csv_table_writer.py` → `repositories/writers/csv_writer.py`
- `core/sheets_multi_table.py` → `repositories/writers/sheets_writer.py`

#### From core/api_clients/ to repositories/api_clients/

- Entire `core/api_clients/` directory → `repositories/api_clients/`

#### From intelligence/ to services/reputation/

- `intelligence/reputation_engine.py` → `services/reputation/reputation_engine.py`
- `intelligence/reputation_calculator.py` → `services/reputation/reputation_calculator.py`
- `intelligence/roi_calculator.py` → `services/reputation/roi_calculator.py`

#### From intelligence/ to services/tracking/

- `intelligence/outcome_tracker.py` → `services/tracking/outcome_tracker.py`

#### From intelligence/ to repositories/file_storage/

- `intelligence/outcome_repository.py` → `repositories/file_storage/outcome_repository.py`

#### From intelligence/ to services/analytics/

- `intelligence/market_analyzer.py` → `services/analytics/market_analyzer.py`

#### From intelligence/ to domain/

- `intelligence/signal_outcome.py` → `domain/signal_outcome.py`
- `intelligence/channel_reputation_model.py` → `domain/channel_reputation.py`

**Total Files to Remove**: ~23 files

### Step 1.2: Check for Remaining References

**Action**: Search codebase for any imports from old locations

**Command**:

```bash
grep -r "from core\." crypto-intelligence/*.py
grep -r "from intelligence\." crypto-intelligence/*.py
```

**Expected**: No matches in new architecture files

---

## Phase 2: Pre-Cleanup Verification

### Step 2.1: Verify New Architecture Imports

**Action**: Test all new imports work

**Test Script**: Run `test_new_architecture.py`

```bash
python crypto-intelligence/test_new_architecture.py
```

**Expected**: 7/7 tests pass

### Step 2.2: Verify Main System

**Action**: Test main system can start

**Command**:

```bash
python -c "import sys; sys.path.insert(0, 'crypto-intelligence'); from main import CryptoIntelligenceSystem; print('✅ OK')"
```

**Expected**: No errors

### Step 2.3: Document Current State

**Action**: List all files in core/ and intelligence/

**Command**:

```bash
ls -la crypto-intelligence/core/*.py
ls -la crypto-intelligence/intelligence/*.py
```

---

## Phase 3: Backup Creation

### Step 3.1: Create Backup Directory

**Action**: Create backup location

**Command**:

```bash
mkdir -p crypto-intelligence/.backup_old_structure
```

### Step 3.2: Backup All Files

**Action**: Copy all files to be deleted to backup

**For each file**:

1. Copy to `.backup_old_structure/` preserving directory structure
2. Verify backup exists
3. Log backup location

---

## Phase 4: Incremental Cleanup (With Verification)

### Step 4.1: Remove Analytics Files from core/

**Files**:

- `core/sentiment_analyzer.py`
- `core/hdrb_scorer.py`

**Process**:

1. Backup files
2. Delete files
3. Run verification: `python -c "from services.analytics import SentimentAnalyzer, HDRBScorer; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.2: Remove Message Processing Files from core/

**Files**:

- `core/message_processor.py`
- `core/address_extractor.py`
- `core/crypto_detector.py`

**Process**:

1. Backup files
2. Delete files
3. Run verification: `python -c "from services.message_processing import MessageProcessor; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.3: Remove Pricing Files from core/

**Files**:

- `core/price_engine.py`
- `core/data_enrichment_service.py`

**Process**:

1. Backup files
2. Delete files
3. Run verification: `python -c "from services.pricing import PriceEngine; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.4: Remove Tracking Files from core/

**Files**:

- `core/performance_tracker.py`

**Process**:

1. Backup files
2. Delete files
3. Run verification: `python -c "from services.tracking import PerformanceTracker; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.5: Remove Infrastructure Files from core/

**Files**:

- `core/telegram_monitor.py`
- `core/data_output.py`
- `core/historical_scraper.py`

**Process**:

1. Backup files
2. Delete files
3. Run verification: `python -c "from infrastructure.telegram import TelegramMonitor; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.6: Remove Writer Files from core/

**Files**:

- `core/csv_table_writer.py`
- `core/sheets_multi_table.py`

**Process**:

1. Backup files
2. Delete files
3. Run verification: `python -c "from repositories.writers import CSVTableWriter; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.7: Remove API Clients Directory from core/

**Directory**: `core/api_clients/`

**Process**:

1. Backup entire directory
2. Delete directory
3. Run verification: `python -c "from repositories.api_clients import CoinGeckoClient; print('✅ OK')"`
4. If PASS → Continue, If FAIL → Restore and stop

### Step 4.8: Remove Files from intelligence/

**Files**:

- `intelligence/reputation_engine.py`
- `intelligence/reputation_calculator.py`
- `intelligence/roi_calculator.py`
- `intelligence/outcome_tracker.py`
- `intelligence/outcome_repository.py`
- `intelligence/market_analyzer.py`
- `intelligence/signal_outcome.py`
- `intelligence/channel_reputation_model.py`

**Process**:

1. Backup files
2. Delete files one by one
3. After each deletion, run verification
4. If PASS → Continue, If FAIL → Restore and stop

---

## Phase 5: Post-Cleanup Verification

### Step 5.1: Run Full Test Suite

**Action**: Run all architecture tests

**Command**:

```bash
python crypto-intelligence/test_new_architecture.py
```

**Expected**: 7/7 tests pass

### Step 5.2: Verify Main System

**Action**: Test main system still works

**Command**:

```bash
python -c "import sys; sys.path.insert(0, 'crypto-intelligence'); from main import CryptoIntelligenceSystem; system = CryptoIntelligenceSystem(); print('✅ System OK')"
```

**Expected**: No errors

### Step 5.3: Check for Empty Directories

**Action**: List remaining files in core/ and intelligence/

**Command**:

```bash
ls -la crypto-intelligence/core/
ls -la crypto-intelligence/intelligence/
```

**Expected**: Only `__init__.py` and `__pycache__/` remain

---

## Phase 6: Final Cleanup

### Step 6.1: Review Remaining Files

**Action**: Manually review what's left in core/ and intelligence/

**Decision Points**:

- Keep `__init__.py` files? (Yes, for backward compatibility)
- Remove `__pycache__/`? (Yes, can be regenerated)
- Remove empty directories? (Optional, document decision)

### Step 6.2: Clean **pycache** Directories

**Action**: Remove all **pycache** directories

**Command**:

```bash
find crypto-intelligence -type d -name "__pycache__" -exec rm -rf {} +
```

### Step 6.3: Document Final State

**Action**: Create final cleanup report

**Include**:

- Files removed (count)
- Directories removed (count)
- Backup location
- Verification results
- Remaining files (if any)

---

## Rollback Plan

### If Cleanup Fails

1. **Stop immediately** at the failing step
2. **Restore from backup**:
   ```bash
   cp -r crypto-intelligence/.backup_old_structure/* crypto-intelligence/
   ```
3. **Verify restoration**:
   ```bash
   python crypto-intelligence/test_new_architecture.py
   ```
4. **Investigate failure** before retrying

### Backup Location

All backups stored in: `crypto-intelligence/.backup_old_structure/`

**Keep backups until**:

- All tests pass
- System runs successfully in production for 1 week
- Team confirms no issues

---

## Success Criteria

### Must Pass All:

- [ ] 7/7 architecture tests pass
- [ ] Main system can start
- [ ] No import errors
- [ ] No references to old locations
- [ ] Backup created successfully
- [ ] All deletions completed
- [ ] Post-cleanup verification passes

---

## Execution Timeline

**Estimated Time**: 30-45 minutes

1. **Phase 1**: Analysis (5 min)
2. **Phase 2**: Pre-verification (5 min)
3. **Phase 3**: Backup (5 min)
4. **Phase 4**: Incremental cleanup (15-20 min)
5. **Phase 5**: Post-verification (5 min)
6. **Phase 6**: Final cleanup (5 min)

---

## Notes

- Execute during low-traffic period
- Have team member available for verification
- Document any unexpected issues
- Keep backup for at least 1 week after cleanup

---

**Plan Created**: November 12, 2025  
**Status**: Ready for execution  
**Approval Required**: Yes
