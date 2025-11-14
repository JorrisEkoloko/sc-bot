# Configuration Management - Deep Implementation Guide

## Overview

Unified configuration system with environment-specific settings, hot-reload capabilities, validation, and secure credential management for the crypto intelligence system.

## Architecture Design

### Core Responsibilities

- Unified configuration management across all components
- Environment-specific configuration (dev/staging/prod)
- Hot-reload capabilities without system restart
- Configuration validation and error handling
- Secure credential and API key management

### Component Structure

```
ConfigurationManagement/
├── config_loader.py        # Configuration loading and parsing
├── environment_manager.py  # Environment-specific settings
├── credential_manager.py   # Secure credential handling
├── validator.py            # Configuration validation
└── hot_reload_manager.py   # Dynamic configuration updates
```

## Unified Configuration System

### 1. Configuration Loader

```python
class ConfigurationLoader:
    """Advanced configuration loading with multiple sources"""

    def __init__(self):
        self.config_sources = [
            'environment_variables',
            'config_files',
            'command_line_args',
            'default_values'
        ]
        self.config_cache = {}
        self.last_loaded = None

    def load_configuration(self, config_path=None, environment=None):
        """Load configuration from multiple sources with precedence"""
        try:
            # Initialize configuration structure
            config = self._initialize_config_structure()

            # Load from sources in order of precedence (lowest to highest)
            config = self._load_default_values(config)
            config = self._load_from_files(config, config_path)
            config = self._load_from_environment(config)
            config = self._load_from_command_line(config)

            # Apply environment-specific overrides
            if environment:
                config = self._apply_environment_overrides(config, environment)

            # Validate configuration
            self._validate_configuration(config)

            # Cache configuration
            self.config_cache = config
            self.last_loaded = datetime.now()

            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _initialize_config_structure(self):
        """Initialize the base configuration structure"""
        return {
            'system': {},
            'telegram': {},
            'apis': {},
            'processing': {},
            'tracking': {},
            'output': {},
            'intelligence': {},
            'logging': {},
            'monitoring': {},
            'security': {}
        }

    def _load_from_files(self, config, config_path):
        """Load configuration from JSON/YAML files"""
        config_files = [
            'config/default.json',
            'config/settings.json',
            config_path
        ]

        for file_path in config_files:
            if file_path and Path(file_path).exists():
                try:
                    with open(file_path, 'r') as f:
                        if file_path.endswith('.json'):
                            file_config = json.load(f)
                        elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                            file_config = yaml.safe_load(f)
                        else:
                            continue

                    # Deep merge configuration
                    config = self._deep_merge_config(config, file_config)

                except Exception as e:
                    logging.warning(f"Failed to load config file {file_path}: {e}")

        return config

    def _load_from_environment(self, config):
        """Load configuration from environment variables"""
        env_mappings = {
            # Telegram configuration
            'TELEGRAM_API_ID': ('telegram', 'api_id'),
            'TELEGRAM_API_HASH': ('telegram', 'api_hash'),
            'TELEGRAM_PHONE': ('telegram', 'phone'),
            'CHANNEL_ID': ('telegram', 'default_channel'),

            # API configuration
            'COINGECKO_API_KEY': ('apis', 'coingecko_key'),
            'BIRDEYE_API_KEY': ('apis', 'birdeye_key'),
            'MORALIS_API_KEY': ('apis', 'moralis_key'),

            # Google Sheets
            'GOOGLE_SERVICE_ACCOUNT_KEY': ('output', 'sheets_config', 'service_account_key'),

            # System configuration
            'LOG_LEVEL': ('logging', 'level'),
            'TRACKING_DAYS': ('tracking', 'tracking_days'),
            'CONFIDENCE_THRESHOLD': ('processing', 'confidence_threshold')
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                value = self._convert_env_value(value, config_path)

                # Set nested configuration value
                self._set_nested_config(config, config_path, value)

        return config

    def _convert_env_value(self, value, config_path):
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Integer conversion for specific paths
        integer_paths = [
            ('telegram', 'api_id'),
            ('tracking', 'tracking_days'),
            ('tracking', 'update_interval')
        ]

        if config_path in integer_paths:
            try:
                return int(value)
            except ValueError:
                pass

        # Float conversion for specific paths
        float_paths = [
            ('processing', 'confidence_threshold'),
            ('processing', 'hdrb_threshold')
        ]

        if config_path in float_paths:
            try:
                return float(value)
            except ValueError:
                pass

        return value
```

