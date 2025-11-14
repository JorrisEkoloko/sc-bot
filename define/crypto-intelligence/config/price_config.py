"""Price engine configuration."""
from dataclasses import dataclass


@dataclass
class PriceConfig:
    """Price engine configuration."""
    coingecko_api_key: str
    birdeye_api_key: str
    moralis_api_key: str
    cryptocompare_api_key: str = ''  # Optional, for historical data
    cache_ttl: int = 300  # 5 minutes
    rate_limit_buffer: float = 0.9  # Use 90% of rate limit
    
    @classmethod
    def load_from_env(cls) -> 'PriceConfig':
        """Load price configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        
        # Load .env file
        load_dotenv()
        
        return cls(
            coingecko_api_key=os.getenv('COINGECKO_API_KEY', ''),
            birdeye_api_key=os.getenv('BIRDEYE_API_KEY', ''),
            moralis_api_key=os.getenv('MORALIS_API_KEY', ''),
            cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
            cache_ttl=int(os.getenv('PRICE_CACHE_TTL', '300')),
            rate_limit_buffer=float(os.getenv('PRICE_RATE_LIMIT_BUFFER', '0.9'))
        )
