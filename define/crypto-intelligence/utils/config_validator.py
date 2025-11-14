"""Configuration validation utilities.

Pure validation logic separated from configuration classes.
"""
import re
from typing import Tuple, List


class ConfigValidator:
    """Pure validation logic for configuration objects."""
    
    @staticmethod
    def validate_telegram_config(api_id: int, api_hash: str, phone: str) -> Tuple[List[str], List[str]]:
        """
        Validate Telegram configuration.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone: Phone number
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate API ID
        if not api_id:
            errors.append("TELEGRAM_API_ID is required")
        elif api_id <= 0:
            errors.append("TELEGRAM_API_ID must be a positive integer")
        
        # Validate API hash
        if not api_hash:
            errors.append("TELEGRAM_API_HASH is required")
        elif len(api_hash) != 32:
            errors.append("TELEGRAM_API_HASH must be 32 characters")
        
        # Validate phone
        if not phone:
            errors.append("TELEGRAM_PHONE is required")
        elif not re.match(r'^\+\d{10,15}$', phone):
            errors.append("TELEGRAM_PHONE must be in format +1234567890 (10-15 digits)")
        
        return errors, warnings
    
    @staticmethod
    def validate_channels(channels: list) -> Tuple[List[str], List[str]]:
        """
        Validate channel configuration.
        
        Args:
            channels: List of ChannelConfig objects
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check if channels exist
        if not channels:
            errors.append("At least one channel must be configured")
            return errors, warnings
        
        # Check if at least one channel is enabled
        enabled_channels = [c for c in channels if c.enabled]
        if not enabled_channels:
            errors.append("At least one channel must be enabled")
        
        # Validate individual channels
        for i, channel in enumerate(channels):
            if not channel.id:
                errors.append(f"Channel {i+1}: id is required")
            if not channel.name:
                warnings.append(f"Channel {i+1}: name is empty")
        
        return errors, warnings
    
    @staticmethod
    def validate_log_level(log_level: str) -> Tuple[str, List[str]]:
        """
        Validate log level.
        
        Args:
            log_level: Log level string
            
        Returns:
            Tuple of (validated_log_level, warnings)
        """
        warnings = []
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if log_level not in valid_log_levels:
            warnings.append(f"Invalid log level '{log_level}', using INFO")
            return 'INFO', warnings
        
        return log_level, warnings
    
    @staticmethod
    def validate_all(telegram_config, channels: list, log_level: str) -> Tuple[List[str], List[str]]:
        """
        Validate all configuration.
        
        Args:
            telegram_config: TelegramConfig object
            channels: List of ChannelConfig objects
            log_level: Log level string
            
        Returns:
            Tuple of (errors, warnings)
        """
        all_errors = []
        all_warnings = []
        
        # Validate Telegram config
        errors, warnings = ConfigValidator.validate_telegram_config(
            telegram_config.api_id,
            telegram_config.api_hash,
            telegram_config.phone
        )
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        
        # Validate channels
        errors, warnings = ConfigValidator.validate_channels(channels)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        
        # Validate log level
        validated_level, warnings = ConfigValidator.validate_log_level(log_level)
        all_warnings.extend(warnings)
        
        return all_errors, all_warnings