### 2. Environment-Specific Configuration

```python
class EnvironmentManager:
    """Manages environment-specific configuration settings"""

    def __init__(self):
        self.environments = ['development', 'staging', 'production']
        self.current_environment = self._detect_environment()

    def _detect_environment(self):
        """Automatically detect current environment"""
        # Check environment variable
        env = os.getenv('CRYPTO_INTELLIGENCE_ENV', '').lower()
        if env in self.environments:
            return env

        # Check for development indicators
        if os.path.exists('.git') or os.getenv('DEBUG') == 'true':
            return 'development'

        # Check for production indicators
        if os.getenv('PRODUCTION') == 'true' or not sys.stdout.isatty():
            return 'production'

        # Default to development
        return 'development'

    def get_environment_config(self, environment=None):
        """Get environment-specific configuration"""
        env = environment or self.current_environment

        configs = {
            'development': {
                'logging': {
                    'level': 'DEBUG',
                    'console_output': True,
                    'file_output': True
                },
                'processing': {
                    'confidence_threshold': 0.5,  # Lower threshold for testing
                    'hdrb_threshold': 0.4
                },
                'tracking': {
                    'tracking_days': 3,  # Shorter tracking for testing
                    'update_interval': 1800  # 30 minutes
                },
                'apis': {
                    'rate_limits': {
                        'coingecko': 10,  # Lower limits for development
                        'birdeye': 20,
                        'moralis': 5
                    }
                },
                'monitoring': {
                    'health_check_interval': 30,
                    'performance_monitoring': True,
                    'detailed_logging': True
                }
            },
            'staging': {
                'logging': {
                    'level': 'INFO',
                    'console_output': True,
                    'file_output': True
                },
                'processing': {
                    'confidence_threshold': 0.6,
                    'hdrb_threshold': 0.5
                },
                'tracking': {
                    'tracking_days': 5,
                    'update_interval': 3600  # 1 hour
                },
                'apis': {
                    'rate_limits': {
                        'coingecko': 25,
                        'birdeye': 40,
                        'moralis': 15
                    }
                },
                'monitoring': {
                    'health_check_interval': 60,
                    'performance_monitoring': True,
                    'detailed_logging': False
                }
            },
            'production': {
                'logging': {
                    'level': 'WARNING',
                    'console_output': False,
                    'file_output': True,
                    'rotation': True
                },
                'processing': {
                    'confidence_threshold': 0.7,  # Higher threshold for production
                    'hdrb_threshold': 0.6
                },
                'tracking': {
                    'tracking_days': 7,
                    'update_interval': 7200  # 2 hours
                },
                'apis': {
                    'rate_limits': {
                        'coingecko': 50,  # Full rate limits
                        'birdeye': 60,
                        'moralis': 25
                    }
                },
                'monitoring': {
                    'health_check_interval': 300,  # 5 minutes
                    'performance_monitoring': True,
                    'detailed_logging': False,
                    'alerting_enabled': True
                }
            }
        }

        return configs.get(env, configs['development'])
```

## Secure Credential Management

### 1. Credential Manager

