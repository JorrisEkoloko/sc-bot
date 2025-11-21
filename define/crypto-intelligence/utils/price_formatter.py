"""Price formatting utilities to prevent scientific notation in outputs.

Ensures prices are displayed in fixed notation with appropriate decimal places
for both very small (meme coins) and normal prices.
"""


class PriceFormatter:
    """Centralized price formatting for all tables."""
    
    @staticmethod
    def format_price(price: float) -> str:
        """
        Format price to avoid scientific notation.
        
        Uses different decimal precision based on price magnitude:
        - Very small (< 0.000001): 12 decimals
        - Small (< 0.01): 8 decimals
        - Normal (>= 0.01): 6 decimals
        
        Args:
            price: Price value to format
            
        Returns:
            Formatted price string (e.g., "0.000001230000" instead of "1.23e-06")
            
        Examples:
            >>> PriceFormatter.format_price(0.00000000123)
            '0.000000001230'
            >>> PriceFormatter.format_price(0.00123)
            '0.00123000'
            >>> PriceFormatter.format_price(1.23)
            '1.230000'
        """
        if price is None or price == 0:
            return ''
        
        try:
            price_float = float(price)
            
            if price_float < 0.000001:
                # For very small prices, use fixed notation with more decimals
                return f"{price_float:.12f}"
            elif price_float < 0.01:
                # For small prices, use 8 decimals
                return f"{price_float:.8f}"
            else:
                # For normal prices, use 6 decimals
                return f"{price_float:.6f}"
                
        except (ValueError, TypeError):
            # If conversion fails, return empty string
            return ''
    
    @staticmethod
    def format_price_or_empty(price) -> str:
        """
        Format price or return empty string if None/invalid.
        
        Args:
            price: Price value to format (can be None)
            
        Returns:
            Formatted price string or empty string
        """
        if price is None:
            return ''
        return PriceFormatter.format_price(price)
    
    @staticmethod
    def format_multiplier(multiplier: float, decimals: int = 4) -> str:
        """
        Format multiplier (e.g., ATH multiplier, ROI).
        
        Args:
            multiplier: Multiplier value
            decimals: Number of decimal places (default: 4)
            
        Returns:
            Formatted multiplier string
            
        Examples:
            >>> PriceFormatter.format_multiplier(2.5)
            '2.5000'
            >>> PriceFormatter.format_multiplier(100.123456, 2)
            '100.12'
        """
        if multiplier is None:
            return ''
        
        try:
            return f"{float(multiplier):.{decimals}f}"
        except (ValueError, TypeError):
            return ''
    
    @staticmethod
    def format_percentage(percentage: float, decimals: int = 2) -> str:
        """
        Format percentage value.
        
        Args:
            percentage: Percentage value
            decimals: Number of decimal places (default: 2)
            
        Returns:
            Formatted percentage string
            
        Examples:
            >>> PriceFormatter.format_percentage(12.3456)
            '12.35'
            >>> PriceFormatter.format_percentage(-5.67)
            '-5.67'
        """
        if percentage is None:
            return ''
        
        try:
            return f"{float(percentage):.{decimals}f}"
        except (ValueError, TypeError):
            return ''
    
    @staticmethod
    def format_large_number(number: float) -> str:
        """
        Format large numbers (market cap, volume) without scientific notation.
        
        Args:
            number: Large number to format
            
        Returns:
            Formatted number string
            
        Examples:
            >>> PriceFormatter.format_large_number(1234567890)
            '1234567890.00'
            >>> PriceFormatter.format_large_number(1.23e9)
            '1230000000.00'
        """
        if number is None or number == 0:
            return ''
        
        try:
            # Use 2 decimal places for large numbers
            return f"{float(number):.2f}"
        except (ValueError, TypeError):
            return ''
