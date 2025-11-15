"""Clean all data files for a fresh system run.

This script backs up existing data and clears all tracking/reputation data
so you can see the system work from scratch.
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path


def backup_data():
    """Backup existing data to timestamped folder."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f'data/.backup_{timestamp}')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Creating backup in: {backup_dir}")
    
    # Backup data files
    data_files = [
        'data/reputation/signal_outcomes.json',
        'data/reputation/channels.json',
        'data/reputation/coins_cross_channel.json',
        'data/reputation/active_tracking.json',
        'data/reputation/completed_history.json',
        'data/performance/tracking.json',
        'data/cache/historical_prices.json',
        'data/scraped_channels.json'
    ]
    
    for file_path in data_files:
        src = Path(file_path)
        if src.exists():
            dst = backup_dir / src.name
            shutil.copy2(src, dst)
            print(f"  ✓ Backed up: {src.name}")
    
    print(f"✅ Backup complete!\n")
    return backup_dir


def clean_data_files():
    """Clean all data files."""
    print("🧹 Cleaning data files...")
    
    # Files to reset with empty structures
    files_to_reset = {
        'data/reputation/signal_outcomes.json': {},
        'data/reputation/channels.json': {},
        'data/reputation/coins_cross_channel.json': {},
        'data/reputation/active_tracking.json': {},
        'data/reputation/completed_history.json': {},
        'data/performance/tracking.json': {},
        'data/cache/historical_prices.json': {},
        'data/scraped_channels.json': {}
    }
    
    for file_path, empty_content in files_to_reset.items():
        path = Path(file_path)
        if path.exists():
            with open(path, 'w') as f:
                json.dump(empty_content, f, indent=2)
            print(f"  ✓ Cleaned: {file_path}")
    
    print("✅ Data files cleaned!\n")


def clean_output_files():
    """Clean output CSV files."""
    print("🧹 Cleaning output files...")
    
    output_dir = Path('output')
    if output_dir.exists():
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  ✓ Removed: {item}")
    
    print("✅ Output files cleaned!\n")


def main():
    """Main cleanup process."""
    print("=" * 60)
    print("🔄 FRESH DATA CLEANUP")
    print("=" * 60)
    print()
    
    # Backup first
    backup_dir = backup_data()
    
    # Clean data
    clean_data_files()
    clean_output_files()
    
    print("=" * 60)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 60)
    print()
    print(f"📦 Backup saved to: {backup_dir}")
    print("🚀 Ready for fresh run: python main.py")
    print()


if __name__ == '__main__':
    main()
