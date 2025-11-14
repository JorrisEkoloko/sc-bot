"""Google Sheets multi-table writer.

Manages 4 separate sheets in a single spreadsheet.
Based on verified documentation:
- gspread: https://docs.gspread.org/en/latest/
- Service account auth: https://docs.gspread.org/en/latest/oauth2.html
"""
from pathlib import Path
from typing import Optional
import time

from utils.logger import setup_logger


class GoogleSheetsMultiTable:
    """Multi-sheet Google Sheets manager."""
    
    # Sheet names
    MESSAGES_SHEET = "Messages"
    TOKEN_PRICES_SHEET = "Token Prices"
    PERFORMANCE_SHEET = "Performance"
    HISTORICAL_SHEET = "Historical"
    
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
        self.min_request_interval = 1.0  # 1 second between requests for rate limiting
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Google Sheets connection and setup sheets."""
        try:
            import gspread
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            import os
            import pickle
            
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
        import pickle
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        
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
                'hdrb_score', 'crypto_mentions', 'sentiment', 'confidence'
            ],
            self.TOKEN_PRICES_SHEET: [
                'address', 'chain', 'symbol', 'price_usd', 'market_cap',
                'volume_24h', 'price_change_24h', 'liquidity_usd', 'pair_created_at'
            ],
            self.PERFORMANCE_SHEET: [
                'address', 'chain', 'first_message_id', 'start_price', 'start_time',
                'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked'
            ],
            self.HISTORICAL_SHEET: [
                'address', 'chain', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
                'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
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
    
    async def append_to_sheet(self, sheet_name: str, row: list):
        """
        Append row to sheet (for append-only tables like MESSAGES).
        
        Args:
            sheet_name: Name of the sheet
            row: List of values to append
        """
        if sheet_name not in self.sheets:
            self.logger.error(f"Sheet not found: {sheet_name}")
            return
        
        try:
            self._rate_limit()
            sheet = self.sheets[sheet_name]
            sheet.append_row([str(v) if v is not None else '' for v in row])
            self.logger.debug(f"Appended row to {sheet_name}")
        except Exception as e:
            self.logger.error(f"Failed to append to {sheet_name}: {e}")
            # Retry once after delay
            try:
                time.sleep(2)
                self._rate_limit()
                sheet.append_row([str(v) if v is not None else '' for v in row])
                self.logger.info(f"Retry successful for {sheet_name}")
            except Exception as retry_error:
                self.logger.error(f"Retry failed for {sheet_name}: {retry_error}")
    
    async def update_or_insert_in_sheet(self, sheet_name: str, key: str, row: list):
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
            
            # Find row with matching key (skip header)
            row_index = None
            for i, existing_row in enumerate(all_values[1:], start=2):  # Start at row 2 (after header)
                if existing_row and existing_row[0] == key:
                    row_index = i
                    break
            
            # Convert row values to strings
            str_row = [str(v) if v is not None else '' for v in row]
            
            if row_index:
                # Update existing row
                self._rate_limit()
                cell_range = f'A{row_index}:{chr(65 + len(row) - 1)}{row_index}'
                sheet.update(cell_range, [str_row])
                self.logger.debug(f"Updated row in {sheet_name} (key: {key[:10]}...)")
            else:
                # Insert new row
                self._rate_limit()
                sheet.append_row(str_row)
                self.logger.debug(f"Inserted new row in {sheet_name} (key: {key[:10]}...)")
                
        except Exception as e:
            self.logger.error(f"Failed to update/insert in {sheet_name}: {e}")
            # Don't retry for update_or_insert to avoid duplicates
    
    def close(self):
        """Close connection (no-op for gspread)."""
        self.logger.debug("Google Sheets connection closed")