```python
class CredentialManager:
    """Secure credential and API key management"""

    def __init__(self):
        self.credential_sources = [
            'environment_variables',
            'credential_files',
            'key_vault',  # For cloud deployments
            'encrypted_storage'
        ]
        self.encryption_key = self._get_or_create_encryption_key()

    def get_credential(self, credential_name, required=True):
        """Securely retrieve credential from multiple sources"""
        try:
            # Try environment variables first (most secure for production)
            value = os.getenv(credential_name)
            if value:
                return value

            # Try encrypted credential file
            value = self._get_from_encrypted_file(credential_name)
            if value:
                return value

            # Try key vault (cloud deployments)
            value = self._get_from_key_vault(credential_name)
            if value:
                return value

            # Handle missing required credentials
            if required:
                raise CredentialError(f"Required credential '{credential_name}' not found")

            return None

        except Exception as e:
            if required:
                raise CredentialError(f"Failed to retrieve credential '{credential_name}': {e}")
            return None

    def store_credential(self, credential_name, value, encrypt=True):
        """Securely store credential"""
        try:
            if encrypt:
                encrypted_value = self._encrypt_value(value)
                self._store_encrypted_credential(credential_name, encrypted_value)
            else:
                # Store in environment (for current session only)
                os.environ[credential_name] = value

        except Exception as e:
            raise CredentialError(f"Failed to store credential '{credential_name}': {e}")

    def _encrypt_value(self, value):
        """Encrypt credential value"""
        try:
            from cryptography.fernet import Fernet

            fernet = Fernet(self.encryption_key)
            encrypted_value = fernet.encrypt(value.encode())
            return encrypted_value

        except ImportError:
            # Fallback to base64 encoding (not secure, for development only)
            import base64
            return base64.b64encode(value.encode())

    def _decrypt_value(self, encrypted_value):
        """Decrypt credential value"""
        try:
            from cryptography.fernet import Fernet

            fernet = Fernet(self.encryption_key)
            decrypted_value = fernet.decrypt(encrypted_value)
            return decrypted_value.decode()

        except ImportError:
            # Fallback to base64 decoding
            import base64
            return base64.b64decode(encrypted_value).decode()

    def _get_or_create_encryption_key(self):
        """Get or create encryption key for credential storage"""
        key_file = Path('.crypto_intelligence_key')

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            try:
                from cryptography.fernet import Fernet
                key = Fernet.generate_key()

                # Store key securely (in production, use key management service)
                with open(key_file, 'wb') as f:
                    f.write(key)

                # Set restrictive permissions
                os.chmod(key_file, 0o600)

                return key

            except ImportError:
                # Fallback for development
                return b'development_key_not_secure'
```

### 2. Configuration Validation

```python
class ConfigurationValidator:
    """Validates configuration completeness and correctness"""

    def __init__(self):
        self.validation_rules = self._define_validation_rules()

    def validate_configuration(self, config):
        """Comprehensive configuration validation"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_optional': []
        }

        try:
            # Validate required fields
            self._validate_required_fields(config, validation_results)

            # Validate data types and formats
            self._validate_data_types(config, validation_results)

            # Validate value ranges and constraints
            self._validate_constraints(config, validation_results)

            # Validate API credentials
            self._validate_credentials(config, validation_results)

            # Validate cross-field dependencies
            self._validate_dependencies(config, validation_results)

            # Check for deprecated settings
            self._check_deprecated_settings(config, validation_results)

        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation error: {e}")

        return validation_results

    def _define_validation_rules(self):
        """Define comprehensive validation rules"""
        return {
            'required_fields': {
                'telegram.api_id': {'type': int, 'min': 1},
                'telegram.api_hash': {'type': str, 'min_length': 32},
                'telegram.phone': {'type': str, 'pattern': r'^\+\d{10,15}$'},
                'processing.confidence_threshold': {'type': float, 'min': 0.0, 'max': 1.0},
                'tracking.tracking_days': {'type': int, 'min': 1, 'max': 30}
            },
            'optional_fields': {
                'apis.coingecko_key': {'type': str, 'min_length': 10},
                'apis.birdeye_key': {'type': str, 'min_length': 10},
                'output.sheets_config.service_account_key': {'type': str}
            },
            'constraints': {
                'processing.hdrb_threshold': {
                    'must_be_less_than': 'processing.confidence_threshold'
                },
                'tracking.update_interval': {
                    'min': 300,  # 5 minutes minimum
                    'max': 86400  # 24 hours maximum
                }
            }
        }

    def _validate_required_fields(self, config, results):
        """Validate all required configuration fields"""
        for field_path, rules in self.validation_rules['required_fields'].items():
            value = self._get_nested_value(config, field_path)

            if value is None:
                results['valid'] = False
                results['errors'].append(f"Required field missing: {field_path}")
                continue

            # Validate type
            if 'type' in rules and not isinstance(value, rules['type']):
                results['valid'] = False
                results['errors'].append(
                    f"Invalid type for {field_path}: expected {rules['type'].__name__}, got {type(value).__name__}"
                )

            # Validate constraints
            self._validate_field_constraints(field_path, value, rules, results)

    def _validate_credentials(self, config, results):
        """Validate API credentials and connectivity"""
        credential_checks = [
            ('telegram.api_id', 'Telegram API ID'),
            ('telegram.api_hash', 'Telegram API Hash'),
            ('apis.coingecko_key', 'CoinGecko API Key'),
            ('apis.birdeye_key', 'Birdeye API Key')
        ]

        for field_path, description in credential_checks:
            value = self._get_nested_value(config, field_path)

            if value:
                # Basic format validation
                if not self._validate_credential_format(field_path, value):
                    results['warnings'].append(f"Invalid format for {description}")
            else:
                if field_path.startswith('telegram'):
                    results['errors'].append(f"Missing required credential: {description}")
                else:
                    results['warnings'].append(f"Missing optional credential: {description}")
```

