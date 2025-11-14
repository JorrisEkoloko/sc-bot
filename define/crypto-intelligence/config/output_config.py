"""Data output configuration."""
from dataclasses import dataclass


@dataclass
class OutputConfig:
    """Data output configuration."""
    csv_output_dir: str = "output"
    csv_rotate_daily: bool = True
    google_sheets_enabled: bool = False
    google_auth_method: str = "service_account"  # "service_account" or "oauth"
    google_oauth_credentials_file: str = ""
    google_token_file: str = ""
    google_spreadsheet_name: str = ""
    google_spreadsheet_id: str = ""
    google_share_email: str = ""
    
    @classmethod
    def load_from_env(cls) -> 'OutputConfig':
        """Load output configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        
        # Load .env file
        load_dotenv()
        
        return cls(
            csv_output_dir=os.getenv('CSV_OUTPUT_DIR', 'output'),
            csv_rotate_daily=os.getenv('CSV_ROTATE_DAILY', 'true').lower() == 'true',
            google_sheets_enabled=os.getenv('GOOGLE_SHEETS_ENABLED', 'false').lower() == 'true',
            google_auth_method=os.getenv('GOOGLE_AUTH_METHOD', 'service_account'),
            google_oauth_credentials_file=os.getenv('GOOGLE_OAUTH_CREDENTIALS_FILE', ''),
            google_token_file=os.getenv('GOOGLE_TOKEN_FILE', ''),
            google_spreadsheet_name=os.getenv('GOOGLE_SPREADSHEET_NAME', ''),
            google_spreadsheet_id=os.getenv('GOOGLE_SPREADSHEET_ID', ''),
            google_share_email=os.getenv('GOOGLE_SHARE_EMAIL', '')
        )
