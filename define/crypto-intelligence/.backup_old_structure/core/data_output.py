"""Multi-table data output coordinator.

Manages 4 separate tables (MESSAGES, TOKEN_PRICES, PERFORMANCE, HISTORICAL)
with dual CSV and Google Sheets output.
"""
from typing import Optional
from pathlib import Path

from config.output_config import OutputConfig
from core.csv_table_writer import CSVTableWriter
from core.sheets_multi_table import GoogleSheetsMultiTable
from core.api_clients import PriceData
from core.performance_tracker import PerformanceData
from utils.logger import setup_logger


class MultiTableDataOutput:
    """Multi-table data output coordinator."""
    
    # Table column definitions
    MESSAGES_COLUMNS = [
        'message_id', 'timestamp', 'channel_name', 'message_text',
        'hdrb_score', 'crypto_mentions', 'sentiment', 'confidence'
    ]
    
    TOKEN_PRICES_COLUMNS = [
        'address', 'chain', 'symbol', 'price_usd', 'market_cap',
        'volume_24h', 'price_change_24h', 'liquidity_usd', 'pair_created_at',
        # Market Intelligence columns (Part 7)
        'market_tier', 'risk_level', 'risk_score',
        'liquidity_ratio', 'volume_ratio', 'data_completeness'
    ]
    
    PERFORMANCE_COLUMNS = [
        'address', 'chain', 'first_message_id', 'start_price', 'start_time',
        'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked'
    ]
    
    HISTORICAL_COLUMNS = [
        'address', 'chain', 'all_time_ath', 'all_time_ath_date', 'distance_from_ath',
        'all_time_atl', 'all_time_atl_date', 'distance_from_atl'
    ]
    
    def __init__(self, config: OutputConfig, logger=None):
        """
        Initialize multi-table data output.
        
        Args:
            config: Output configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or setup_logger('MultiTableDataOutput')
        
        # Create output directory
        output_dir = Path(config.csv_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV writers for each table
        self.csv_writers = {
            'messages': CSVTableWriter(
                'messages',
                self.MESSAGES_COLUMNS,
                config.csv_output_dir,
                self.logger
            ),
            'token_prices': CSVTableWriter(
                'token_prices',
                self.TOKEN_PRICES_COLUMNS,
                config.csv_output_dir,
                self.logger
            ),
            'performance': CSVTableWriter(
                'performance',
                self.PERFORMANCE_COLUMNS,
                config.csv_output_dir,
                self.logger
            ),
            'historical': CSVTableWriter(
                'historical',
                self.HISTORICAL_COLUMNS,
                config.csv_output_dir,
                self.logger
            )
        }
        
        # Initialize Google Sheets writer if enabled
        self.sheets_writer = None
        if config.google_sheets_enabled:
            try:
                self.sheets_writer = GoogleSheetsMultiTable(config, self.logger)
                self.logger.info("Google Sheets multi-table writer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Sheets: {e}")
                self.logger.warning("Continuing with CSV-only output")
                self.logger.info("Continuing with CSV-only output")
        
        # Statistics
        self.stats = {
            'messages_written': 0,
            'token_prices_written': 0,
            'performance_written': 0,
            'historical_written': 0,
            'csv_errors': 0,
            'sheets_errors': 0
        }
        
        self.logger.info(f"Multi-table data output initialized (CSV: {config.csv_output_dir}, Sheets: {config.google_sheets_enabled})")
    
    async def write_message(self, message_data: dict):
        """
        Write message to MESSAGES table (append-only).
        
        Args:
            message_data: Dictionary with message fields
        """
        try:
            row = [
                message_data.get('message_id', ''),
                message_data.get('timestamp', ''),
                message_data.get('channel_name', ''),
                str(message_data.get('message_text', ''))[:500],  # Truncate to 500 chars
                message_data.get('hdrb_score', ''),
                ','.join(message_data.get('crypto_mentions', [])),
                message_data.get('sentiment', ''),
                message_data.get('confidence', '')
            ]
            
            # Write to CSV
            try:
                self.csv_writers['messages'].append(row)
                self.stats['messages_written'] += 1
            except Exception as e:
                self.logger.error(f"CSV write failed for MESSAGES: {e}")
                self.stats['csv_errors'] += 1
            
            # Write to Google Sheets
            if self.sheets_writer:
                try:
                    await self.sheets_writer.append_to_sheet('Messages', row)
                except Exception as e:
                    self.logger.error(f"Google Sheets write failed for MESSAGES: {e}")
                    self.stats['sheets_errors'] += 1
                    
        except Exception as e:
            self.logger.error(f"Failed to write message: {e}")
    
    async def write_token_price(self, address: str, chain: str, price_data: PriceData):
        """
        Write/update token price in TOKEN_PRICES table (update or insert).
        
        Args:
            address: Token contract address
            chain: Blockchain type
            price_data: Price data from API
        """
        try:
            row = [
                address,
                chain,
                price_data.symbol or 'UNKNOWN',
                price_data.price_usd,
                price_data.market_cap or '',
                price_data.volume_24h or '',
                price_data.price_change_24h or '',
                price_data.liquidity_usd or '',
                price_data.pair_created_at or '',
                # Market Intelligence fields (Part 7)
                price_data.market_tier or '',
                price_data.risk_level or '',
                price_data.risk_score if price_data.risk_score is not None else '',
                price_data.liquidity_ratio if price_data.liquidity_ratio is not None else '',
                price_data.volume_ratio if price_data.volume_ratio is not None else '',
                price_data.data_completeness if price_data.data_completeness is not None else ''
            ]
            
            # Update CSV (update existing row or append new)
            try:
                self.csv_writers['token_prices'].update_or_insert(address, row)
                self.stats['token_prices_written'] += 1
            except Exception as e:
                self.logger.error(f"CSV update failed for TOKEN_PRICES: {e}")
                self.stats['csv_errors'] += 1
            
            # Update Google Sheets (update existing row or append new)
            if self.sheets_writer:
                try:
                    await self.sheets_writer.update_or_insert_in_sheet('Token Prices', address, row)
                except Exception as e:
                    self.logger.error(f"Google Sheets update failed for TOKEN_PRICES: {e}")
                    self.stats['sheets_errors'] += 1
                    
        except Exception as e:
            self.logger.error(f"Failed to write token price: {e}")
    
    async def write_performance(self, address: str, chain: str, performance_data: PerformanceData):
        """
        Write/update performance tracking in PERFORMANCE table (update or insert).
        
        Args:
            address: Token contract address
            chain: Blockchain type
            performance_data: Performance tracking data
        """
        try:
            row = [
                address,
                chain,
                performance_data.first_message_id,
                performance_data.start_price,
                performance_data.start_time,
                performance_data.ath_since_mention,
                performance_data.ath_time,
                round(performance_data.ath_multiplier, 4),
                round(performance_data.current_multiplier, 4),
                performance_data.days_tracked
            ]
            
            # Update CSV (update existing row or append new)
            try:
                self.csv_writers['performance'].update_or_insert(address, row)
                self.stats['performance_written'] += 1
            except Exception as e:
                self.logger.error(f"CSV update failed for PERFORMANCE: {e}")
                self.stats['csv_errors'] += 1
            
            # Update Google Sheets (update existing row or append new)
            if self.sheets_writer:
                try:
                    await self.sheets_writer.update_or_insert_in_sheet('Performance', address, row)
                except Exception as e:
                    self.logger.error(f"Google Sheets update failed for PERFORMANCE: {e}")
                    self.stats['sheets_errors'] += 1
                    
        except Exception as e:
            self.logger.error(f"Failed to write performance: {e}")
    
    async def write_historical(self, address: str, chain: str, historical_data: dict):
        """
        Write/update historical ATH/ATL data in HISTORICAL table (update or insert).
        
        Args:
            address: Token contract address
            chain: Blockchain type
            historical_data: Historical ATH/ATL data from CoinGecko
        """
        try:
            row = [
                address,
                chain,
                historical_data.get('all_time_ath', ''),
                historical_data.get('all_time_ath_date', ''),
                historical_data.get('distance_from_ath', ''),
                historical_data.get('all_time_atl', ''),
                historical_data.get('all_time_atl_date', ''),
                historical_data.get('distance_from_atl', '')
            ]
            
            # Update CSV (update existing row or append new)
            try:
                self.csv_writers['historical'].update_or_insert(address, row)
                self.stats['historical_written'] += 1
            except Exception as e:
                self.logger.error(f"CSV update failed for HISTORICAL: {e}")
                self.stats['csv_errors'] += 1
            
            # Update Google Sheets (update existing row or append new)
            if self.sheets_writer:
                try:
                    await self.sheets_writer.update_or_insert_in_sheet('Historical', address, row)
                except Exception as e:
                    self.logger.error(f"Google Sheets update failed for HISTORICAL: {e}")
                    self.stats['sheets_errors'] += 1
                    
        except Exception as e:
            self.logger.error(f"Failed to write historical: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get output statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()
    
    async def close(self):
        """Close connections."""
        if self.sheets_writer:
            # Check if close method is async
            import asyncio
            if asyncio.iscoroutinefunction(self.sheets_writer.close):
                await self.sheets_writer.close()
            else:
                self.sheets_writer.close()
        self.logger.info(f"Data output closed. Stats: {self.stats}")
