import pytest
from datetime import datetime, timedelta
from app.fx import FXService, CurrencyCode, FXRates


class TestFXService:
    @pytest.fixture
    def fx_service(self):
        """Create FX service instance for testing."""
        return FXService()

    @pytest.mark.asyncio
    async def test_mock_rates_fallback(self, fx_service):
        """Test that mock rates are returned when no API key is provided."""
        rates = await fx_service.fetch_rates()
        
        assert rates.base == "USD"
        assert "GBP" in rates.rates
        assert "EUR" in rates.rates
        assert "AUD" in rates.rates
        assert "MXN" in rates.rates
        assert "JPY" in rates.rates
        assert isinstance(rates.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_currency_conversion_same_currency(self, fx_service):
        """Test conversion when source and target currencies are the same."""
        amount = 100.0
        result = await fx_service.convert(amount, CurrencyCode.USD, CurrencyCode.USD)
        assert result == amount

    @pytest.mark.asyncio
    async def test_currency_conversion_to_usd(self, fx_service):
        """Test conversion from other currency to USD."""
        # First fetch rates to cache them
        await fx_service.fetch_rates()
        
        result = await fx_service.convert(100.0, CurrencyCode.GBP, CurrencyCode.USD)
        # With mock rate of 0.79 GBP/USD, 100 GBP should be ~126.58 USD
        assert result > 100  # Should be more USD than GBP
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_currency_conversion_from_usd(self, fx_service):
        """Test conversion from USD to other currency."""
        await fx_service.fetch_rates()
        
        result = await fx_service.convert(100.0, CurrencyCode.USD, CurrencyCode.EUR)
        # With mock rate of 0.85 EUR/USD, 100 USD should be 85 EUR
        assert result < 100  # Should be less EUR than USD
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_currency_conversion_between_non_usd(self, fx_service):
        """Test conversion between two non-USD currencies."""
        await fx_service.fetch_rates()
        
        result = await fx_service.convert(100.0, CurrencyCode.GBP, CurrencyCode.EUR)
        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_invalid_currency_conversion(self, fx_service):
        """Test that invalid currency raises appropriate error."""
        # Mock a custom service with limited rates
        fx_service._cached_rates = FXRates(
            base="USD",
            rates={"EUR": 0.85},  # Only EUR, no GBP
            timestamp=datetime.utcnow()
        )
        fx_service._cache_expiry = datetime.utcnow() + timedelta(hours=1)
        
        with pytest.raises(ValueError, match="No exchange rate available for CurrencyCode.GBP"):
            await fx_service.convert(100.0, CurrencyCode.GBP, CurrencyCode.USD)

    def test_cache_validity(self, fx_service):
        """Test cache validity checking."""
        # Initially no cache
        assert not fx_service._is_cache_valid()
        
        # Set cache with future expiry
        fx_service._cached_rates = FXRates(
            base="USD",
            rates={"EUR": 0.85},
            timestamp=datetime.utcnow()
        )
        fx_service._cache_expiry = datetime.utcnow() + timedelta(hours=1)
        assert fx_service._is_cache_valid()
        
        # Set cache with past expiry
        fx_service._cache_expiry = datetime.utcnow() - timedelta(hours=1)
        assert not fx_service._is_cache_valid()

    def test_is_cache_stale(self, fx_service):
        """Test cache staleness detection."""
        # Initially stale
        assert fx_service.is_cache_stale()
        
        # Set fresh cache
        fx_service._cached_rates = FXRates(
            base="USD",
            rates={"EUR": 0.85},
            timestamp=datetime.utcnow()
        )
        fx_service._cache_expiry = datetime.utcnow() + timedelta(hours=1)
        assert not fx_service.is_cache_stale()
        
        # Make cache stale
        fx_service._cache_expiry = datetime.utcnow() - timedelta(hours=1)
        assert fx_service.is_cache_stale()

    def test_get_cached_rates(self, fx_service):
        """Test getting cached rates."""
        # Initially None
        assert fx_service.get_cached_rates() is None
        
        # Set cache
        rates = FXRates(
            base="USD",
            rates={"EUR": 0.85},
            timestamp=datetime.utcnow()
        )
        fx_service._cached_rates = rates
        
        cached = fx_service.get_cached_rates()
        assert cached == rates
        assert cached.base == "USD"
        assert "EUR" in cached.rates
