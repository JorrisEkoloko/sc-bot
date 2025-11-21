"""
Master script to remove duplicate rows from all Google Sheets tables.

This script cleans up duplicates in:
- Performance (composite key: address + first_message_id)
- Token Prices (single key: address)
- Historical (single key: address)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.output_config import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger


def cleanup_sheet_duplicates(sheet, sheet_name: str, key_columns: list, logger):
    """
    Generic function to clean up duplicates from a sheet.
    
    Args:
        sheet: Google Sheet object
        sheet_name: Name of the sheet
        key_columns: List of column indices that form the unique key
        logger: Logger instance
        
    Returns:
        Number of duplicates removed
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing {sheet_name} sheet...")
    logger.info(f"{'='*60}")
    
    all_values = sheet.get_all_values()
    
    if len(all_values) <= 1:
        logger.info("No data rows found (only header)")
        return 0
    
    # Header row
    header = all_values[0]
    logger.info(f"Columns: {', '.join(header[:5])}...")
    
    # Track unique rows by composite key
    seen_keys = {}
    rows_to_keep = [header]  # Start with header
    duplicates_found = 0
    
    # Process data rows (skip header)
    for i, row in enumerate(all_values[1:], start=2):
        if not row or len(row) <= max(key_columns):
            continue
        
        # Extract composite key from specified columns
        key_parts = []
        for col_idx in key_columns:
            if col_idx < len(row):
                value = str(row[col_idx]).strip()
                # Normalize (remove leading quote if present)
                if value.startswith("'"):
                    value = value[1:]
                key_parts.append(value)
            else:
                key_parts.append('')
        
        composite_key = '|'.join(key_parts)
        
        if composite_key in seen_keys:
            duplicates_found += 1
            logger.debug(f"Duplicate found at row {i}: {composite_key[:80]}...")
        else:
            seen_keys[composite_key] = True
            rows_to_keep.append(row)
    
    logger.info(f"Total rows: {len(all_values) - 1}")
    logger.info(f"Unique rows: {len(rows_to_keep) - 1}")
    logger.info(f"Duplicates found: {duplicates_found}")
    
    if duplicates_found == 0:
        logger.info("✓ No duplicates found. Sheet is clean!")
        return 0
    
    # Ask for confirmation
    print(f"\n{sheet_name}: Found {duplicates_found} duplicate rows.")
    print(f"Will keep {len(rows_to_keep) - 1} unique rows.")
    response = input(f"Remove duplicates from {sheet_name}? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("Skipped by user")
        return 0
    
    # Clear sheet and rewrite with unique rows
    logger.info(f"Clearing {sheet_name} sheet...")
    sheet.clear()
    
    logger.info("Writing unique rows back to sheet...")
    # Write in batches to avoid rate limits
    batch_size = 100
    for i in range(0, len(rows_to_keep), batch_size):
        batch = rows_to_keep[i:i + batch_size]
        sheet.append_rows(batch)
        logger.info(f"Wrote batch {i // batch_size + 1} ({len(batch)} rows)")
    
    logger.info(f"✓ Cleanup complete! Removed {duplicates_found} duplicates.")
    
    return duplicates_found


def cleanup_all_duplicates():
    """Remove duplicate rows from all sheets."""
    logger = setup_logger('CleanupAllDuplicates')
    
    try:
        # Load config
        config = OutputConfig()
        
        if not config.google_sheets_enabled:
            logger.error("Google Sheets is not enabled in config")
            return
        
        # Initialize sheets writer
        logger.info("Connecting to Google Sheets...")
        sheets_writer = GoogleSheetsMultiTable(config, logger)
        
        total_duplicates = 0
        
        # Define sheets and their key columns
        sheets_config = [
            ('Performance', [0, 3]),      # address (col 0) + first_message_id (col 3)
            ('Token Prices', [0]),        # address (col 0)
            ('Historical', [0]),          # address (col 0)
        ]
        
        for sheet_name, key_columns in sheets_config:
            sheet = sheets_writer.sheets.get(sheet_name)
            if not sheet:
                logger.warning(f"{sheet_name} sheet not found, skipping...")
                continue
            
            try:
                duplicates = cleanup_sheet_duplicates(sheet, sheet_name, key_columns, logger)
                total_duplicates += duplicates
            except Exception as e:
                logger.error(f"Error cleaning {sheet_name}: {e}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total duplicates removed across all sheets: {total_duplicates}")
        logger.info(f"✓ All cleanup operations complete!")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


if __name__ == "__main__":
    cleanup_all_duplicates()
