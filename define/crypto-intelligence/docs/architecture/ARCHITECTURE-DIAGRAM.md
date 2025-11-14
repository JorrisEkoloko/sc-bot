# Crypto Intelligence System - Architecture Diagram

## Layered Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py                                 │
│                    (System Orchestrator)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│                  (External Integrations)                         │
├─────────────────────────────────────────────────────────────────┤
│  telegram/                output/              scrapers/         │
│  • telegram_monitor.py    • data_output.py    • historical_     │
│                                                  scraper.py      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICES LAYER                              │
│                    (Business Logic)                              │
├─────────────────────────────────────────────────────────────────┤
│  message_processing/      analytics/          pricing/          │
│  • message_processor.py   • sentiment_        • price_engine.py │
│  • address_extractor.py     analyzer.py      • data_enrichment  │
│  • crypto_detector.py     • hdrb_scorer.py     .py              │
│                           • market_analyzer                      │
│                             .py                                  │
│                                                                  │
│  tracking/                reputation/                            │
│  • performance_tracker    • reputation_engine.py                │
│    .py                    • reputation_calculator.py            │
│  • outcome_tracker.py     • roi_calculator.py                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   REPOSITORIES LAYER                             │
│                    (Data Access)                                 │
├─────────────────────────────────────────────────────────────────┤
│  api_clients/             file_storage/       writers/          │
│  • base_client.py         • outcome_          • csv_writer.py   │
│  • coingecko_client.py      repository.py    • sheets_writer    │
│  • birdeye_client.py      • reputation_        .py              │
│  • moralis_client.py        repository.py                       │
│  • dexscreener_client     • tracking_                           │
│    .py                      repository.py                       │
│  • cryptocompare_client                                         │
│    .py                                                          │
│  • defillama_client.py                                          │
│  • twelvedata_client.py                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                │
│                  (Pure Data Structures)                          │
├─────────────────────────────────────────────────────────────────┤
│  • price_data.py          • signal_outcome.py                   │
│  • channel_reputation.py  • message_event.py                    │
│                                                                  │
│  (Zero dependencies - Pure dataclasses)                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   CROSS-CUTTING CONCERNS                         │
├─────────────────────────────────────────────────────────────────┤
│  config/                  utils/                                │
│  • settings.py            • logger.py                           │
│  • price_config.py        • error_handler.py                    │
│  • performance_config.py  • rate_limiter.py                     │
│  • output_config.py       • circuit_breaker.py                  │
│  • retry_config.py        • type_converters.py                  │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Flow

```
┌──────────────┐
│   main.py    │
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│ infrastructure   │ ──→ Uses services for business logic
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│    services      │ ──→ Uses repositories for data access
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│  repositories    │ ──→ Uses domain models for data structures
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│     domain       │ ──→ Zero dependencies
└──────────────────┘

       ↑
       │
┌──────┴───────────┐
│  utils & config  │ ──→ Used by all layers
└──────────────────┘
```

## Component Interactions

### Message Processing Flow

```
TelegramMonitor (infrastructure)
       │
       ↓ MessageEvent
MessageProcessor (service)
       │
       ├──→ CryptoDetector (service)
       ├──→ AddressExtractor (service)
       ├──→ SentimentAnalyzer (service)
       └──→ HDRBScorer (service)
       │
       ↓ ProcessedMessage
PriceEngine (service)
       │
       ├──→ CoinGeckoClient (repository)
       ├──→ BirdeyeClient (repository)
       ├──→ MoralisClient (repository)
       └──→ DexScreenerClient (repository)
       │
       ↓ PriceData
DataEnrichmentService (service)
       │
       └──→ MarketAnalyzer (service)
       │
       ↓ EnrichedPriceData
PerformanceTracker (service)
       │
       └──→ TrackingRepository (repository)
       │
       ↓ PerformanceData
DataOutput (infrastructure)
       │
       ├──→ CSVWriter (repository)
       └──→ SheetsWriter (repository)
```

### Reputation Update Flow

```
OutcomeTracker (service)
       │
       ├──→ OutcomeRepository (repository) ──→ Load outcomes
       └──→ ROICalculator (service) ──→ Calculate ROI
       │
       ↓ SignalOutcome[]
ReputationEngine (service)
       │
       ├──→ ReputationCalculator (service) ──→ Calculate metrics
       └──→ ReputationRepository (repository) ──→ Save reputation
       │
       ↓ ChannelReputation
```

## Layer Responsibilities

### Domain Layer

**Purpose**: Pure data structures
**Rules**:

- No business logic
- No external dependencies
- Only dataclasses and type hints
- Shared across all layers

### Repositories Layer

**Purpose**: Data access and persistence
**Rules**:

- Only CRUD operations
- No business logic
- No calculations
- Returns domain models

### Services Layer

**Purpose**: Business logic and orchestration
**Rules**:

- Contains all business rules
- Orchestrates repositories
- Performs calculations
- Implements algorithms

### Infrastructure Layer

**Purpose**: External integrations
**Rules**:

- Handles external I/O
- Uses services for logic
- Manages connections
- Handles protocols

## Import Patterns

### ✅ Correct Imports

```python
# Infrastructure importing services
from services.pricing.price_engine import PriceEngine

# Services importing repositories
from repositories.api_clients import CoinGeckoClient

# Repositories importing domain
from domain.price_data import PriceData

# All layers importing utils
from utils.logger import setup_logger
```

### ❌ Incorrect Imports (Violations)

```python
# Infrastructure directly accessing repositories (skip services)
from repositories.api_clients import CoinGeckoClient  # ❌

# Services directly accessing infrastructure
from infrastructure.telegram import TelegramMonitor  # ❌

# Repositories importing services
from services.analytics import MarketAnalyzer  # ❌

# Domain importing anything
from utils.logger import setup_logger  # ❌
```

## Testing Strategy

### Unit Tests

```
domain/     → Test data structures and methods
repositories/ → Test with mocked external APIs/files
services/   → Test with mocked repositories
infrastructure/ → Test with mocked services
```

### Integration Tests

```
services + repositories → Test business logic with real data access
infrastructure + services → Test external integrations with real logic
```

### End-to-End Tests

```
main.py → infrastructure → services → repositories → domain
```

## Benefits of This Architecture

1. **Testability**: Easy to mock each layer
2. **Maintainability**: Clear where to find/add code
3. **Scalability**: Easy to add new features
4. **Flexibility**: Easy to swap implementations
5. **Clarity**: Obvious dependencies and flow
6. **Professional**: Industry-standard architecture

---

**Architecture Pattern**: Clean Architecture / Layered Architecture
**Dependency Rule**: Dependencies point inward (toward domain)
**Status**: ✅ Implemented and Verified
