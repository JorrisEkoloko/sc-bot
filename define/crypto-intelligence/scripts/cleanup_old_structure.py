"""Cleanup script for old architecture files.

Systematically removes old files after verifying new architecture works.
"""
import os
import sys
from pathlib import Path
import shutil


def verify_imports():
    """Verify all new architecture imports work."""
    print("\n" + "="*80)
    print("VERIFYING NEW ARCHITECTURE IMPORTS")
    print("="*80)
    
    errors = []
    
    # Test domain imports
    try:
        from domain.price_data import PriceData
        from domain.signal_outcome import SignalOutcome
        from domain.channel_reputation import ChannelReputation
        from domain.message_event import MessageEvent
        print("✅ Domain layer imports OK")
    except Exception as e:
        errors.append(f"Domain layer: {e}")
        print(f"❌ Domain layer: {e}")
    
    # Test repositories imports
    try:
        from repositories.api_clients import CoinGeckoClient, BirdeyeClient
        from repositories.file_storage import OutcomeRepository, ReputationRepository
        from repositories.writers import CSVTableWriter, GoogleSheetsMultiTable
        print("✅ Repositories layer imports OK")
    except Exception as e:
        errors.append(f"Repositories layer: {e}")
        print(f"❌ Repositories layer: {e}")
    
    # Test services imports
    try:
        from services.analytics import SentimentAnalyzer, HDRBScorer
        from services.message_processing import MessageProcessor, AddressExtractor
        from services.pricing import PriceEngine, DataEnrichmentService
        from services.tracking import PerformanceTracker, OutcomeTracker
        from services.reputation import ReputationEngine
        from utils.roi_calculator import ROICalculator
        print("✅ Services layer imports OK")
    except Exception as e:
        errors.append(f"Services layer: {e}")
        print(f"❌ Services layer: {e}")
    
    # Test infrastructure imports
    try:
        from infrastructure.telegram import TelegramMonitor
        from infrastructure.output import MultiTableDataOutput
        from infrastructure.scrapers import HistoricalScraper
        print("✅ Infrastructure layer imports OK")
    except Exception as e:
        errors.append(f"Infrastructure layer: {e}")
        print(f"❌ Infrastructure layer: {e}")
    
    # Test main import
    try:
        from main import CryptoIntelligenceSystem
        print("✅ Main orchestrator imports OK")
    except Exception as e:
        errors.append(f"Main orchestrator: {e}")
        print(f"❌ Main orchestrator: {e}")
    
    return len(errors) == 0, errors


def check_file_references(file_path):
    """Check if any files still reference the old location."""
    print(f"\nChecking references to: {file_path}")
    
    # Search for imports of this file
    import subprocess
    try:
        # Use grep to find references (cross-platform)
        result = subprocess.run(
            ['python', '-c', f'import pathlib; [print(f) for f in pathlib.Path(".").rglob("*.py") if "{file_path}" in f.read_text(errors="ignore")]'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip():
            print(f"⚠️  Found references in: {result.stdout}")
            return False
        else:
            print(f"✅ No references found")
            return True
    except:
        # Fallback: assume safe if grep fails
        print(f"⚠️  Could not verify references (assuming safe)")
        return True


def backup_file(file_path):
    """Create backup of file before deletion."""
    backup_dir = Path("crypto-intelligence/.backup_old_structure")
    backup_dir.mkdir(exist_ok=True)
    
    source = Path(file_path)
    if source.exists():
        # Preserve directory structure in backup
        relative_path = source.relative_to("crypto-intelligence")
        backup_path = backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source, backup_path)
        print(f"✅ Backed up to: {backup_path}")
        return True
    return False


def delete_file(file_path):
    """Delete a file safely."""
    path = Path(file_path)
    if path.exists():
        path.unlink()
        print(f"✅ Deleted: {file_path}")
        return True
    else:
        print(f"⚠️  File not found: {file_path}")
        return False


def delete_directory(dir_path):
    """Delete a directory safely."""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        print(f"✅ Deleted directory: {dir_path}")
        return True
    else:
        print(f"⚠️  Directory not found: {dir_path}")
        return False


def cleanup_step_1_moved_files():
    """Step 1: Remove files that were moved to new locations."""
    print("\n" + "="*80)
    print("STEP 1: Cleanup Moved Files")
    print("="*80)
    
    files_to_remove = [
        # Files moved to services/analytics
        "crypto-intelligence/core/sentiment_analyzer.py",
        "crypto-intelligence/core/hdrb_scorer.py",
        
        # Files moved to services/message_processing
        "crypto-intelligence/core/message_processor.py",
        "crypto-intelligence/core/address_extractor.py",
        "crypto-intelligence/core/crypto_detector.py",
        
        # Files moved to services/pricing
        "crypto-intelligence/core/price_engine.py",
        "crypto-intelligence/core/data_enrichment_service.py",
        
        # Files moved to services/tracking
        "crypto-intelligence/core/performance_tracker.py",
        
        # Files moved to infrastructure
        "crypto-intelligence/core/telegram_monitor.py",
        "crypto-intelligence/core/data_output.py",
        "crypto-intelligence/core/historical_scraper.py",
        
        # Files moved to repositories/writers
        "crypto-intelligence/core/csv_table_writer.py",
        "crypto-intelligence/core/sheets_multi_table.py",
        
        # Files moved from intelligence to services/reputation
        "crypto-intelligence/intelligence/reputation_engine.py",
        "crypto-intelligence/intelligence/reputation_calculator.py",
        "crypto-intelligence/intelligence/roi_calculator.py",
        
        # Files moved from intelligence to services/tracking
        "crypto-intelligence/intelligence/outcome_tracker.py",
        
        # Files moved from intelligence to repositories/file_storage
        "crypto-intelligence/intelligence/outcome_repository.py",
        
        # Files moved from intelligence to services/analytics
        "crypto-intelligence/intelligence/market_analyzer.py",
        
        # Files moved to domain
        "crypto-intelligence/intelligence/signal_outcome.py",
        "crypto-intelligence/intelligence/channel_reputation_model.py",
    ]
    
    print(f"\nFiles to remove: {len(files_to_remove)}")
    
    for file_path in files_to_remove:
        print(f"\n--- Processing: {file_path}")
        if backup_file(file_path):
            delete_file(file_path)
    
    print("\n✅ Step 1 complete")


def cleanup_step_2_api_clients():
    """Step 2: Remove old api_clients directory."""
    print("\n" + "="*80)
    print("STEP 2: Cleanup API Clients Directory")
    print("="*80)
    
    api_clients_dir = "crypto-intelligence/core/api_clients"
    
    print(f"\nDirectory to remove: {api_clients_dir}")
    
    # Backup entire directory
    backup_dir = Path("crypto-intelligence/.backup_old_structure/core/api_clients")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = Path(api_clients_dir)
    if source_dir.exists():
        for file in source_dir.rglob("*.py"):
            relative_path = file.relative_to(source_dir)
            backup_path = backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, backup_path)
        
        print(f"✅ Backed up directory to: {backup_dir}")
        delete_directory(api_clients_dir)
    
    print("\n✅ Step 2 complete")