## Hot-Reload Configuration System

### 1. Hot-Reload Manager

```python
class HotReloadManager:
    """Manages dynamic configuration updates without system restart"""

    def __init__(self, config_loader, system_components):
        self.config_loader = config_loader
        self.system_components = system_components
        self.file_watchers = {}
        self.reload_callbacks = {}
        self.last_reload = None

    async def start_hot_reload_monitoring(self):
        """Start monitoring configuration files for changes"""
        try:
            config_files = [
                'config/settings.json',
                'config/channels.json',
                'config/api_settings.json'
            ]

            for config_file in config_files:
                if Path(config_file).exists():
                    await self._setup_file_watcher(config_file)

            # Start periodic reload check
            asyncio.create_task(self._periodic_reload_check())

        except Exception as e:
            logging.error(f"Failed to start hot-reload monitoring: {e}")

    async def _setup_file_watcher(self, file_path):
        """Setup file system watcher for configuration file"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, reload_manager):
                    self.reload_manager = reload_manager

                def on_modified(self, event):
                    if not event.is_directory and event.src_path.endswith(('.json', '.yaml', '.yml')):
                        asyncio.create_task(self.reload_manager._handle_config_change(event.src_path))

            observer = Observer()
            observer.schedule(
                ConfigFileHandler(self),
                path=str(Path(file_path).parent),
                recursive=False
            )
            observer.start()

            self.file_watchers[file_path] = observer

        except ImportError:
            # Fallback to periodic checking if watchdog not available
            logging.warning("Watchdog not available, using periodic config checking")

    async def _handle_config_change(self, file_path):
        """Handle configuration file change"""
        try:
            # Wait a moment for file write to complete
            await asyncio.sleep(1)

            # Reload configuration
            new_config = self.config_loader.load_configuration()

            # Validate new configuration
            validator = ConfigurationValidator()
            validation_result = validator.validate_configuration(new_config)

            if not validation_result['valid']:
                logging.error(f"Invalid configuration in {file_path}: {validation_result['errors']}")
                return

            # Apply configuration changes
            await self._apply_configuration_changes(new_config)

            self.last_reload = datetime.now()
            logging.info(f"Configuration reloaded from {file_path}")

        except Exception as e:
            logging.error(f"Failed to reload configuration from {file_path}: {e}")

    async def _apply_configuration_changes(self, new_config):
        """Apply configuration changes to system components"""
        try:
            # Update component configurations
            for component_name, component in self.system_components.items():
                if hasattr(component, 'update_configuration'):
                    component_config = self._extract_component_config(new_config, component_name)
                    await component.update_configuration(component_config)

            # Trigger reload callbacks
            for callback_name, callback in self.reload_callbacks.items():
                try:
                    await callback(new_config)
                except Exception as e:
                    logging.error(f"Error in reload callback {callback_name}: {e}")

        except Exception as e:
            logging.error(f"Failed to apply configuration changes: {e}")

    def register_reload_callback(self, name, callback):
        """Register callback for configuration reload events"""
        self.reload_callbacks[name] = callback

    def _extract_component_config(self, config, component_name):
        """Extract configuration section for specific component"""
        component_mappings = {
            'telegram_monitor': 'telegram',
            'message_processor': 'processing',
            'price_engine': 'apis',
            'performance_tracker': 'tracking',
            'data_output': 'output'
        }

        config_section = component_mappings.get(component_name, component_name)
        return config.get(config_section, {})
```

## Configuration Templates and Examples

### 1. Complete Configuration Template

