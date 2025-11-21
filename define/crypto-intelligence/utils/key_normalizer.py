"""Key normalization utilities for consistent data matching across tables.

Provides centralized normalization logic to prevent duplicates caused by:
- Case differences (0xABC vs 0xabc)
- Quote prefixes ('0x123 vs 0x123)
- Symbol case variations (ETH vs eth)

Also provides price formatting to prevent scientific notation in sheets.
"""


class PriceFormatter:
    """Price formatting utilities to prevent scientific notation."""
    
    @staticmethod
    def format_price(price: float) -> str:
        """
        Format price to avoid scientific notation for very small numbers.
        
        Args:
            price: Price value to format
            
        Returns:
            Formatted price string with appropriate decimal places
            
        Examples:
            0.00000000123 → "0.000000001230"
            0.00123 → "0.00123000"
            1.23 → "1.230000"
        """
        if price is None or price == 0:
            return ''
        
        try:
            price_float = float(price)
            
            if price_float < 0.000001:
                # For very small prices, use fixed notation with 12 decimals
                return f"{price_float:.12f}"
            elif price_float < 0.01:
                # For small prices, use 8 decimals
                return f"{price_float:.8f}"
            else:
                # For normal prices, use 6 decimals
                return f"{price_float:.6f}"
        except (ValueError, TypeError):
            return str(price)


class KeyNormalizer:
    """Centralized key normalization for all tables."""
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """
        Normalize address for consistent matching.
        
        Args:
            address: Token contract address
            
        Returns:
            Normalized address (lowercase, no quote prefix)
        """
        if not address:
            return ''
        
        addr = str(address).strip()
        
        # Remove leading single quote (Google Sheets text formatting)
        if addr.startswith("'"):
            addr = addr[1:]
        
        # Lowercase for case-insensitive matching
        addr = addr.lower()
        
        return addr
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normalize symbol for consistent matching.
        
        Args:
            symbol: Token symbol
            
        Returns:
            Normalized symbol (uppercase, no quote prefix)
        """
        if not symbol:
            return ''
        
        sym = str(symbol).strip()
        
        # Remove leading single quote (Google Sheets text formatting)
        if sym.startswith("'"):
            sym = sym[1:]
        
        # Uppercase for case-insensitive matching
        sym = sym.upper()
        
        return sym
    
    @staticmethod
    def normalize_message_id(message_id: str) -> str:
        """
        Normalize message ID for consistent matching.
        
        Args:
            message_id: Message ID
            
        Returns:
            Normalized message ID (no quote prefix, keep case)
        """
        if not message_id:
            return ''
        
        msg_id = str(message_id).strip()
        
        # Remove leading single quote (Google Sheets text formatting)
        if msg_id.startswith("'"):
            msg_id = msg_id[1:]
        
        return msg_id
    
    @staticmethod
    def normalize_key_by_column(value: str, column_index: int, table_name: str) -> str:
        """
        Normalize key value based on column type and table.
        
        Args:
            value: Key value to normalize
            column_index: Column index in the table
            table_name: Name of the table
            
        Returns:
            Normalized key value
        """
        # Performance table: [address, chain, symbol, first_message_id, ...]
        if table_name.lower() == 'performance':
            if column_index == 0:  # address
                return KeyNormalizer.normalize_address(value)
            elif column_index == 2:  # symbol
                return KeyNormalizer.normalize_symbol(value)
            elif column_index == 3:  # first_message_id
                return KeyNormalizer.normalize_message_id(value)
        
        # Token Prices table: [address, chain, symbol, ...]
        elif table_name.lower() in ['token_prices', 'token prices']:
            if column_index == 0:  # address
                return KeyNormalizer.normalize_address(value)
            elif column_index == 2:  # symbol
                return KeyNormalizer.normalize_symbol(value)
        
        # Historical table: [address, chain, symbol, ...]
        elif table_name.lower() == 'historical':
            if column_index == 0:  # address
                return KeyNormalizer.normalize_address(value)
            elif column_index == 2:  # symbol
                return KeyNormalizer.normalize_symbol(value)
        
        # Default: just strip quotes and whitespace
        val = str(value).strip()
        if val.startswith("'"):
            val = val[1:]
        return val
    
    @staticmethod
    def normalize_composite_key(key_values: list, key_column_indices: list, table_name: str) -> list:
        """
        Normalize composite key values.
        
        Args:
            key_values: List of key values
            key_column_indices: List of column indices for the keys
            table_name: Name of the table
            
        Returns:
            List of normalized key values
        """
        normalized = []
        for value, col_idx in zip(key_values, key_column_indices):
            normalized.append(
                KeyNormalizer.normalize_key_by_column(value, col_idx, table_name)
            )
        return normalized
