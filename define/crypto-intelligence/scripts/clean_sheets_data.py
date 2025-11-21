"""
Clean Google Sheets data only (preserve headers).

This script clears all data rows from Google Sheets while keeping the header rows intact.
Useful for resetting the sheets without losing the structure.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger


def clean_sheets_data():
    """Clear all data from Google Sheets (keep headers)."""
    
    print()
    print("=" * 80)
    print("CLEAN GOOGLE SHEETS DATA")
    print("=" * 80)
    
    # Initialize logger
    logger = setup_logger('DataCleaner')
    
    # Load config
    config = OutputConfig.load_from_env()
    
    # Check if Google Sheets is enabled
    if not config.google_sheets_enabled:
        print("⚠️  Google Sheets is disabled in .env file")
        print("   Set GOOGLE_SHEETS_ENABLED=true to enable")
        return
    
    # Connect to Google Sheets
    print("🔐 Authenticating with Google Sheets...")
    sheets = GoogleSheetsMultiTable(config, logger)
    print("✅ Connected to Google Sheets")
    
    # List of all sheets to clean
    sheet_names = [
        sheets.MESSAGES_SHEET,
        sheets.TOKEN_PRICES_SHEET,
        sheets.PERFORMANCE_SHEET,
        sheets.HISTORICAL_SHEET,
        sheets.CHANNEL_RANKINGS_SHEET,
        sheets.CHANNEL_COIN_PERFORMANCE_SHEET,
        sheets.COIN_CROSS_CHANNEL_SHEET,
        sheets.PREDICTION_ACCURACY_SHEET
    ]
    
    print()
    print("📊 Clearing all sheet data (keeping headers)...")
    
    for sheet_name in sheet_names:
        try:
            sheet = sheets.sheets[sheet_name]
            
            # Get all values
            sheets._rate_limit()
            all_values = sheet.get_all_values()
            
            # Count data rows (excluding header)
            data_row_count = len(all_values) - 1 if len(all_values) > 1 else 0
            
            if data_row_count > 0:
                print(f"📝 Clearing {sheet_name} sheet...")
                
                # Delete all rows except header (row 1)
                # Delete from row 2 to the last row
                sheets._rate_limit()
                sheet.delete_rows(2, len(all_values))
                
                print(f"   ✅ Cleared {data_row_count} rows (kept headers)")
            else:
                print(f"📝 Clearing {sheet_name} sheet...")
                print(f"   ✅ Cleared 0 rows (kept headers)")
                
        except Exception as e:
            logger.error(f"Failed to clear {sheet_name}: {e}")
            print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print("✅ All Google Sheets data cleared (headers preserved)")
    print("   Ready for fresh production scraping!")
    print()


if __name__ == "__main__":
    clean_sheets_data()
