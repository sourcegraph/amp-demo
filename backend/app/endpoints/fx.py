"""Foreign exchange rate endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from ..config import settings, CurrencyCode
from ..fx import fx_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fx", tags=["foreign exchange"])


@router.get("/status")
async def fx_status() -> Dict[str, Any]:
    """Get FX rates status for debugging."""
    rates = fx_service.get_cached_rates()
    is_stale = fx_service.is_cache_stale()
    
    if rates:
        return {
            "status": "stale" if is_stale else "fresh",
            "base": rates.base,
            "timestamp": rates.timestamp,
            "available_currencies": list(rates.rates.keys()) + ["USD"],
            "rates_count": len(rates.rates)
        }
    else:
        return {
            "status": "no_rates",
            "message": "No exchange rates cached"
        }


@router.get("/rates")
async def get_fx_rates() -> Dict[str, Any]:
    """Get current exchange rates."""
    try:
        rates = await fx_service.fetch_rates()
        return {
            "base": rates.base,
            "rates": rates.rates,
            "timestamp": rates.timestamp,
            "status": "stale" if fx_service.is_cache_stale() else "fresh"
        }
    except Exception as e:
        logger.error(f"Failed to fetch FX rates: {e}")
        raise HTTPException(
            status_code=503,
            detail="Currency exchange rates temporarily unavailable"
        )


@router.get("/currencies")
def get_supported_currencies() -> Dict[str, Any]:
    """Get list of supported currencies."""
    allowed_codes = [c.value for c in settings.allowed_currency_codes]
    
    # Currency display names
    currency_names = {
        "USD": "US Dollar",
        "GBP": "British Pound",
        "EUR": "Euro",
        "AUD": "Australian Dollar",
        "MXN": "Mexican Peso", 
        "JPY": "Japanese Yen",
        "CAD": "Canadian Dollar",
        "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan",
        "INR": "Indian Rupee"
    }
    
    currencies = []
    for code in allowed_codes:
        currencies.append({
            "code": code,
            "name": currency_names.get(code, code)
        })
    
    return {
        "currencies": currencies,
        "default": "USD"
    }


@router.post("/convert")
async def convert_currency(
    amount: float,
    from_currency: CurrencyCode,
    to_currency: CurrencyCode
) -> Dict[str, Any]:
    """Convert amount from one currency to another."""
    try:
        if fx_service.is_cache_stale():
            raise HTTPException(
                status_code=409,
                detail="Currency conversion rates are stale or unavailable. Please try again later."
            )
        
        converted_amount = await fx_service.convert(amount, from_currency, to_currency)
        
        cached_rates = fx_service.get_cached_rates()
        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": converted_amount,
            "timestamp": cached_rates.timestamp if cached_rates else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        raise HTTPException(
            status_code=409,
            detail="Currency conversion temporarily unavailable. Please try again later."
        )
