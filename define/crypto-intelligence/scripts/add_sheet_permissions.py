"""
Add permissions to Google Sheets.

This script adds viewer or editor permissions to the Google Sheets spreadsheet.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import OutputConfig
from repositories.writers.sheets_writer import GoogleSheetsMultiTable
from utils.logger import setup_logger


def add_permissions():
    """Add permissions to Google Sheets."""
    
    print()
    print("=" * 80)
    print("ADD GOOGLE SHEETS PERMISSIONS")
    print("=" * 80)
    
    # Initialize logger
    logger = setup_logger('PermissionManager')
    
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
    print(f"📊 Spreadsheet: {sheets.spreadsheet.title}")
    print(f"🔗 URL: {sheets.spreadsheet.url}")
    
    # Get email from config
    share_email = config.google_share_email
    
    if not share_email:
        print()
        print("⚠️  No email specified in .env file")
        print("   Set GOOGLE_SHARE_EMAIL=your_email@example.com")
        print()
        
        # Ask for email
        share_email = input("Enter email address to share with: ").strip()
        
        if not share_email:
            print("❌ No email provided, exiting")
            return
    
    # Ask for permission type
    print()
    print("Select permission type:")
    print("  1. Viewer (read-only)")
    print("  2. Editor (can edit)")
    print("  3. Owner (full control)")
    
    choice = input("Enter choice (1-3) [default: 1]: ").strip() or "1"
    
    permission_map = {
        "1": "reader",
        "2": "writer",
        "3": "owner"
    }
    
    role = permission_map.get(choice, "reader")
    role_name = {
        "reader": "Viewer",
        "writer": "Editor",
        "owner": "Owner"
    }[role]
    
    # Add permission
    print()
    print(f"📧 Adding {role_name} permission for: {share_email}")
    
    try:
        sheets.spreadsheet.share(
            share_email,
            perm_type='user',
            role=role,
            notify=True,
            email_message=f"You've been granted {role_name} access to the Crypto Intelligence Data spreadsheet."
        )
        
        print(f"✅ Permission added successfully!")
        print(f"   {share_email} now has {role_name} access")
        print()
        print("📧 An email notification has been sent to the user")
        
    except Exception as e:
        logger.error(f"Failed to add permission: {e}")
        print(f"❌ Error: {e}")
        
        # Check if permission already exists
        if "already has access" in str(e).lower():
            print()
            print("ℹ️  This user may already have access to the spreadsheet")
            print("   Check the sharing settings in Google Sheets")
    
    # List current permissions
    print()
    print("=" * 80)
    print("CURRENT PERMISSIONS")
    print("=" * 80)
    
    try:
        permissions = sheets.spreadsheet.list_permissions()
        
        for i, perm in enumerate(permissions, 1):
            email = perm.get('emailAddress', 'N/A')
            role = perm.get('role', 'N/A')
            perm_type = perm.get('type', 'N/A')
            
            print(f"{i}. {email}")
            print(f"   Role: {role}")
            print(f"   Type: {perm_type}")
            print()
            
    except Exception as e:
        logger.error(f"Failed to list permissions: {e}")
        print(f"❌ Error listing permissions: {e}")
    
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    add_permissions()
