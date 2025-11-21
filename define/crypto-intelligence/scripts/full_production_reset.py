"""
Full production reset - Clear all data, keep only headers.

This script prepares the system for a fresh production scrape by:
1. Backing up all existing data
2. Clearing all CSV files (keeping headers)
3. Clearing all Google Sheets (keeping headers)
4. Resetting all tracking/reputation data
5. Preserving essential configuration
"""
import json
import shutil
import gspread
from pathlib import Path
from datetime import datetime
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# Sheet headers (from data_output.py)
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


def authenticate_sheets():
    """Authenticate with Google Sheets using OAuth."""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = None
    
    token_path = Path('credentials/token.json')
    creds_path = Path('credentials/oauth_credentials.json')
    
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return gspread.authorize(creds)


def backup_all_data(base_dir):
    """Create comprehensive backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = base_dir / 'data' / f'.backup_production_reset_{timestamp}'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print("📦 Creating backup...")
    
    # Backup data files
    data_files = [
        'data/reputation/channels.json',
        'data/reputation/signal_outcomes.json',
        'data/reputation/active_tracking.json',
        'data/reputation/completed_history.json',
        'data/reputation/coins_cross_channel.json',
        'data/cache/historical_prices.json',
        'data/performance/tracking.json',
    ]
    
    backed_up = []
    for file_path in data_files:
        full_path = base_dir / file_path
        if full_path.exists():
            dest = backup_dir / Path(file_path).name
            shutil.copy2(full_path, dest)
            backed_up.append(file_path)
    
    # Backup CSV files
    output_dir = base_dir / 'output'
    if output_dir.exists():
        for date_dir in output_dir.iterdir():
            if date_dir.is_dir():
                dest_dir = backup_dir / 'output' / date_dir.name
                dest_dir.mkdir(parents=True, exist_ok=True)
                for csv_file in date_dir.glob('*.csv'):
                    shutil.copy2(csv_file, dest_dir / csv_file.name)
                    backed_up.append(str(csv_file.relative_to(base_dir)))
    
    print(f"   ✅ Backup created: {backup_dir}")
    print(f"   📁 Backed up {len(backed_up)} files")
    
    return backup_dir


def clear_csv_files(base_dir):
    """Clear all CSV files, keep only headers."""
    print("\n🗑️  Clearing CSV files...")
    
    output_dir = base_dir / 'output'
    
    if output_dir.exists():
        # Remove all date directories
        for date_dir in output_dir.iterdir():
            if date_dir.is_dir():
                shutil.rmtree(date_dir)
                print(f"   ✅ Removed: {date_dir.name}")
    
    # Create fresh output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"   ✅ CSV files cleared")


def clear_google_sheets(client, spreadsheet_name):
    """Clear all Google Sheets data, keep only headers."""
    print("\n🗑️  Clearing Google Sheets...")
    
    try:
        spreadsheet = client.open(spreadsheet_name)
        
        for sheet_name, headers in SHEET_HEADERS.items():
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                
                # Get current row count
                all_values = worksheet.get_all_values()
                row_count = len(all_values)
                
                if row_count > 1:
                    # Clear all data except row 1 (headers)
                    worksheet.delete_rows(2, row_count)
                    print(f"   ✅ {sheet_name}: Cleared {row_count - 1} rows")
                else:
                    print(f"   ℹ️  {sheet_name}: Already empty")
                
                # Ensure headers are correct
                worksheet.update('A1', [headers])
                
            except gspread.WorksheetNotFound:
                print(f"   ⚠️  {sheet_name}: Sheet not found")
            except Exception as e:
                print(f"   ❌ {sheet_name}: Error - {e}")
        
        print(f"   ✅ Google Sheets cleared")
        
    except Exception as e:
        print(f"   ❌ Error accessing Google Sheets: {e}")


def reset_tracking_data(base_dir):
    """Reset all tracking and reputation data."""
    print("\n🔄 Resetting tracking data...")
    
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
        print(f"   ✅ Reset: {filename}")
    
    # Reset cache
    cache_dir = base_dir / 'data' / 'cache'
    cache_file = cache_dir / 'historical_prices.json'
    with open(cache_file, 'w') as f:
        json.dump({}, f, indent=2)
    print(f"   ✅ Reset: cache/historical_prices.json")
    
    # Reset performance tracking
    performance_dir = base_dir / 'data' / 'performance'
    performance_file = performance_dir / 'tracking.json'
    with open(performance_file, 'w') as f:
        json.dump({}, f, indent=2)
    print(f"   ✅ Reset: performance/tracking.json")
    
    # Reset scraped channels if exists
    scraped_file = base_dir / 'data' / 'scraped_channels.json'
    if scraped_file.exists():
        with open(scraped_file, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"   ✅ Reset: scraped_channels.json")
    
    # Reset dead tokens blacklist
    blacklist_file = base_dir / 'data' / 'dead_tokens_blacklist.json'
    if blacklist_file.exists():
        with open(blacklist_file, 'w') as f:
            json.dump([], f, indent=2)
        print(f"   ✅ Reset: dead_tokens_blacklist.json")
    
    # Reset symbol mapping
    symbol_mapping_file = base_dir / 'data' / 'symbol_mapping.json'
    if symbol_mapping_file.exists():
        with open(symbol_mapping_file, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"   ✅ Reset: symbol_mapping.json")


def preserve_essential_data(base_dir):
    """List essential data that's being preserved."""
    print("\n💾 Preserving essential data...")
    
    essential_files = [
        'config/channels.json',
        'credentials/token.json',
        'credentials/oauth_credentials.json',
    ]
    
    preserved = []
    for file_path in essential_files:
        full_path = base_dir / file_path
        if full_path.exists():
            preserved.append(file_path)
    
    if preserved:
        print(f"   ✅ Preserved {len(preserved)} essential files:")
        for f in preserved:
            print(f"      - {f}")
    else:
        print(f"   ℹ️  Only credentials preserved (if they exist)")


