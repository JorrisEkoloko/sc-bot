#!/usr/bin/env python3
"""
Fix duplicate entries in Google Sheets caused by address formatting mismatch.

This script:
1. Identifies duplicate addresses (with and without quote prefix)
2. Keeps the entry with the quote prefix (newer format)
3. Removes the old entry without the quote prefix
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.output_config import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import get_logger


async def fix_duplicates():
    """Fix duplicate entries in Google Sheets."""
    logger = get_logger(__name__)
    
    print("\n" + "="*70)
    print("Fixing Duplicate Entries in Google Sheets")
    print("="*70)
    
    # Load config
    try:
        from config.config import Config
        config = Config.from_yaml("config/config.yaml")
        output_config = config.output
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    # Initialize sheets writer
    try:
        sheets_writer = GoogleSheetsMultiTable(output_config, logger)
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets: {e}")
        return
    
    # Sheets to fix (those with address as primary key)
    sheets_to_fix = [
        ('Token Prices', 'address'),
        ('Performance', 'address'),
        ('Historical', 'address')
    ]
    
    total_duplicates_removed = 0
    
    for sheet_name, key_column in sheets_to_fix:
        print(f"\n📊 Processing {sheet_name}...")
        
        try:
            sheet = sheets_writer.sheets[sheet_name]
            
            # Get all values
            sheets_writer._rate_limit()
            all_values = sheet.get_all_values()
            
            if len(all_values) <= 1:
                print(f"   ℹ️  Sheet is empty or has only headers")
                continue
            
            # Track addresses and their row indices
            address_map = {}  # address -> list of (row_index, has_quote)
            
            for i, row in enumerate(all_values[1:], start=2):  # Skip header
                if not row or not row[0]:
                    continue
                
                address_value = row[0]
                
                # Normalize address for comparison (remove quote if present)
                normalized = address_value.lstrip("'")
                
                if normalized not in address_map:
                    address_map[normalized] = []
                
                has_quote = address_value.startswith("'")
                address_map[normalized].append((i, has_quote, address_value))
            
            # Find duplicates
            duplicates_found = 0
            rows_to_delete = []
            
            for normalized_addr, entries in address_map.items():
                if len(entries) > 1:
                    duplicates_found += 1
                    
                    # Sort: prefer entries with quote (newer format)
                    entries.sort(key=lambda x: (not x[1], x[0]))  # Quote first, then by row
                    
                    # Keep the first (with quote if available), mark others for deletion
                    keep_entry = entries[0]
                    delete_entries = entries[1:]
                    
                    print(f"   🔍 Found duplicate: {normalized_addr[:20]}...")
                    print(f"      Keeping row {keep_entry[0]}: {keep_entry[2][:30]}...")
                    
                    for entry in delete_entries:
                        print(f"      Deleting row {entry[0]}: {entry[2][:30]}...")
                        rows_to_delete.append(entry[0])
            
            if not rows_to_delete:
                print(f"   ✅ No duplicates found in {sheet_name}")
                continue
            
            # Delete rows (in reverse order to maintain indices)
            rows_to_delete.sort(reverse=True)
            
            print(f"\n   🗑️  Deleting {len(rows_to_delete)} duplicate rows...")
            
            for row_index in rows_to_delete:
                try:
                    sheets_writer._rate_limit()
                    sheet.delete_rows(row_index)
                    logger.info(f"Deleted row {row_index} from {sheet_name}")
                except Exception as e:
                    logger.error(f"Failed to delete row {row_index}: {e}")
            
            total_duplicates_removed += len(rows_to_delete)
            print(f"   ✅ Removed {len(rows_to_delete)} duplicates from {sheet_name}")
            
        except Exception as e:
            logger.error(f"Error processing {sheet_name}: {e}")
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print(f"Total duplicate rows removed: {total_duplicates_removed}")
    print("\n✅ Duplicate cleanup complete!")
    print("\nℹ️  Going forward, the system will:")
    print("   • Use quote-prefixed addresses for all new entries")
    print("   • Properly update existing entries instead of creating duplicates")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(fix_duplicates())
