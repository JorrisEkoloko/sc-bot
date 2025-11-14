"""Centralized logging system with console and file output."""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Color codes for console output
class LogColors:
    """ANSI color codes for console logging."""
    RESET = '\033[0m'
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta
    TIMESTAMP = '\033[90m'  # Gray


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if record.levelno in self.COLORS:
            levelname_color = f"{self.COLORS[record.levelno]}{levelname}{LogColors.RESET}"
            record.levelname = levelname_color
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return formatted


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with console and file output.
    
    Args:
        name: Logger name (typically component name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = ColoredFormatter(
        f'{LogColors.TIMESTAMP}[%(asctime)s]{LogColors.RESET} '
        f'[%(levelname)s] '
        f'[%(name)s] '
        f'%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with rotation
    log_file = log_dir / f'crypto_intelligence_{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=7,  # Keep 7 days
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
