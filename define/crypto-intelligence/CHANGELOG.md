# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-11-21

### Fixed
- **Critical Bug**: Fixed undefined `error_count` variable in `message_processor_coordinator.py` that caused crashes during historical scraping at message processing
- **Windows Compatibility**: Added Windows-safe log rotation to prevent PermissionError crashes when log files are locked during shutdown or interruption
- **Production Reset**: Updated `full_production_reset.py` to preserve `channels.json` configuration file

### Changed
- Logger now gracefully handles Windows file permission errors during log rotation
- Production reset script no longer removes channel configuration

### Removed
- Cleaned up temporary backup directories and cache files
- Removed 31 temporary test files from root directory

### Technical Details
- `message_processor_coordinator.py` line 91: Changed `error_count` to `len(failed_messages)`
- `utils/logger.py`: Added safe_doRollover wrapper to catch PermissionError/OSError
- `.gitignore`: Added backup directory patterns
