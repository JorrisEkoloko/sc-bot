"""Configuration management for crypto intelligence system."""
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from config.processing_config import ProcessingConfig
from config.retry_config import RetryConfig
from config.price_config import PriceConfig
from config.performance_config import PerformanceConfig
from config.output_config import OutputConfig
from utils.config_validator import ConfigValidator


@dataclass
class TelegramConfig:
    """Telegram API configuration."""
    api_id: int
    api_hash: str
    phone: str
    session_name: str = "crypto_scraper_session"


@dataclass
class ChannelConfig:
    """Telegram channel configuration."""
    id: str
    name: str
    enabled: bool = True


@dataclass
class Config:
    """Main system configuration."""
    telegram: TelegramConfig
    channels: list[ChannelConfig]
    log_level: str
    processing: ProcessingConfig
    retry: RetryConfig
    price: PriceConfig
    performance: PerformanceConfig
    output: OutputConfig
    
    @classmethod
    def load(cls, env_file: str = '.env', channels_file: str = 'config/channels.json') -> 'Config':
        """Load configuration from environment and JSON files."""
        # Load environment variables
        load_dotenv(env_file)
        
        # Load Telegram configuration
        telegram_config = cls._load_telegram_config()
        
        # Load channels configuration
        channels = cls._load_channels_config(channels_file)
        
        # Load system configuration
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Load processing configuration
        processing_config = ProcessingConfig.load_from_env()
        
        # Load retry configuration
        retry_config = RetryConfig.load_from_env()
        
        # Load price configuration
        price_config = PriceConfig.load_from_env()
        
        # Load performance configuration
        performance_config = PerformanceConfig.load_from_env()
        
        # Load output configuration
        output_config = OutputConfig.load_from_env()
        
        config = cls(
            telegram=telegram_config,
            channels=channels,
            log_level=log_level,
            processing=processing_config,
            retry=retry_config,
            price=price_config,
            performance=performance_config,
            output=output_config
        )
        
        # Validate configuration
        errors, warnings = config.validate()
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
        
        if warnings:
            pass
        
        return config
    
    @classmethod
    def _load_telegram_config(cls) -> TelegramConfig:
        """Load Telegram configuration from environment variables."""
        api_id_str = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        # Convert API ID to integer
        try:
            api_id = int(api_id_str) if api_id_str else None
        except ValueError:
            api_id = None
        
        return TelegramConfig(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone
        )
    
    @classmethod
    def _load_channels_config(cls, channels_file: str) -> list[ChannelConfig]:
        """Load channels configuration from JSON file."""
        channels_path = Path(channels_file)
        
        if not channels_path.exists():
            raise FileNotFoundError(f"Channels configuration file not found: {channels_file}")
        
        try:
            with open(channels_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in channels file: {e}")
        
        if 'channels' not in data:
            raise ValueError("Channels file must contain 'channels' key")
        
        channels = []
        for channel_data in data['channels']:
            channel = ChannelConfig(
                id=channel_data.get('id', ''),
                name=channel_data.get('name', ''),
                enabled=channel_data.get('enabled', True)
            )
            channels.append(channel)
        
        return channels
    
    def validate(self) -> tuple[list[str], list[str]]:
        """Validate configuration and return errors and warnings."""
        errors, warnings = ConfigValidator.validate_all(
            self.telegram,
            self.channels,
            self.log_level
        )
        
        # Update log level if invalid (side effect needed for backward compatibility)
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            self.log_level = 'INFO'
        
        return errors, warnings
