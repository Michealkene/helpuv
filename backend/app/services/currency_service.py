import requests
from functools import lru_cache
from datetime import datetime, timedelta

class CurrencyService:
    """Service for currency conversion"""
    
    # Cache exchange rate for 1 hour
    _cache = {}
    _cache_time = None
    _cache_duration = timedelta(hours=1)
    
    @classmethod
    def get_usd_to_naira_rate(cls) -> float:
        """Get current USD to Naira exchange rate"""
        
        # Check cache
        if cls._cache_time and datetime.now() - cls._cache_time < cls._cache_duration:
            return cls._cache.get('usd_to_naira', 1650.0)  # Default fallback
        
        try:
            # Use free currency API
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/USD',
                timeout=5
            )
            data = response.json()
            rate = data['rates'].get('NGN', 1650.0)
            
            # Update cache
            cls._cache['usd_to_naira'] = rate
            cls._cache_time = datetime.now()
            
            return rate
        except Exception as e:
            print(f"Currency API error: {e}")
            # Return fallback rate if API fails
            return cls._cache.get('usd_to_naira', 1650.0)
    
    @classmethod
    def usd_to_naira(cls, usd_amount: float) -> float:
        """Convert USD to Naira"""
        rate = cls.get_usd_to_naira_rate()
        return round(usd_amount * rate, 2)
    
    @classmethod
    def naira_to_usd(cls, naira_amount: float) -> float:
        """Convert Naira to USD"""
        rate = cls.get_usd_to_naira_rate()
        return round(naira_amount / rate, 2)
