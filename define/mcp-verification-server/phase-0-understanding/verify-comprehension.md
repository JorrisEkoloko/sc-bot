# Verify Comprehension - Phase 0

## Purpose

Verify the AI agent understands the current system, new architecture, and preservation requirements before starting implementation.

## Comprehension Checkpoints

### 1. Current System Understanding

**Verify Knowledge Of**:

- [ ] Main.py has 4,135 lines (verified via codebase)
- [ ] 24 directories in src/ (verified count)
- [ ] 100+ Python files across components
- [ ] Complex integration with tight coupling
- [ ] Memory management issues exist

**Questions to Answer**:

1. What is the main problem with the current architecture?
2. Why is main.py so large?
3. What causes the integration complexity?

**Expected Answers**:

1. Over-engineering with 24+ directories and tight coupling
2. All orchestration logic in single file, no separation of concerns
3. Components directly depend on each other, no clean interfaces

### 2. New Architecture Understanding

**Verify Knowledge Of**:

- [ ] 19 focused components (vs 100+ files)
- [ ] 6-8 directories (vs 24)
- [ ] Main.py target: < 500 lines (vs 4,135)
- [ ] Loosely coupled design
- [ ] Clean component boundaries

**Questions to Answer**:

1. How many core components in new architecture?
2. What is the main orchestration file size target?
3. How does coupling differ from current system?

**Expected Answers**:

1. 6 core components (TelegramMonitor, MessageProcessor, AddressExtractor, PriceEngine, PerformanceTracker, DataOutput)
2. < 500 lines in main.py
3. Loosely coupled via interfaces, not direct dependencies

### 3. Functional Preservation Understanding

**Verify Knowledge Of**:

- [ ] HDRB formula: IC = retweet + (2 × favorite) + (0.5 × reply)
- [ ] Telegram fallback: retweets→forwards, favorites→likes, replies→comments
- [ ] 6 APIs: CoinGecko, DexScreener, Moralis, Etherscan, Birdeye, DeFiLlama
- [ ] 7-day ATH tracking with 2-hour updates
- [ ] 37-column Google Sheets output
- [ ] 99% API reduction via targeted ATH checking

**Questions to Answer**:

1. What is the exact HDRB formula?
2. How many APIs must be preserved?
3. What is the ATH tracking period?
4. How many columns in Google Sheets output?

**Expected Answers**:

1. IC = retweet + (2 × favorite) + (0.5 × reply) with weights 1.0, 2.0, 0.5
2. 6 APIs in failover sequence
3. 7 days (168 hours) with 2-hour update cycles
4. 37 columns (21 base + 13 API + 3 enhanced)

### 4. Implementation Order Understanding

**Verify Knowledge Of**:

- [ ] Phase 3: Core Foundation (Week 1)
- [ ] Phase 4: Intelligence Layer (Week 2)
- [ ] Phase 5: Supporting Systems (Week 3)
- [ ] Phase 6: Integration (Week 4)
- [ ] Phase 7: Deployment (Week 5)

**Questions to Answer**:

1. What gets implemented first?
2. When is intelligence layer added?
3. When does main orchestration happen?

**Expected Answers**:

1. 6 core components in Week 1
2. Intelligence layer in Week 2 (after core is stable)
3. Main orchestration in Week 4 (after all components ready)

### 5. Verification Strategy Understanding

**Verify Knowledge Of**:

- [ ] Validate after each component
- [ ] Check against current implementation
- [ ] Test integration points
- [ ] Verify functional preservation
- [ ] Measure performance metrics

**Questions to Answer**:

1. When should verification happen?
2. What is the reference for correctness?
3. How to ensure functionality preserved?

**Expected Answers**:

1. After each component implementation, before moving to next
2. Current codebase in src/ is the reference
3. Compare behavior, test same inputs/outputs, verify algorithms match

## Documentation Comprehension

### Must Have Read

- [ ] MASTER-IMPLEMENTATION-GUIDE.md (complete roadmap)
- [ ] current-vs-new-architecture-analysis.md (detailed comparison)
- [ ] complete-pipeline-coverage-summary.md (component overview)
- [ ] actual-env-configuration-guide.md (your credentials)
- [ ] component-migration-matrix.md (migration mapping)

### Must Understand

- [ ] Reading order for all 28 documents
- [ ] Phase-by-phase implementation approach
- [ ] Validation checkpoints at each step
- [ ] Success criteria for each phase

## Critical Findings Awareness

### Issue 1: Telegram HDRB Reality

**Must Understand**:

- Documentation says: forwards + (2 × views/1000) + (0.5 × replies)
- Reality: Telegram only provides `views` field
- Actual behavior: forwards/favorites/replies default to 0
- Result: IC = 0 for most Telegram messages

**Question**: What is the actual Telegram message structure?
**Expected Answer**: {id, text, date, views, sender_id} - only views available

### Issue 2: Column Count Correction

**Must Understand**:

- Old documentation said: 26 columns
- Verified reality: 37 columns
- Breakdown: 21 base + 13 API fields + 3 enhanced

**Question**: How many columns in Google Sheets output?
**Expected Answer**: 37 columns (verified in codebase)

### Issue 3: API Count Correction

**Must Understand**:

- Old documentation said: 5 APIs
- Verified reality: 6 APIs
- Missing from old docs: Etherscan

**Question**: List all 6 APIs in failover order
**Expected Answer**: CoinGecko → DexScreener → Moralis → Etherscan → Birdeye → DeFiLlama

## Comprehension Test

### Scenario 1: HDRB Implementation

**Given**: You need to implement HDRB scoring
**Question**: What formula do you use and where do you verify it?
**Expected Answer**:

- Formula: IC = retweet + (2 × favorite) + (0.5 × reply)
- Verify against: src/scoring/research_compliant_scorer.py line 140-167
- Test with: Known values to confirm exact calculation

### Scenario 2: Telegram Message Processing

**Given**: Telegram message arrives with only views field
**Question**: What will the IC value be and why?
**Expected Answer**:

- IC = 0 because forwards/favorites/replies all default to 0
- This is expected behavior (Telegram limitation)
- Document this reality in implementation

### Scenario 3: API Failover

**Given**: CoinGecko API fails
**Question**: What happens next?
**Expected Answer**:

- System tries DexScreener (next in sequence)
- If that fails, tries Moralis
- Continues through all 6 APIs
- Returns failure only if all 6 fail

### Scenario 4: Component Order

**Given**: You want to implement intelligence features
**Question**: Can you start with intelligence layer?
**Expected Answer**:

- No, must implement core foundation first (Phase 3)
- Intelligence depends on core components
- Follow exact order: Core → Intelligence → Supporting → Integration

## Success Criteria

✅ **Comprehension Verified** when:

- [ ] All checkpoints answered correctly
- [ ] All documentation read and understood
- [ ] All critical findings acknowledged
- [ ] All scenarios answered correctly
- [ ] Implementation order clear
- [ ] Verification strategy understood

✅ **Ready for Phase 1** when:

- All above criteria met
- No confusion about architecture
- Clear on what to preserve
- Understands verification approach
- Knows where to find reference implementations
