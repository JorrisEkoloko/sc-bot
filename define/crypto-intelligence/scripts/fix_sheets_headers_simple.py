"""
Simple Google Sheets header fix - directly updates row 1.
"""
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from pathlib import Path


# Column definitions
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


def authenticate():
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


def main():
    """Main function."""
    print("="*80)
    print("GOOGLE SHEETS HEADER FIX (Simple)")
    print("="*80)
    print()
    
    # Authenticate
    print("🔐 Authenticating...")
    client = authenticate()
    print("✅ Authenticated")
    print()
    
    # Open spreadsheet
    spreadsheet_name = "Crypto Intelligence Data"
    print(f"📊 Opening spreadsheet: {spreadsheet_name}")
    spreadsheet = client.open(spreadsheet_name)
    print(f"✅ Opened: {spreadsheet.title}")
    print()
    
    # Fix each sheet
    for sheet_name, headers in SHEET_HEADERS.items():
        try:
            print(f"📝 Fixing {sheet_name}...")
            
            # Get worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                print(f"   ⚠️  Sheet not found, skipping")
                continue
            
            # Get current row 1
            current_headers = worksheet.row_values(1)
            print(f"   Current: {len(current_headers)} columns")
            print(f"   Expected: {len(headers)} columns")
            
            # Update row 1 with correct headers
            worksheet.update('A1', [headers])
            print(f"   ✅ Headers updated")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("="*80)
    print("COMPLETE")
    print("="*80)
    print()
    print("✅ All sheet headers have been updated")
    print("   Open your Google Sheet to verify")
    print()


if __name__ == '__main__':
    main()
