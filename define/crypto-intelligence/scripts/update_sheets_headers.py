#!/usr/bin/env python3
"""
Update Google Sheets headers to include symbol column in PERFORMANCE and HISTORICAL tables.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.output_config import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger


async def update_sheets_headers():
    """Update Google Sheets headers to include symbol column."""
    
    logger = setup_logger('UpdateSheetsHeaders')
    
    # Load config from environment
    config = OutputConfig.load_from_env()
    
    if not config.google_sheets_enabled:
        logger.error("Google Sheets is not enabled in config")
        return False
    
    try:
        # Initialize sheets writer
        logger.info("Connecting to Google Sheets...")
        sheets_writer = GoogleSheetsMultiTable(config, logger)
        
        # Update PERFORMANCE sheet header
        logger.info("Updating PERFORMANCE sheet header...")
        perf_sheet = sheets_writer.sheets.get('Performance')
        if perf_sheet:
            new_header = [
                'address', 'chain', 'symbol', 'first_message_id', 'start_price', 'start_time',
                'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked',
                'days_to_ath', 'peak_timing', 'day_7_price', 'day_7_multiplier', 'day_7_classification',
                'day_30_price', 'day_30_multiplier', 'day_30_classification', 'trajectory'
            ]
            
            # Get current data
            sheets_writer._rate_limit()
            all_values = perf_sheet.get_all_values()
            
            if all_values:
                current_header = all_values[0]
                logger.info(f"Current PERFORMANCE header: {len(current_header)} columns")
                
                # Check if symbol already exists
                if 'symbol' in current_header:
                    logger.info("✅ Symbol column already exists in PERFORMANCE sheet")
                else:
                    # Update header row
                    sheets_writer._rate_limit()
                    perf_sheet.update('A1:T1', [new_header])
                    logger.info(f"✅ Updated PERFORMANCE header to {len(new_header)} columns")
                    
                    # Update existing data rows to insert empty symbol column at position 2
                    if len(all_values) > 1:
                        logger.info(f"Updating {len(all_values)-1} data rows...")
                        for i in range(1, len(all_values)):
                            if all_values[i] and len(all_values[i]) >= 2:
                                # Insert empty symbol after chain (position 2)
                                all_values[i].insert(2, '')
                        
                        # Write back all data
                        sheets_writer._rate_limit()
                        perf_sheet.update(f'A1:T{len(all_values)}', all_values)
                        logger.info(f"✅ Updated {len(all_values)-1} data rows")
        else:
            logger.warning("Performance sheet not found")
        
        # Update HISTORICAL sheet header
        logger.info("Updating HISTORICAL sheet header...")
        hist_sheet = sheets_writer.sheets.get('Historical')
        if hist_sheet:
            new_header = [
                'address', 'chain', 'symbol', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
                'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
            ]
            
            # Get current data
            sheets_writer._rate_limit()
            all_values = hist_sheet.get_all_values()
            
            if all_values:
                current_header = all_values[0]
                logger.info(f"Current HISTORICAL header: {len(current_header)} columns")
                
                # Check if symbol already exists
                if 'symbol' in current_header:
                    logger.info("✅ Symbol column already exists in HISTORICAL sheet")
                else:
                    # Update header row
                    sheets_writer._rate_limit()
                    hist_sheet.update('A1:I1', [new_header])
                    logger.info(f"✅ Updated HISTORICAL header to {len(new_header)} columns")
                    
                    # Update existing data rows to insert empty symbol column at position 2
                    if len(all_values) > 1:
                        logger.info(f"Updating {len(all_values)-1} data rows...")
                        for i in range(1, len(all_values)):
                            if all_values[i] and len(all_values[i]) >= 2:
                                # Insert empty symbol after chain (position 2)
                                all_values[i].insert(2, '')
                        
                        # Write back all data
                        sheets_writer._rate_limit()
                        hist_sheet.update(f'A1:I{len(all_values)}', all_values)
                        logger.info(f"✅ Updated {len(all_values)-1} data rows")
            else:
                logger.info("HISTORICAL sheet is empty, header will be created on first write")
        else:
            logger.warning("Historical sheet not found")
        
        logger.info("✅ Google Sheets headers updated successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update Google Sheets headers: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Change to crypto-intelligence directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print("="*70)
    print("Google Sheets Header Update Script")
    print("="*70)
    print()
    
    success = asyncio.run(update_sheets_headers())
    
    print()
    print("="*70)
    if success:
        print("✅ Headers updated successfully!")
        print("🔄 New data will include symbol column")
    else:
        print("❌ Failed to update headers")
    print("="*70)
