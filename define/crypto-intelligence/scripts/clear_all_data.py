"""Clear all data for a fresh scrape.

This script removes:
- All CSV output files
- All JSON tracking data
- All reputation data
- Historical bootstrap data
- Telegram session files (optional)

Use this when you want to start completely fresh.
"""
import os
import sys
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger


def clear_csv_files(output_dir: str, logger) -> int:
    """Clear all CSV output files."""
    csv_files = [
        'messages.csv',
        'token_prices.csv',
        'performance.csv',
        'historical.csv',
        'channel_rankings.csv',
        'channel_coin_performance.csv',
        'coin_cross_channel.csv',
        'prediction_accuracy.csv'
    ]
    
    cleared = 0
    output_path = Path(output_dir)
    
    # Check root output directory
    for csv_file in csv_files:
        file_path = output_path / csv_file
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"   ✅ Deleted: {csv_file}")
                cleared += 1
            except Exception as e:
                logger.error(f"   ❌ Failed to delete {csv_file}: {e}")
    
    # Check dated subdirectories (e.g., output/2025-11-19/)
    if output_path.exists():
        for subdir in output_path.iterdir():
            if subdir.is_dir():
                for csv_file in csv_files:
                    file_path = subdir / csv_file
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            logger.info(f"   ✅ Deleted: {subdir.name}/{csv_file}")
                            cleared += 1
                        except Exception as e:
                            logger.error(f"   ❌ Failed to delete {subdir.name}/{csv_file}: {e}")
                
                # Remove empty subdirectory
                try:
                    if not any(subdir.iterdir()):
                        subdir.rmdir()
                        logger.info(f"   ✅ Removed empty directory: {subdir.name}")
                except Exception as e:
                    logger.debug(f"   Could not remove directory {subdir.name}: {e}")
    
    return cleared


def clear_json_data(data_dir: str, logger) -> int:
    """Clear all JSON tracking data files."""
    json_files = [
        'performance_tracking.json',
        'signal_outcomes.json',
        'channel_reputations.json',
        'coins_cross_channel.json',
        'historical_bootstrap.json'
    ]
    
    cleared = 0
    
    # Check main data directory
    data_path = Path(data_dir)
    for json_file in json_files:
        file_path = data_path / json_file
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"   ✅ Deleted: {json_file}")
                cleared += 1
            except Exception as e:
                logger.error(f"   ❌ Failed to delete {json_file}: {e}")
    
    # Check reputation subdirectory
    reputation_path = data_path / 'reputation'
    if reputation_path.exists():
        for json_file in ['channel_reputations.json', 'coins_cross_channel.json']:
            file_path = reputation_path / json_file
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"   ✅ Deleted: reputation/{json_file}")
                    cleared += 1
                except Exception as e:
                    logger.error(f"   ❌ Failed to delete reputation/{json_file}: {e}")
    
    # Check tracking subdirectory
    tracking_path = data_path / 'tracking'
    if tracking_path.exists():
        for json_file in ['performance_tracking.json', 'signal_outcomes.json']:
            file_path = tracking_path / json_file
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"   ✅ Deleted: tracking/{json_file}")
                    cleared += 1
                except Exception as e:
                    logger.error(f"   ❌ Failed to delete tracking/{json_file}: {e}")
    
    # Check bootstrap subdirectory
    bootstrap_path = data_path / 'bootstrap'
    if bootstrap_path.exists():
        for json_file in ['historical_bootstrap.json']:
            file_path = bootstrap_path / json_file
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"   ✅ Deleted: bootstrap/{json_file}")
                    cleared += 1
                except Exception as e:
                    logger.error(f"   ❌ Failed to delete bootstrap/{json_file}: {e}")
    
    return cleared


def clear_session_files(credentials_dir: str, logger) -> int:
    """Clear Telegram session files."""
    cleared = 0
    creds_path = Path(credentials_dir)
    
    if not creds_path.exists():
        logger.debug(f"   ⏭️  Credentials directory not found: {credentials_dir}")
        return 0
    
    # Find all .session files
    session_files = list(creds_path.glob('*.session'))
    
    for session_file in session_files:
        try:
            session_file.unlink()
            logger.info(f"   ✅ Deleted: {session_file.name}")
            cleared += 1
        except Exception as e:
            logger.error(f"   ❌ Failed to delete {session_file.name}: {e}")
    
    return cleared


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Clear all data for a fresh scrape',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clear all data except Telegram sessions
  python scripts/clear_all_data.py

  # Clear all data including Telegram sessions (will need to re-authenticate)
  python scripts/clear_all_data.py --clear-sessions

  # Dry run to see what would be deleted
  python scripts/clear_all_data.py --dry-run
        """
    )
    parser.add_argument(
        '--clear-sessions',
        action='store_true',
        help='Also clear Telegram session files (requires re-authentication)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for CSV files (default: output)'
    )
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Data directory for JSON files (default: data)'
    )
    parser.add_argument(
        '--credentials-dir',
        default='credentials',
        help='Credentials directory for session files (default: credentials)'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger('ClearAllData', 'INFO')
    
    logger.info("=" * 80)
    logger.info("CLEAR ALL DATA FOR FRESH SCRAPE")
    logger.info("=" * 80)
    
    if args.dry_run:
        logger.warning("\n⚠️  DRY RUN MODE - No files will be deleted\n")
    else:
        logger.warning("\n⚠️  WARNING: This will delete all tracking data!")
        logger.warning("⚠️  You will lose all historical performance data and reputation scores!")
        
        if args.clear_sessions:
            logger.warning("⚠️  Telegram sessions will also be cleared (requires re-authentication)!")
        
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logger.info("❌ Cancelled by user")
            return 1
        
        logger.info("")
    
    total_cleared = 0
    
    # Clear CSV files
    logger.info("1. Clearing CSV output files...")
    csv_cleared = clear_csv_files(args.output_dir, logger)
    total_cleared += csv_cleared
    logger.info(f"   📊 Cleared {csv_cleared} CSV files\n")
    
    # Clear JSON data files
    logger.info("2. Clearing JSON tracking data...")
    json_cleared = clear_json_data(args.data_dir, logger)
    total_cleared += json_cleared
    logger.info(f"   📊 Cleared {json_cleared} JSON files\n")
    
    # Clear session files if requested
    if args.clear_sessions:
        logger.info("3. Clearing Telegram session files...")
        session_cleared = clear_session_files(args.credentials_dir, logger)
        total_cleared += session_cleared
        logger.info(f"   📊 Cleared {session_cleared} session files\n")
    else:
        logger.info("3. Skipping Telegram session files (use --clear-sessions to clear)\n")
    
    # Summary
    logger.info("=" * 80)
    if args.dry_run:
        logger.info(f"DRY RUN: Would delete {total_cleared} files")
    else:
        logger.info(f"✅ CLEARED {total_cleared} FILES")
    logger.info("=" * 80)
    
    if not args.dry_run and total_cleared > 0:
        logger.info("\n✨ System is ready for a fresh scrape!")
        logger.info("   Run: python main.py")
        
        if args.clear_sessions:
            logger.info("\n⚠️  Note: You will need to re-authenticate with Telegram")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
