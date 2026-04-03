import os
import logging
from typing import Optional
import redis.asyncio as aioredis
import redis as syncredis

logger = logging.getLogger(__name__)

# Singletons for reusing connection pools
_async_redis_client: Optional[aioredis.Redis] = None
_sync_redis_client: Optional[syncredis.Redis] = None

def get_redis_url() -> str:
    """Get the Redis connection URL from the environment, defaulting to localhost."""
    return os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

def get_async_redis() -> aioredis.Redis:
    """Get or create the global async Redis client."""
    global _async_redis_client
    if _async_redis_client is None:
        url = get_redis_url()
        logger.info(f"Connecting to async Redis at {url}")
        # Add timeouts to prevent indefinite hangs
        _async_redis_client = aioredis.from_url(
            url, 
            decode_responses=True, 
            socket_timeout=5.0, 
            socket_connect_timeout=5.0
        )
    return _async_redis_client

def get_sync_redis() -> syncredis.Redis:
    """Get or create the global sync Redis client. 
    Useful for background threads that don't have an active asyncio loop.
    """
    global _sync_redis_client
    if _sync_redis_client is None:
        url = get_redis_url()
        logger.info(f"Connecting to sync Redis at {url}")
        # Add timeouts to prevent indefinite hangs
        _sync_redis_client = syncredis.from_url(
            url, 
            decode_responses=True, 
            socket_timeout=5.0, 
            socket_connect_timeout=5.0
        )
    return _sync_redis_client

async def close_redis_connections():
    """Gracefully close all connection pools during app shutdown."""
    global _async_redis_client, _sync_redis_client
    if _async_redis_client:
        await _async_redis_client.aclose()
        _async_redis_client = None
    if _sync_redis_client:
        _sync_redis_client.close()
        _sync_redis_client = None
