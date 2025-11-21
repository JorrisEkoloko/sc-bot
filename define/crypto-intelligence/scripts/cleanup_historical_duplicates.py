"""
Script to remove duplicate rows from Historical sheet in Google Sheets.

This script identifies and removes duplicate historical entries based on
the address key (case-insensitive), keeping only the most recent entry.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.output_config import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger


def cleanup_historical_duplicates():
    """Remove duplicate rows from Historical sheet."""
    logger = setup_logger('CleanupHistorical')
    
    try:
        # Load config
        config = OutputConfig()
        
        if not config.google_sheets_enabled:
            logger.error("Google Sheets is not enabled in config")
            return
        
        # Initialize sheets writer
        logger.info("Connecting to Google Sheets...")
        sheets_writer = GoogleSheetsMultiTable(config, logger)
        
        # Get Historical sheet
        sheet = sheets_writer.sheets.get('Historical')
        if not sheet:
            logger.error("Historical sheet not found")
            return
        
        logger.info("Fetching all rows from Historical sheet...")
        all_values = sheet.get_all_values()
        
        if len(all_values) <= 1:
            logger.info("No data rows found (only header)")
            return
        
        # Header row
        header = all_values[0]
        logger.info(f"Header: {header[:4]}")  # Show first 4 columns
        
        # Track unique rows by address (case-insensitive)
        seen_keys = {}
        rows_to_keep = [header]  # Start with header
        duplicates_found = 0
        
        # Process data rows (skip header)
        for i, row in enumerate(all_values[1:], start=2):
            if not row or len(row) < 1:
                continue
            
            # Extract address (column 0)
            address = str(row[0]).strip()
            
            # Normalize address (remove leading quote, lowercase)
            if address.startswith("'"):
                address = address[1:]
            address = address.lower()
            
            if address in seen_keys:
                duplicates_found += 1
                logger.debug(f"Duplicate found at row {i}: {address[:20]}...")
            else:
                seen_keys[address] = True
                rows_to_keep.append(row)
        
        logger.info(f"Total rows: {len(all_values) - 1}")
        logger.info(f"Unique rows: {len(rows_to_keep) - 1}")
        logger.info(f"Duplicates found: {duplicates_found}")
        
        if duplicates_found == 0:
            logger.info("No duplicates found. Sheet is clean!")
            return
        
        # Ask for confirmation
        print(f"\nFound {duplicates_found} duplicate rows.")
        print(f"Will keep {len(rows_to_keep) - 1} unique rows.")
        response = input("Do you want to remove duplicates? (yes/no): ").strip().lower()
        
        if response != 'yes':
            logger.info("Operation cancelled by user")
            return
        
        # Clear sheet and rewrite with unique rows
        logger.info("Clearing Historical sheet...")
        sheet.clear()
        
        logger.info("Writing unique rows back to sheet...")
        # Write in batches to avoid rate limits
        batch_size = 100
        for i in range(0, len(rows_to_keep), batch_size):
            batch = rows_to_keep[i:i + batch_size]
            sheet.append_rows(batch)
            logger.info(f"Wrote batch {i // batch_size + 1} ({len(batch)} rows)")
        
        logger.info(f"✓ Cleanup complete! Removed {duplicates_found} duplicates.")
        logger.info(f"✓ Historical sheet now has {len(rows_to_keep) - 1} unique rows.")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


if __name__ == "__main__":
    cleanup_historical_duplicates()
