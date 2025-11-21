#!/usr/bin/env python3
"""
Update CSV headers to include symbol column in PERFORMANCE and HISTORICAL tables.
"""

import csv
from pathlib import Path
from datetime import datetime

def update_performance_headers():
    """Update PERFORMANCE table headers to include symbol column."""
    
    # Find today's performance.csv
    today = datetime.now().strftime('%Y-%m-%d')
    csv_path = Path(f"crypto-intelligence/output/{today}/performance.csv")
    
    if not csv_path.exists():
        print(f"❌ Performance CSV not found: {csv_path}")
        return False
    
    print(f"📄 Found: {csv_path}")
    
    # Read all rows
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        print("❌ CSV is empty")
        return False
    
    # Check current header
    current_header = rows[0]
    print(f"Current header columns: {len(current_header)}")
    print(f"First 5 columns: {current_header[:5]}")
    
    # New header with symbol as 3rd column
    new_header = [
        'address', 'chain', 'symbol', 'first_message_id', 'start_price', 'start_time',
        'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked',
        'days_to_ath', 'peak_timing', 'day_7_price', 'day_7_multiplier', 'day_7_classification',
        'day_30_price', 'day_30_multiplier', 'day_30_classification', 'trajectory'
    ]
    
    # Check if symbol column already exists
    if 'symbol' in current_header:
        print("✅ Symbol column already exists in PERFORMANCE table")
        return True
    
    # Update header
    rows[0] = new_header
    
    # For existing data rows, insert empty symbol column at position 2
    for i in range(1, len(rows)):
        if rows[i]:
            # Insert empty symbol after chain (position 2)
            rows[i].insert(2, '')
    
    # Write back
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"✅ Updated PERFORMANCE table header (added symbol column)")
    print(f"   New header columns: {len(new_header)}")
    return True

def update_historical_headers():
    """Update HISTORICAL table headers to include symbol column."""
    
    # Find today's historical.csv
    today = datetime.now().strftime('%Y-%m-%d')
    csv_path = Path(f"crypto-intelligence/output/{today}/historical.csv")
    
    if not csv_path.exists():
        print(f"❌ Historical CSV not found: {csv_path}")
        return False
    
    print(f"📄 Found: {csv_path}")
    
    # Read all rows
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        print("❌ CSV is empty")
        return False
    
    # Check current header
    current_header = rows[0]
    print(f"Current header columns: {len(current_header)}")
    print(f"First 5 columns: {current_header[:5]}")
    
    # New header with symbol as 3rd column
    new_header = [
        'address', 'chain', 'symbol', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
        'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
    ]
    
    # Check if symbol column already exists
    if 'symbol' in current_header:
        print("✅ Symbol column already exists in HISTORICAL table")
        return True
    
    # Update header
    rows[0] = new_header
    
    # For existing data rows, insert empty symbol column at position 2
    for i in range(1, len(rows)):
        if rows[i]:
            # Insert empty symbol after chain (position 2)
            rows[i].insert(2, '')
    
    # Write back
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"✅ Updated HISTORICAL table header (added symbol column)")
    print(f"   New header columns: {len(new_header)}")
    return True

if __name__ == "__main__":
    print("="*70)
    print("CSV Header Update Script")
    print("="*70)
    print()
    
    # Update PERFORMANCE table
    print("📊 Updating PERFORMANCE table...")
    perf_success = update_performance_headers()
    print()
    
    # Update HISTORICAL table
    print("📊 Updating HISTORICAL table...")
    hist_success = update_historical_headers()
    print()
    
    print("="*70)
    if perf_success or hist_success:
        print("✅ Headers updated successfully!")
        print("🔄 Restart the system to use the new headers")
    else:
        print("⚠️  No CSV files found to update")
    print("="*70)
