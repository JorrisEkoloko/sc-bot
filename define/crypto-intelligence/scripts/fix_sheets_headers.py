"""
Fix Google Sheets column headers.

This script resets all sheet headers to match the correct column definitions.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.output_config import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger

# Load environment
load_dotenv()


# Column definitions (from data_output.py)
SHEET_HEADERS = {
    'Messages': [
        'message_id', 'timestamp', 'channel_name', 'message_text',
        'hdrb_score', 'crypto_mentions', 'sentiment', 'confidence',
        'forwards', 'reactions', 'replies', 'views',
        'channel_reputation_score', 'channel_reputation_tier', 
        'channel_expected_roi', 'prediction_source'
    ],
    
    'Token Prices': [
        'address', 'chain', 'symbol', 'price_usd', 'market_cap',
        'volume_24h', 'price_change_24h', 'liquidity_usd', 'pair_created_at',
        'market_tier', 'risk_level', 'risk_score',
        'liquidity_ratio', 'volume_ratio', 'data_completeness'
    ],
    
    'Performance': [
        'address', 'chain', 'first_message_id', 'start_price', 'start_time',
        'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked',
        'days_to_ath', 'peak_timing', 'day_7_price', 'day_7_multiplier', 'day_7_classification',
        'day_30_price', 'day_30_multiplier', 'day_30_classification', 'trajectory'
    ],
    
    'Historical': [
        'address', 'chain', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
        'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
    ],
    
    'Channel Rankings': [
        'rank', 'channel_name', 'total_signals', 'win_rate',
        'avg_roi', 'median_roi', 'best_roi', 'worst_roi',
        'expected_roi', 'sharpe_ratio', 'speed_score',
        'reputation_score', 'reputation_tier',
        'total_predictions', 'prediction_accuracy', 'mean_absolute_error',
        'mean_squared_error', 'first_signal_date', 'last_signal_date', 'last_updated'
    ],
    
    'Channel Coin Performance': [
        'channel_name', 'coin_symbol', 'mentions',
        'avg_roi', 'expected_roi', 'win_rate',
        'best_roi', 'worst_roi', 'prediction_accuracy',
        'sharpe_ratio', 'last_mentioned', 'days_since_last_mention',
        'recommendation'
    ],
    
    'Coin Cross Channel': [
        'coin_symbol', 'total_mentions', 'total_channels',
        'avg_roi_all_channels', 'median_roi_all_channels',
        'best_channel', 'best_channel_roi', 'best_channel_mentions',
        'worst_channel', 'worst_channel_roi', 'worst_channel_mentions',
        'consensus_strength', 'recommendation'
    ],
    
    'Prediction Accuracy': [
        'channel_name', 'total_predictions', 'correct_predictions',
        'accuracy_percentage', 'mean_absolute_error', 'mean_squared_error',
        'overestimations', 'underestimations', 'avg_error_magnitude'
    ]
}


async def fix_sheet_headers(sheets_writer, sheet_name, headers):
    """Fix headers for a single sheet."""
    try:
        print(f"\n📝 Fixing {sheet_name}...")
        print(f"   Expected columns: {len(headers)}")
        
        # Get current headers
        current_headers = await sheets_writer.get_sheet_headers(sheet_name)
        
        if current_headers:
            print(f"   Current columns: {len(current_headers)}")
            
            # Compare
            missing = set(headers) - set(current_headers)
            extra = set(current_headers) - set(headers)
            
            if missing:
                print(f"   ⚠️  Missing columns: {', '.join(missing)}")
            if extra:
                print(f"   ⚠️  Extra columns: {', '.join(extra)}")
        else:
            print(f"   ⚠️  No headers found (empty sheet)")
        
        # Update headers (row 1)
        await sheets_writer.update_sheet_headers(sheet_name, headers)
        
        print(f"   ✅ Headers updated successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def main():
    """Main function."""
    print("="*80)
    print("GOOGLE SHEETS HEADER FIX")
    print("="*80)
    print()
    
    # Initialize config
    config = OutputConfig.load_from_env()
    logger = setup_logger('SheetsHeaderFix')
    
    if not config.google_sheets_enabled:
        print("❌ Google Sheets is not enabled in config")
        print("   Set GOOGLE_SHEETS_ENABLED=true in .env")
        return
    
    print(f"📊 Spreadsheet: {config.google_spreadsheet_name}")
    print()
    
    # Initialize sheets writer
    try:
        sheets_writer = GoogleSheetsMultiTable(config, logger)
        print("✅ Connected to Google Sheets")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Google Sheets: {e}")
        return
    
    # Fix headers for each sheet
    results = {}
    for sheet_name, headers in SHEET_HEADERS.items():
        success = await fix_sheet_headers(sheets_writer, sheet_name, headers)
        results[sheet_name] = success
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    print(f"✅ Successfully fixed: {successful}/{len(results)} sheets")
    if failed > 0:
        print(f"❌ Failed: {failed} sheets")
        print()
        print("Failed sheets:")
        for sheet_name, success in results.items():
            if not success:
                print(f"  - {sheet_name}")
    
    print()
    print("="*80)
    print()
    print("💡 Next steps:")
    print("   1. Open your Google Sheet to verify headers")
    print("   2. Check that data is still intact (headers only changed)")
    print("   3. Run main.py to continue tracking")
    print()


if __name__ == '__main__':
    asyncio.run(main())
