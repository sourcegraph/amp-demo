"""Application configuration and settings."""
from typing import List
from pydantic_settings import BaseSettings
from enum import Enum


class CurrencyCode(str, Enum):
    USD = "USD"
    GBP = "GBP"
    EUR = "EUR"
    AUD = "AUD"
    MXN = "MXN"
    JPY = "JPY"
    CAD = "CAD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./store.db"
    
    # Currency Exchange API
    fx_api_key: str | None = None
    fx_base_url: str = "https://openexchangerates.org/api"
    fx_cache_ttl_hours: int = 1
    
    # Allowed currencies for conversion
    allowed_currencies: str = "USD,GBP,EUR,AUD,MXN,JPY"
    
    # Application settings
    debug: bool = False
    disable_scheduler: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_currency_codes(self) -> List[CurrencyCode]:
        """Get list of allowed currency codes."""
        currencies = [c.strip().upper() for c in self.allowed_currencies.split(",")]
        valid_currencies = []
        
        for currency in currencies:
            try:
                valid_currencies.append(CurrencyCode(currency))
            except ValueError:
                # Skip invalid currency codes
                continue
                
        return valid_currencies if valid_currencies else [CurrencyCode.USD]


# Global settings instance
settings = Settings()