```json
{
  "system": {
    "environment": "production",
    "max_memory_usage": "2GB",
    "max_cpu_usage": 80,
    "debug_mode": false
  },
  "telegram": {
    "api_id": "${TELEGRAM_API_ID}",
    "api_hash": "${TELEGRAM_API_HASH}",
    "phone": "${TELEGRAM_PHONE}",
    "default_channel": "${CHANNEL_ID}",
    "channels_file": "config/channels.json",
    "session_file": "crypto_intelligence_session",
    "connection_timeout": 30,
    "retry_attempts": 3
  },
  "apis": {
    "coingecko_key": "${COINGECKO_API_KEY}",
    "birdeye_key": "${BIRDEYE_API_KEY}",
    "moralis_key": "${MORALIS_API_KEY}",
    "rate_limits": {
      "coingecko": 50,
      "birdeye": 60,
      "moralis": 25,
      "dexscreener": 300
    },
    "timeout": 10,
    "retry_attempts": 3,
    "circuit_breaker": {
      "failure_threshold": 5,
      "recovery_timeout": 300
    }
  },
  "processing": {
    "confidence_threshold": 0.7,
    "hdrb_threshold": 0.6,
    "hdrb_config": {
      "weights": {
        "engagement": 0.4,
        "crypto_relevance": 0.25,
        "signal_strength": 0.2,
        "timing_factor": 0.15
      }
    },
    "intelligence_weights": {
      "hdrb_score": 0.35,
      "market_cap_intelligence": 0.25,
      "channel_reputation": 0.25,
      "historical_correlation": 0.15
    }
  },
  "tracking": {
    "tracking_days": 7,
    "update_interval": 7200,
    "max_tracked_tokens": 1000,
    "tracking_file": "data/tracking.json",
    "cleanup_threshold": 0.8,
    "backup_interval": 3600
  },
  "output": {
    "csv_path": "output/crypto_tracking.csv",
    "csv_rotation": true,
    "sheets_config": {
      "service_account_key": "${GOOGLE_SERVICE_ACCOUNT_KEY}",
      "spreadsheet_name": "Crypto Intelligence Dashboard",
      "auto_resize_columns": true,
      "conditional_formatting": true
    },
    "batch_size": 50,
    "sync_interval": 300
  },
  "intelligence": {
    "market_analysis_enabled": true,
    "channel_reputation_enabled": true,
    "signal_scoring_enabled": true,
    "learning_rate": 0.01,
    "optimization_frequency": "daily"
  },
  "logging": {
    "level": "INFO",
    "console_output": true,
    "file_output": true,
    "file_path": "logs/crypto_intelligence.log",
    "rotation": true,
    "max_file_size": "100MB",
    "backup_count": 5
  },
  "monitoring": {
    "health_check_interval": 300,
    "performance_monitoring": true,
    "alerting_enabled": true,
    "metrics_retention": "30d"
  },
  "security": {
    "credential_encryption": true,
    "api_key_rotation": false,
    "audit_logging": true
  }
}
```

### 2. Environment-Specific Overrides

```json
{
  "development": {
    "logging": {
      "level": "DEBUG",
      "console_output": true
    },
    "processing": {
      "confidence_threshold": 0.5
    },
    "tracking": {
      "tracking_days": 3,
      "update_interval": 1800
    }
  },
  "staging": {
    "logging": {
      "level": "INFO"
    },
    "processing": {
      "confidence_threshold": 0.6
    },
    "tracking": {
      "tracking_days": 5
    }
  },
  "production": {
    "logging": {
      "level": "WARNING",
      "console_output": false
    },
    "processing": {
      "confidence_threshold": 0.7
    },
    "monitoring": {
      "alerting_enabled": true
    }
  }
}
```

## Integration Interfaces

### Configuration Interface

```python
class Config:
    @classmethod
    def load(cls, config_path: str = None, environment: str = None) -> 'Config':
        """Load configuration from multiple sources"""

    def validate(self) -> bool:
        """Validate configuration completeness and correctness"""

    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation"""

    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration values dynamically"""
```

### Hot-Reload Interface

```python
async def enable_hot_reload(self, components: Dict[str, Any]) -> None:
    """Enable hot-reload monitoring for configuration files"""

def register_reload_callback(self, name: str, callback: Callable) -> None:
    """Register callback for configuration reload events"""
```

## Performance Targets

### Configuration Performance

- **< 100ms Load Time**: Configuration loading and validation
- **< 50ms Reload Time**: Hot-reload configuration updates
- **100% Validation Coverage**: All configuration fields validated
- **Zero Downtime Reloads**: Configuration updates without restart

### Security Targets

- **Encrypted Credentials**: All sensitive data encrypted at rest
- **No Plaintext Secrets**: No credentials in configuration files
- **Audit Trail**: Complete configuration change logging
- **Access Control**: Restricted access to configuration files
