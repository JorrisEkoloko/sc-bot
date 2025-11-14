# Project Structure

## Repository Organization

This is a **documentation-first repository** containing comprehensive implementation guides for rebuilding a crypto intelligence system. The actual source code implementation follows the documented architecture.

## Documentation Structure

### Root Level Documentation

- **README.md**: Entry point with complete navigation
- **MASTER-IMPLEMENTATION-GUIDE.md**: Complete ordered roadmap for AI agents
- **crypto-intelligence-rebuild.md**: Master architecture overview
- **VERIFICATION-REPORT-100-PERCENT.md**: Validation report

### Planning & Analysis

- **current-vs-new-architecture-analysis.md**: Detailed comparison
- **component-migration-matrix.md**: Current → New mapping
- **complete-pipeline-coverage-summary.md**: All 19 components overview
- **implementation-roadmap.md**: 5-week timeline
- **test-coverage-preservation-plan.md**: Testing strategy

### Environment & Deployment

- **environment-setup-guide.md**: Complete setup instructions
- **actual-env-configuration-guide.md**: Working .env structure
- **production-deployment-guide.md**: Production deployment
- **credential-matching-verification.md**: Credential validation

### Component Implementation Guides

#### core-components/

6 detailed implementation guides for core system:

- `telegram-monitor-implementation.md`
- `message-processor-implementation.md`
- `address-extractor-implementation.md`
- `price-engine-implementation.md`
- `performance-tracker-implementation.md`
- `data-output-implementation.md`

#### intelligence-layer/

6 guides for intelligence features:

- `market-analyzer-implementation.md`
- `channel-reputation-implementation.md`
- `signal-scorer-implementation.md`
- `coin-mention-detector-implementation.md`
- `targeted-ath-checker-implementation.md`
- `intelligence-data-enricher-implementation.md`

#### discovery-system/

2 guides for discovery features:

- `active-coins-collector-implementation.md`
- `channel-database-reader-implementation.md`

#### validation-system/

2 guides for validation:

- `real-world-data-provider-implementation.md`
- `statistical-validation-engine-implementation.md`

#### system-integration/

2 guides for system coordination:

- `configuration-management-implementation.md`
- `main-orchestration-implementation.md`

#### utils-layer/

1 guide for utilities:

- `enhanced-utilities-implementation.md`

### MCP Verification Server

**mcp-verification-server/**: Phase-by-phase verification system

- 8 phase JSON files with questionnaires and validation endpoints
- Pre-phase questionnaires (10/10 required to proceed)
- Component-specific verification checks
- Progression gates for quality assurance

## Target Implementation Structure

The documented system will be implemented as:

```
crypto-intelligence/
├── core/                       # 6 core components
│   ├── telegram_monitor.py
│   ├── message_processor.py
│   ├── address_extractor.py
│   ├── price_engine.py
│   ├── performance_tracker.py
│   └── data_output.py
├── intelligence/               # 3 intelligence modules
│   ├── market_analyzer.py
│   ├── channel_reputation.py
│   └── signal_scorer.py
├── config/                     # Configuration
│   ├── settings.py
│   └── channels.json
├── utils/                      # Utilities
│   ├── logger.py
│   ├── error_handler.py
│   └── rate_limiter.py
├── data/                       # Data storage
├── output/                     # Output files
├── credentials/                # API credentials
├── main.py                     # Orchestration (<500 lines)
└── requirements.txt
```

## Implementation Order

**Critical**: Components must be implemented in this exact order:

1. **Phase 0**: Understanding (read documentation)
2. **Phase 1**: Environment Setup (credentials, config)
3. **Phase 2**: Planning (migration strategy)
4. **Phase 3**: Core Foundation (6 core components)
5. **Phase 4**: Intelligence Layer (6 intelligence components)
6. **Phase 5**: Supporting Systems (discovery, validation, utils)
7. **Phase 6**: Integration (config + main orchestration)
8. **Phase 7**: Deployment (production setup)

## Key Architectural Principles

- **Simplification**: 88% code reduction from original
- **Preservation**: 100% functional preservation required
- **Modularity**: Clear component boundaries
- **Integration**: Proper component coordination
- **Validation**: Checkpoint validation at each phase

## Navigation Pattern

1. Start with **README.md** for overview
2. Read **MASTER-IMPLEMENTATION-GUIDE.md** for complete roadmap
3. Follow phase-by-phase implementation order
4. Use component-specific guides for detailed implementation
5. Validate with MCP verification server at each phase
