"""Google Sheets multi-table writer.

Manages 4 separate sheets in a single spreadsheet.
Based on verified documentation:
- gspread: https://docs.gspread.org/en/latest/
- Service account auth: https://docs.gspread.org/en/latest/oauth2.html
"""
import os
import pickle
import time
from pathlib import Path
from typing import Optional

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from utils.logger import setup_logger
from utils.key_normalizer import KeyNormalizer


class GoogleSheetsMultiTable:
    """Multi-sheet Google Sheets manager."""
    
    # Sheet names
    MESSAGES_SHEET = "Messages"
    TOKEN_PRICES_SHEET = "Token Prices"
    PERFORMANCE_SHEET = "Performance"
    HISTORICAL_SHEET = "Historical"
    # Task 6: New reputation sheets
    CHANNEL_RANKINGS_SHEET = "Channel Rankings"
    CHANNEL_COIN_PERFORMANCE_SHEET = "Channel Coin Performance"
    COIN_CROSS_CHANNEL_SHEET = "Coin Cross Channel"
    PREDICTION_ACCURACY_SHEET = "Prediction Accuracy"
    
    def __init__(self, config, logger=None):
        """
        Initialize Google Sheets multi-table writer.
        
        Args:
            config: OutputConfig with Google Sheets settings
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or setup_logger('GoogleSheetsMultiTable')
        
        self.client = None
        self.spreadsheet = None
        self.sheets = {}
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests for rate limiting (Google Sheets limit: 60 writes/min)
        self.retry_delays = [2, 5, 10]  # Exponential backoff delays
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Google Sheets connection and setup sheets."""
        try:
            # Authenticate based on method
            if self.config.google_auth_method == 'oauth':
                self.logger.info("Using OAuth authentication")
                self.client = self._authenticate_oauth(gspread)
            else:
                self.logger.info("Using service account authentication")
                self.client = self._authenticate_service_account(gspread)
            
            self.logger.info("Authenticated with Google Sheets")
            
            # Open or create spreadsheet
            if self.config.google_spreadsheet_id:
                # Open by ID
                self.spreadsheet = self.client.open_by_key(self.config.google_spreadsheet_id)
                self.logger.info(f"Opened spreadsheet by ID: {self.spreadsheet.title}")
            elif self.config.google_spreadsheet_name:
                # Try to open by name, create if doesn't exist
                try:
                    self.spreadsheet = self.client.open(self.config.google_spreadsheet_name)
                    self.logger.info(f"Opened existing spreadsheet: {self.spreadsheet.title}")
                except gspread.SpreadsheetNotFound:
                    self.spreadsheet = self.client.create(self.config.google_spreadsheet_name)
                    self.logger.info(f"Created new spreadsheet: {self.spreadsheet.title}")
                    
                    # Share with user email if provided
                    if self.config.google_share_email:
                        self.spreadsheet.share(self.config.google_share_email, perm_type='user', role='writer')
                        self.logger.info(f"Shared spreadsheet with: {self.config.google_share_email}")
            else:
                raise ValueError("Either google_spreadsheet_id or google_spreadsheet_name must be provided")
            
            # Setup sheets
            self._setup_sheets()
            
        except ImportError as e:
            self.logger.error(f"Missing required library: {e}")
            self.logger.error("Install with: pip install gspread google-auth google-auth-oauthlib google-auth-httplib2")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets: {e}")
            raise
    
    def _authenticate_service_account(self, gspread):
        """Authenticate using service account."""
        credentials_path = Path(self.config.google_oauth_credentials_file)
        if not credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        return gspread.service_account(filename=str(credentials_path))
    
    def _authenticate_oauth(self, gspread):
        """Authenticate using OAuth."""
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = None
        token_file = Path(self.config.google_token_file)
        credentials_file = Path(self.config.google_oauth_credentials_file)
        
        # Load token if exists
        if token_file.exists():
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired token")
                creds.refresh(Request())
            else:
                if not credentials_file.exists():
                    raise FileNotFoundError(f"OAuth credentials file not found: {credentials_file}")
                
                self.logger.info("Starting OAuth flow (browser will open)")
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token for future use
            token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            self.logger.info(f"Token saved to: {token_file}")
        
        return gspread.authorize(creds)
    
    def _setup_sheets(self):
        """Setup all 4 sheets with headers."""
        sheet_configs = {
            self.MESSAGES_SHEET: [
                'message_id', 'timestamp', 'channel_name', 'message_text',
                'hdrb_score', 'crypto_mentions', 'sentiment', 'confidence',
                'forwards', 'reactions', 'replies', 'views',
                'channel_reputation_score', 'channel_reputation_tier',
                'channel_expected_roi', 'prediction_source'
            ],
            self.TOKEN_PRICES_SHEET: [
                'address', 'chain', 'symbol', 'price_usd', 'market_cap',
                'volume_24h', 'price_change_24h', 'liquidity_usd', 'pair_created_at'
            ],
            self.PERFORMANCE_SHEET: [
                'address', 'chain', 'symbol', 'first_message_id', 'start_price', 'start_time',
                'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked',
                'days_to_ath', 'peak_timing', 'day_7_price', 'day_7_multiplier', 'day_7_classification',
                'day_30_price', 'day_30_multiplier', 'day_30_classification', 'trajectory'
            ],
            self.HISTORICAL_SHEET: [
                'address', 'chain', 'symbol', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
                'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
            ],
            # Task 6: New reputation sheets
            self.CHANNEL_RANKINGS_SHEET: [
                'rank', 'channel_name', 'total_signals', 'win_rate',
                'avg_roi', 'median_roi', 'best_roi', 'worst_roi',
                'expected_roi', 'sharpe_ratio', 'speed_score',
                'reputation_score', 'reputation_tier',
                'total_predictions', 'prediction_accuracy', 'mean_absolute_error',
                'mean_squared_error', 'first_signal_date', 'last_signal_date', 'last_updated'
            ],
            self.CHANNEL_COIN_PERFORMANCE_SHEET: [
                'channel_name', 'coin_symbol', 'mentions',
                'avg_roi', 'expected_roi', 'win_rate',
                'best_roi', 'worst_roi', 'prediction_accuracy',
                'sharpe_ratio', 'last_mentioned', 'days_since_last_mention',
                'recommendation'
            ],
            self.COIN_CROSS_CHANNEL_SHEET: [
                'coin_symbol', 'total_mentions', 'total_channels',
                'avg_roi_all_channels', 'median_roi_all_channels',
                'best_channel', 'best_channel_roi', 'best_channel_mentions',
                'worst_channel', 'worst_channel_roi', 'worst_channel_mentions',
                'consensus_strength', 'recommendation'
            ],
            self.PREDICTION_ACCURACY_SHEET: [
                'channel_name', 'total_predictions', 'correct_predictions',
                'accuracy_percentage', 'mean_absolute_error', 'mean_squared_error',
                'overestimations', 'underestimations', 'avg_error_magnitude'
            ]
        }
        
        for sheet_name, headers in sheet_configs.items():
            try:
                # Try to get existing sheet
                sheet = self.spreadsheet.worksheet(sheet_name)
                self.logger.debug(f"Found existing sheet: {sheet_name}")
            except:
                # Create new sheet
                sheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )
                self.logger.info(f"Created new sheet: {sheet_name}")
                
                # Add header row
                self._rate_limit()
                sheet.append_row(headers)
                self.logger.debug(f"Added headers to {sheet_name}")
            
            self.sheets[sheet_name] = sheet
        
        self.logger.info(f"Setup complete: {len(self.sheets)} sheets ready")
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def append_to_sheet(self, sheet_name: str, row: list[str]):
        """
        Append row to sheet (for append-only tables like MESSAGES).
        
        Args:
            sheet_name: Name of the sheet
            row: List of values to append
        """
        if sheet_name not in self.sheets:
            self.logger.error(f"Sheet not found: {sheet_name}")
            return
        
        sheet = self.sheets[sheet_name]
        str_row = [str(v) if v is not None else '' for v in row]
        
        # Retry with exponential backoff
        for attempt, delay in enumerate([0] + self.retry_delays):
            try:
                if attempt > 0:
                    self.logger.warning(f"Retry attempt {attempt} for {sheet_name} after {delay}s delay")
                    time.sleep(delay)
                
                self._rate_limit()
                sheet.append_row(str_row)
                self.logger.debug(f"Appended row to {sheet_name}")
                return
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Quota exceeded" in error_msg:
                    if attempt < len(self.retry_delays):
                        self.logger.warning(f"Rate limit hit for {sheet_name}, will retry...")
                        continue
                    else:
                        self.logger.error(f"Rate limit exceeded after all retries for {sheet_name}, skipping")
                        return
                else:
                    self.logger.error(f"Failed to append to {sheet_name}: {e}")
                    return
    
    async def update_or_insert_in_sheet(self, sheet_name: str, key: str, row: list[str]):
        """
        Update existing row or insert new row (for update-or-insert tables).
        
        Args:
            sheet_name: Name of the sheet
            key: Primary key value (first column)
            row: List of values to write
        """
        if sheet_name not in self.sheets:
            self.logger.error(f"Sheet not found: {sheet_name}")
            return
        
        try:
            sheet = self.sheets[sheet_name]
            
            # Get all values (limit to first 10,000 rows for performance)
            self._rate_limit()
            all_values = sheet.get_all_values()
            
            # Normalize key for comparison using KeyNormalizer
            normalized_key = KeyNormalizer.normalize_key_by_column(key, 0, sheet_name)
            
            # Find row with matching key (skip header)
            row_index = None
            for i, existing_row in enumerate(all_values[1:], start=2):  # Start at row 2 (after header)
                if existing_row:
                    # Normalize existing key for comparison using KeyNormalizer
                    existing_key = KeyNormalizer.normalize_key_by_column(existing_row[0], 0, sheet_name)
                    
                    if existing_key == normalized_key:
                        row_index = i
                        break
            
            # Convert row values to strings
            str_row = [str(v) if v is not None else '' for v in row]
            
            if row_index:
                # Update existing row
                self._rate_limit()
                cell_range = f'A{row_index}:{chr(65 + len(row) - 1)}{row_index}'
                sheet.update(cell_range, [str_row])
                self.logger.debug(f"Updated row in {sheet_name} (key: {normalized_key[:10]}...)")
            else:
                # Insert new row
                self._rate_limit()
                sheet.append_row(str_row)
                self.logger.debug(f"Inserted new row in {sheet_name} (key: {normalized_key[:10]}...)")
                
        except Exception as e:
            self.logger.error(f"Failed to update/insert in {sheet_name}: {e}")
            # Don't retry for update_or_insert to avoid duplicates
    
    async def update_or_insert_in_sheet_composite(self, sheet_name: str, key_values: list, row: list[str]):
        """
        Update existing row or insert new row using composite key.
        
        Args:
            sheet_name: Name of the sheet
            key_values: List of values for composite key (e.g., [address, message_id])
            row: List of values to write
        """
        if sheet_name not in self.sheets:
            self.logger.error(f"Sheet not found: {sheet_name}")
            return
        
        try:
            sheet = self.sheets[sheet_name]
            
            # Get all values (limit to first 10,000 rows for performance)
            self._rate_limit()
            all_values = sheet.get_all_values()
            
            # Define key column indices for each sheet type
            # Performance: [address, symbol, first_message_id] at columns [0, 2, 3]
            # Channel Coin Performance: [channel_name, coin_symbol] at columns [0, 1]
            # Others: sequential from column 0
            if sheet_name == 'Performance':
                key_column_indices = [0, 2, 3]  # address at col 0, symbol at col 2, first_message_id at col 3
            elif sheet_name == 'Channel Coin Performance':
                key_column_indices = [0, 1]  # channel_name at col 0, coin_symbol at col 1
            else:
                # Default: use first N columns sequentially
                key_column_indices = list(range(len(key_values)))
            
            # Normalize key values for comparison using KeyNormalizer
            normalized_keys = KeyNormalizer.normalize_composite_key(
                key_values, key_column_indices, sheet_name
            )
            
            # Find row with matching composite key (skip header)
            row_index = None
            for i, existing_row in enumerate(all_values[1:], start=2):  # Start at row 2 (after header)
                if existing_row and len(existing_row) > max(key_column_indices):
                    # Extract and normalize existing row values using KeyNormalizer
                    existing_key_values = [existing_row[col_idx] for col_idx in key_column_indices]
                    existing_keys = KeyNormalizer.normalize_composite_key(
                        existing_key_values, key_column_indices, sheet_name
                    )
                    
                    # Check if all key columns match
                    if existing_keys == normalized_keys:
                        row_index = i
                        break
            
            # Convert row values to strings
            str_row = [str(v) if v is not None else '' for v in row]
            
            if row_index:
                # Update existing row
                self._rate_limit()
                cell_range = f'A{row_index}:{chr(65 + len(row) - 1)}{row_index}'
                sheet.update(cell_range, [str_row])
                key_str = '|'.join(str(k)[:10] for k in normalized_keys)
                self.logger.debug(f"Updated row in {sheet_name} (key: {key_str}...)")
            else:
                # Insert new row
                self._rate_limit()
                sheet.append_row(str_row)
                key_str = '|'.join(str(k)[:10] for k in normalized_keys)
                self.logger.debug(f"Inserted new row in {sheet_name} (key: {key_str}...)")
                
        except Exception as e:
            self.logger.error(f"Failed to update/insert with composite key in {sheet_name}: {e}")
            # Don't retry for update_or_insert to avoid duplicates
    
    async def clear_sheet(self, sheet_name: str):
        """
        Clear all data from a sheet except the header row.
        
        Args:
            sheet_name: Name of the sheet to clear
        """
        if sheet_name not in self.sheets:
            self.logger.error(f"Sheet not found: {sheet_name}")
            return
        
        try:
            sheet = self.sheets[sheet_name]
            
            # Get all values to determine how many rows to clear
            self._rate_limit()
            all_values = sheet.get_all_values()
            
            if len(all_values) <= 1:
                # Only header row exists, nothing to clear
                self.logger.debug(f"Sheet {sheet_name} already empty (only header)")
                return
            
            # Clear all rows except header (row 1)
            # Delete rows 2 onwards
            num_rows_to_delete = len(all_values) - 1
            if num_rows_to_delete > 0:
                self._rate_limit()
                sheet.delete_rows(2, len(all_values))
                self.logger.debug(f"Cleared {num_rows_to_delete} rows from {sheet_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to clear sheet {sheet_name}: {e}")
    
    def close(self):
        """Close connection (no-op for gspread)."""
        self.logger.debug("Google Sheets connection closed")