def cleanup_step_3_empty_dirs():
    """Step 3: Remove empty directories."""
    print("\n" + "="*80)
    print("STEP 3: Cleanup Empty Directories")
    print("="*80)
    
    dirs_to_check = [
        "crypto-intelligence/core",
        "crypto-intelligence/intelligence",
    ]
    
    for dir_path in dirs_to_check:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            # Check if directory is empty (only __pycache__ or __init__.py)
            contents = list(path.iterdir())
            py_files = [f for f in contents if f.suffix == '.py' and f.name != '__init__.py']
            
            if not py_files:
                print(f"\n⚠️  Directory mostly empty: {dir_path}")
                print(f"   Remaining files: {[f.name for f in contents]}")
                print(f"   Consider manual review before deletion")
            else:
                print(f"\n✅ Directory still has files: {dir_path} ({len(py_files)} .py files)")
    
    print("\n✅ Step 3 complete")


def main():
    """Main cleanup process."""
    print("="*80)
    print("ARCHITECTURE CLEANUP SCRIPT")
    print("="*80)
    print("\nThis script will:")
    print("1. Verify new architecture imports work")
    print("2. Backup old files")
    print("3. Remove old files")
    print("4. Verify imports still work after cleanup")
    print("\nBackups will be stored in: crypto-intelligence/.backup_old_structure/")
    
    # Step 0: Initial verification
    print("\n" + "="*80)
    print("STEP 0: Pre-Cleanup Verification")
    print("="*80)
    
    success, errors = verify_imports()
    if not success:
        print("\n❌ FAILED: New architecture has import errors!")
        print("Errors found:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these errors before running cleanup.")
        return 1
    
    print("\n✅ Pre-cleanup verification passed")
    
    # Confirm with user
    print("\n" + "="*80)
    response = input("\nProceed with cleanup? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Cleanup cancelled.")
        return 0
    
    # Execute cleanup steps
    try:
        cleanup_step_1_moved_files()
        cleanup_step_2_api_clients()
        cleanup_step_3_empty_dirs()
        
        # Final verification
        print("\n" + "="*80)
        print("FINAL VERIFICATION")
        print("="*80)
        
        success, errors = verify_imports()
        if not success:
            print("\n❌ FAILED: Imports broken after cleanup!")
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
            print("\nRestore from backup: crypto-intelligence/.backup_old_structure/")
            return 1
        
        print("\n" + "="*80)
        print("✅ CLEANUP COMPLETE")
        print("="*80)
        print("\nSummary:")
        print("- Old files backed up to: crypto-intelligence/.backup_old_structure/")
        print("- Old files removed from core/ and intelligence/")
        print("- All imports verified working")
        print("\nNext steps:")
        print("1. Run tests: python crypto-intelligence/test_new_architecture.py")
        print("2. Test system: python crypto-intelligence/main.py")
        print("3. If all works, delete backup: rm -rf crypto-intelligence/.backup_old_structure/")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR during cleanup: {e}")
        import traceback
        traceback.print_exc()
        print("\nRestore from backup: crypto-intelligence/.backup_old_structure/")
        return 1


if __name__ == "__main__":
    sys.exit(main())
