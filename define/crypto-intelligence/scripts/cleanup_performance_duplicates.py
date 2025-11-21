"""
Script to remove duplicate rows from Performance sheet in Google Sheets.

This script identifies and removes duplicate performance entries based on
the composite key (address, first_message_id), keeping only the most recent entry.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.output_config import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger


def cleanup_performance_duplicates():
    """Remove duplicate rows from Performance sheet."""
    logger = setup_logger('CleanupDuplicates')
    
    try:
        # Load config
        config = OutputConfig()
        
        if not config.google_sheets_enabled:
            logger.error("Google Sheets is not enabled in config")
            return
        
        # Initialize sheets writer
        logger.info("Connecting to Google Sheets...")
        sheets_writer = GoogleSheetsMultiTable(config, logger)
        
        # Get Performance sheet
        sheet = sheets_writer.sheets.get('Performance')
        if not sheet:
            logger.error("Performance sheet not found")
            return
        
        logger.info("Fetching all rows from Performance sheet...")
        all_values = sheet.get_all_values()
        
        if len(all_values) <= 1:
            logger.info("No data rows found (only header)")
            return
        
        # Header row
        header = all_values[0]
        logger.info(f"Header: {header[:4]}")  # Show first 4 columns
        
        # Track unique rows by composite key (address, message_id)
        seen_keys = {}
        rows_to_keep = [header]  # Start with header
        duplicates_found = 0
        
        # Process data rows (skip header)
        for i, row in enumerate(all_values[1:], start=2):
            if not row or len(row) < 4:
                continue
            
            # Extract composite key (address at col 0, symbol at col 2, first_message_id at col 3)
            address = str(row[0]).strip()
            symbol = str(row[2]).strip() if len(row) > 2 else ''
            message_id = str(row[3]).strip() if len(row) > 3 else ''
            
            # Normalize address (remove leading quote if present, lowercase)
            if address.startswith("'"):
                address = address[1:]
            address = address.lower()
            
            # Normalize symbol (remove leading quote if present, uppercase)
            if symbol.startswith("'"):
                symbol = symbol[1:]
            symbol = symbol.upper()
            
            # Normalize message_id (remove leading quote if present, keep as-is)
            if message_id.startswith("'"):
                message_id = message_id[1:]
            
            composite_key = f"{address}|{symbol}|{message_id}"
            
            if composite_key in seen_keys:
                duplicates_found += 1
                logger.debug(f"Duplicate found at row {i}: {composite_key[:50]}...")
            else:
                seen_keys[composite_key] = True
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
        logger.info("Clearing Performance sheet...")
        sheet.clear()
        
        logger.info("Writing unique rows back to sheet...")
        # Write in batches to avoid rate limits
        batch_size = 100
        for i in range(0, len(rows_to_keep), batch_size):
            batch = rows_to_keep[i:i + batch_size]
            sheet.append_rows(batch)
            logger.info(f"Wrote batch {i // batch_size + 1} ({len(batch)} rows)")
        
        logger.info(f"✓ Cleanup complete! Removed {duplicates_found} duplicates.")
        logger.info(f"✓ Performance sheet now has {len(rows_to_keep) - 1} unique rows.")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


if __name__ == "__main__":
    cleanup_performance_duplicates()
