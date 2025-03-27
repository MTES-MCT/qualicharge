"""QualiCharge cache management."""

from aiocache import SimpleMemoryCache
from aiocache.plugins import HitMissRatioPlugin

from .conf import settings

amemory = SimpleMemoryCache(
    ttl=settings.API_CACHE_TTL,
    plugins=[
        HitMissRatioPlugin,
    ],
)
