"""
Currency conversion using ExchangeRate-API.
Caches exchange rates in memory for 24 hours to minimize API calls.
Free tier: 1,500 calls/month.
"""
import httpx
import logging
import time

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory cache: {("USD", "INR"): {"rate": 83.5, "timestamp": 1710000000}}
_rate_cache: dict[tuple[str, str], dict] = {}
CACHE_TTL_SECONDS = 86400  # 24 hours


async def get_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    """
    Get exchange rate from one currency to another.
    Returns the conversion rate or None on failure.
    Caches results for 24 hours.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return 1.0

    # Check cache
    cache_key = (from_currency, to_currency)
    cached = _rate_cache.get(cache_key)
    if cached and (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS:
        return cached["rate"]

    # Fetch from API
    if not settings.EXCHANGERATE_API_KEY:
        logger.warning("ExchangeRate API key not configured")
        return None

    url = f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGERATE_API_KEY}/pair/{from_currency}/{to_currency}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)

            if response.status_code != 200:
                logger.error(f"ExchangeRate API failed: {response.status_code}")
                return None

            data = response.json()

            if data.get("result") != "success":
                logger.error(f"ExchangeRate API error: {data.get('error-type', 'unknown')}")
                return None

            rate = data.get("conversion_rate")
            if rate is None:
                return None

            # Cache the rate
            _rate_cache[cache_key] = {"rate": rate, "timestamp": time.time()}

            # Also cache the inverse
            inverse_key = (to_currency, from_currency)
            _rate_cache[inverse_key] = {"rate": 1.0 / rate, "timestamp": time.time()}

            return rate

        except Exception as e:
            logger.error(f"ExchangeRate API error: {e}")
            return None


async def convert(amount: float, from_currency: str, to_currency: str) -> float | None:
    """
    Convert an amount from one currency to another.
    Returns the converted amount or None on failure.
    """
    rate = await get_exchange_rate(from_currency, to_currency)
    if rate is None:
        return None
    return round(amount * rate, 2)