def main():
    """Main reset function."""
    print("="*80)
    print("FULL PRODUCTION RESET")
    print("="*80)
    print()
    print("⚠️  WARNING: This will clear ALL data (CSV + Google Sheets)")
    print("   Only headers will remain. A backup will be created first.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n❌ Reset cancelled")
        return
    
    print()
    base_dir = Path(__file__).parent.parent
    
    # Step 1: Backup
    backup_dir = backup_all_data(base_dir)
    
    # Step 2: Clear CSV files
    clear_csv_files(base_dir)
    
    # Step 3: Clear Google Sheets
    print("\n🔐 Authenticating with Google Sheets...")
    try:
        client = authenticate_sheets()
        print("   ✅ Authenticated")
        clear_google_sheets(client, "Crypto Intelligence Data")
    except Exception as e:
        print(f"   ⚠️  Could not clear Google Sheets: {e}")
        print("   You may need to manually clear the sheets")
    
    # Step 4: Reset tracking data
    reset_tracking_data(base_dir)
    
    # Step 5: Preserve essential data
    preserve_essential_data(base_dir)
    
    # Summary
    print()
    print("="*80)
    print("RESET COMPLETE")
    print("="*80)
    print()
    print("✅ System is ready for fresh production scraping")
    print()
    print("📋 What was done:")
    print("   ✅ All data backed up")
    print("   ✅ CSV files cleared (headers only)")
    print("   ✅ Google Sheets cleared (headers only)")
    print("   ✅ Tracking/reputation data reset")
    print("   ✅ Essential config preserved")
    print()
    print("📋 Next Steps:")
    print("   1. Verify config/channels.json has your production channels")
    print("   2. Run: python main.py")
    print("   3. Monitor the scraping process")
    print()
    print(f"💾 Backup location: {backup_dir}")
    print("   (Restore from this if needed)")
    print()
    print("="*80)


if __name__ == '__main__':
    main()
