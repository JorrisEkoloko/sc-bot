"""
Enhanced data reset script for fresh production scraping.

This script provides comprehensive data cleanup with backup and selective reset options.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime


def backup_data(base_dir):
    """Create timestamped backup of all data."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = base_dir / 'data' / f'.backup_{timestamp}'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to backup
    backup_files = [
        'data/reputation/channels.json',
        'data/reputation/signal_outcomes.json',
        'data/reputation/active_tracking.json',
        'data/reputation/completed_history.json',
        'data/reputation/coins_cross_channel.json',
        'data/cache/historical_prices.json',
        'data/symbol_mapping.json',
        'data/dead_tokens_blacklist.json',
    ]
    
    backed_up = []
    for file_path in backup_files:
        full_path = base_dir / file_path
        if full_path.exists():
            dest = backup_dir / Path(file_path).name
            shutil.copy2(full_path, dest)
            backed_up.append(file_path)
    
    return backup_dir, backed_up


def reset_reputation_data(base_dir):
    """Reset reputation and tracking data."""
    reputation_dir = base_dir / 'data' / 'reputation'
    
    files_to_reset = {
        'channels.json': {},
        'signal_outcomes.json': {},
        'active_tracking.json': {},
        'completed_history.json': {},
        'coins_cross_channel.json': {}
    }
    
    for filename, default_content in files_to_reset.items():
        file_path = reputation_dir / filename
        with open(file_path, 'w') as f:
            json.dump(default_content, f, indent=2)
    
    return list(files_to_reset.keys())


def reset_cache_data(base_dir):
    """Reset cache data."""
    cache_dir = base_dir / 'data' / 'cache'
    
    files_to_reset = {
        'historical_prices.json': {}
    }
    
    for filename, default_content in files_to_reset.items():
        file_path = cache_dir / filename
        with open(file_path, 'w') as f:
            json.dump(default_content, f, indent=2)
    
    return list(files_to_reset.keys())


def reset_output_data(base_dir):
    """Clear output CSV files."""
    output_dir = base_dir / 'output'
    
    cleared = []
    if output_dir.exists():
        for date_dir in output_dir.iterdir():
            if date_dir.is_dir():
                shutil.rmtree(date_dir)
                cleared.append(str(date_dir))
    
    return cleared


def reset_scraped_channels(base_dir):
    """Reset scraped channels tracking."""
    file_path = base_dir / 'data' / 'scraped_channels.json'
    
    if file_path.exists():
        with open(file_path, 'w') as f:
            json.dump({}, f, indent=2)
        return True
    return False


def keep_essential_data(base_dir):
    """Keep essential data that shouldn't be reset."""
    essential_files = [
        'data/symbol_mapping.json',
        'data/dead_tokens_blacklist.json',
        'data/dead_tokens_analysis.json',
    ]
    
    kept = []
    for file_path in essential_files:
        full_path = base_dir / file_path
        if full_path.exists():
            kept.append(file_path)
    
    return kept


def main():
    """Main reset function."""
    print("="*80)
    print("ENHANCED DATA RESET - Production Scraping Preparation")
    print("="*80)
    print()
    
    base_dir = Path(__file__).parent.parent
    
    # Step 1: Backup
    print("📦 Step 1: Creating backup...")
    backup_dir, backed_up = backup_data(base_dir)
    print(f"   ✅ Backup created: {backup_dir}")
    print(f"   📁 Backed up {len(backed_up)} files")
    print()
    
    # Step 2: Reset reputation data
    print("🔄 Step 2: Resetting reputation data...")
    reset_files = reset_reputation_data(base_dir)
    print(f"   ✅ Reset {len(reset_files)} reputation files")
    for f in reset_files:
        print(f"      - {f}")
    print()
    
    # Step 3: Reset cache
    print("🔄 Step 3: Resetting cache...")
    cache_files = reset_cache_data(base_dir)
    print(f"   ✅ Reset {len(cache_files)} cache files")
    for f in cache_files:
        print(f"      - {f}")
    print()
    
    # Step 4: Clear output
    print("🔄 Step 4: Clearing output files...")
    cleared = reset_output_data(base_dir)
    print(f"   ✅ Cleared {len(cleared)} output directories")
    print()
    
    # Step 5: Reset scraped channels
    print("🔄 Step 5: Resetting scraped channels tracking...")
    if reset_scraped_channels(base_dir):
        print("   ✅ Scraped channels tracking reset")
    else:
        print("   ℹ️  No scraped channels file found")
    print()
    
    # Step 6: Keep essential data
    print("💾 Step 6: Preserving essential data...")
    kept = keep_essential_data(base_dir)
    print(f"   ✅ Kept {len(kept)} essential files:")
    for f in kept:
        print(f"      - {f}")
    print()
    
    # Summary
    print("="*80)
    print("RESET COMPLETE")
    print("="*80)
    print()
    print("✅ System is ready for fresh production scraping")
    print()
    print("📋 Next Steps:")
    print("   1. Update config/channels.json with your production channels")
    print("   2. Run: python main.py")
    print("   3. Monitor data/reputation/ for channel performance")
    print()
    print(f"💾 Backup location: {backup_dir}")
    print("   (You can restore from this backup if needed)")
    print()
    print("="*80)


if __name__ == '__main__':
    main()
