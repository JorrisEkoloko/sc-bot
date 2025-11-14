# Architecture Quick Reference Guide

## Where to Find Things

### Domain Models (Pure Data)

```python
from domain.price_data import PriceData
from domain.signal_outcome import SignalOutcome
from domain.channel_reputation import ChannelReputation
from domain.message_event import MessageEvent
```

### Repositories (Data Access)

```python
# API Clients
from repositories.api_clients import CoinGeckoClient, BirdeyeClient

# File Storage
from repositories.file_storage import OutcomeRepository, ReputationRepository

# Writers
from repositories.writers import CSVTableWriter, GoogleSheetsMultiTable
```

### Services (Business Logic)

```python
# Analytics
from services.analytics import SentimentAnalyzer, HDRBScorer, MarketAnalyzer

# Message Processing
from services.message_processing import MessageProcessor, AddressExtractor

# Pricing
from services.pricing import PriceEngine, DataEnrichmentService

# Tracking
from services.tracking import PerformanceTracker, OutcomeTracker

# Reputation
from services.reputation import ReputationEngine, ROICalculator
```

### Infrastructure (External Integrations)

```python
from infrastructure.telegram import TelegramMonitor
from infrastructure.output import MultiTableDataOutput
from infrastructure.scrapers import HistoricalScraper
```

---

## Where to Add New Code

### Adding a New Domain Model

**Location**: `domain/new_model.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class NewModel:
    """Pure data structure."""
    field1: str
    field2: Optional[int] = None
```

**Update**: `domain/__init__.py`

### Adding a New Repository

**Location**: `repositories/file_storage/new_repository.py`

```python
from domain.new_model import NewModel
from utils.logger import setup_logger

class NewRepository:
    """Pure data access - no business logic."""

    def save(self, data):
        # Save to file/database
        pass

    def load(self):
        # Load from file/database
        pass
```

**Update**: `repositories/file_storage/__init__.py`

### Adding a New Service

**Location**: `services/category/new_service.py`

```python
from repositories.file_storage import NewRepository
from domain.new_model import NewModel
from utils.logger import setup_logger

class NewService:
    """Business logic - no data access."""

    def __init__(self):
        self.repository = NewRepository()

    def process(self, data):
        # Business logic here
        result = self._calculate(data)
        self.repository.save(result)
        return result
```

**Update**: `services/category/__init__.py`

### Adding a New Infrastructure Component

**Location**: `infrastructure/category/new_component.py`

```python
from services.category import NewService
from utils.logger import setup_logger

class NewComponent:
    """External integration."""

    def __init__(self):
        self.service = NewService()

    def connect(self):
        # Handle external connection
        pass
```

**Update**: `infrastructure/category/__init__.py`

---

## Common Patterns

### Pattern 1: Service Using Repository

```python
# services/example/example_service.py
from repositories.file_storage.example_repository import ExampleRepository
from domain.example_model import ExampleModel

class ExampleService:
    def __init__(self):
        self.repository = ExampleRepository()

    def process(self, data):
        # Business logic
        result = self._calculate(data)

        # Save using repository
        self.repository.save(result)
        return result
```

### Pattern 2: Infrastructure Using Service

```python
# infrastructure/example/example_component.py
from services.example.example_service import ExampleService

class ExampleComponent:
    def __init__(self):
        self.service = ExampleService()

    def handle_external_event(self, event):
        # Use service for business logic
        result = self.service.process(event)
        return result
```

### Pattern 3: Creating Domain Models

```python
# Anywhere in the codebase
from domain.price_data import PriceData

price = PriceData(
    price_usd=0.001,
    market_cap=1000000,
    symbol="TOKEN"
)
```

---

## Import Rules

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

---

## Testing Patterns

### Testing Domain Models

```python
from domain.price_data import PriceData

def test_price_data():
    price = PriceData(price_usd=0.001, symbol="TEST")
    assert price.symbol == "TEST"
```

### Testing Repositories (with mocks)

```python
from repositories.file_storage.outcome_repository import OutcomeRepository
import tempfile

def test_repository():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = OutcomeRepository(data_dir=tmpdir)
        repo.save({"key": data})
        loaded = repo.load()
        assert "key" in loaded
```

### Testing Services (with mocked repositories)

```python
from services.analytics.sentiment_analyzer import SentimentAnalyzer

def test_service():
    analyzer = SentimentAnalyzer()
    sentiment, score = analyzer.analyze("Bullish! 🚀")
    assert sentiment == "positive"
```

### Testing Integration

```python
def test_integration():
    # Create domain model
    from domain.message_event import MessageEvent
    event = MessageEvent(...)

    # Use service
    from services.message_processing.crypto_detector import CryptoDetector
    detector = CryptoDetector()
    mentions = detector.detect_mentions(event.message_text)

    # Verify result
    assert len(mentions) > 0
```

---

## Running Tests

### Run New Architecture Tests

```bash
python crypto-intelligence/test_new_architecture.py
```

### Expected Output

```
================================================================================
TEST SUMMARY
================================================================================
✅ PASS - Domain Layer
✅ PASS - Repositories Layer
✅ PASS - Services Layer
✅ PASS - Infrastructure Layer
✅ PASS - Main Orchestrator
✅ PASS - Dependency Flow
✅ PASS - Integration Flow
================================================================================
Results: 7/7 tests passed

🎉 ALL TESTS PASSED - Architecture is working correctly!
```

---

## Troubleshooting

### Import Error: Module not found

**Problem**: `ModuleNotFoundError: No module named 'domain'`
**Solution**: Make sure you're running from the project root and `crypto-intelligence` is in your Python path

### Circular Import Error

**Problem**: `ImportError: cannot import name 'X' from partially initialized module`
**Solution**: Check dependency flow - upper layers should not import from lower layers

### Test Failures

**Problem**: Tests failing after changes
**Solution**: Run `python crypto-intelligence/test_new_architecture.py` to verify architecture integrity

---

## Quick Commands

```bash
# Test architecture
python crypto-intelligence/test_new_architecture.py

# Run main system
python crypto-intelligence/main.py

# Check imports
python -c "from main import CryptoIntelligenceSystem; print('✅ OK')"

# Run diagnostics (if using IDE)
# Check for import errors and type issues
```

---

## File Organization Checklist

When creating new files:

- [ ] Place in correct layer (domain/repositories/services/infrastructure)
- [ ] Add to appropriate `__init__.py`
- [ ] Use absolute imports for cross-layer
- [ ] Use relative imports within package
- [ ] Follow single responsibility principle
- [ ] Add docstrings
- [ ] Add type hints
- [ ] Write tests

---

## Need Help?

1. Check `ARCHITECTURE-DIAGRAM.md` for visual overview
2. Check `ARCHITECTURE-VERIFICATION-REPORT.md` for detailed verification
3. Check `REFACTORING-COMPLETE.md` for complete documentation
4. Run `test_new_architecture.py` to verify your changes

---

**Quick Reference Version**: 1.0  
**Last Updated**: November 12, 2025
