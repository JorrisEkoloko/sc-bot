"""
Clean all data files for a fresh historical scrape.

This script removes:
1. Performance tracking data
2. Signal outcomes data
3. Channel reputation data
4. Cross-channel coin data
5. Scraped channels tracking
6. Output CSV files (messages, performance, historical, token_prices)
7. Cached historical prices
8. Test output files

Use this when:
- Starting a fresh scrape
- After fixing coin mention detection (to remove false positives)
- Resetting all tracking and reputation data
"""
import os
import shutil
from pathlib import Path


def clean_data_for_fresh_scrape():
    """Remove all data files to start fresh."""
    
    print("=" * 80)
    print("CLEANING DATA FOR FRESH SCRAPE")
    print("=" * 80)
    print()
    
    # Base directory
    base_dir = Path(__file__).parent.parent
    
    # Files to delete
    files_to_delete = [
        "data/scraped_channels.json",
        "data/tracking_data.json",
        "data/performance/tracking.json",
        "data/reputation/signal_outcomes.json",
        "data/reputation/channels.json",
        "data/reputation/coins_cross_channel.json",
        "data/cache/historical_prices.json"
    ]
    
    # Directories to delete (output files with potentially bad coin mentions)
    dirs_to_delete = [
        "output",
        "../output_test"  # Test output directory
    ]
    
    # Delete files
    print("Deleting data files:")
    for file_path in files_to_delete:
        full_path = base_dir / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                print(f"  ✓ Deleted: {file_path}")
            except Exception as e:
                print(f"  ✗ Failed to delete {file_path}: {e}")
        else:
            print(f"  - Not found: {file_path}")
    
    print()
    
    # Delete directories
    print("Deleting output directories:")
    for dir_path in dirs_to_delete:
        full_path = base_dir / dir_path
        if full_path.exists():
            try:
                shutil.rmtree(full_path)
                print(f"  ✓ Deleted: {dir_path}/")
            except Exception as e:
                print(f"  ✗ Failed to delete {dir_path}: {e}")
        else:
            print(f"  - Not found: {dir_path}/")
    
    print()
    print("=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print()
    print("All old data with potentially incorrect coin mentions has been removed.")
    print("The improved ambiguous ticker detection is now active.")
    print()
    print("You can now run a fresh historical scrape:")
    print("  python scripts/historical_scraper.py --channel erics_calls --limit 100")
    print()
    print("Note: Ambiguous tickers (ONE, LINK, NEAR, etc.) now require $ or # prefix")
    print("      See QUICK_REFERENCE_AMBIGUOUS_TICKERS.md for details")
    print()


if __name__ == "__main__":
    # Ask for confirmation
    print()
    print("⚠️  WARNING: This will delete all data files including:")
    print("   - All output CSV files (messages, performance, historical)")
    print("   - All tracking and reputation data")
    print("   - Cached historical prices")
    print("   - Test output files")
    print()
    print("This is useful after fixing coin mention detection to remove false positives.")
    print()
    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    
    if response == "yes":
        clean_data_for_fresh_scrape()
    else:
        print("Cleanup cancelled.")
