"""
HTTP Session Manager for Torob AI Assistant

Manages aiohttp sessions to prevent file descriptor leaks.
"""

import asyncio
import aiohttp
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages HTTP sessions to prevent file descriptor leaks"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create a shared HTTP session"""
        if self._session is None or self._session.closed:
            async with self._lock:
                if self._session is None or self._session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=100,  # Total connection pool size
                        limit_per_host=30,  # Per-host connection limit
                        ttl_dns_cache=300,  # DNS cache TTL
                        use_dns_cache=True,
                    )
                    timeout = aiohttp.ClientTimeout(total=30)
                    self._session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout
                    )
                    logger.info("Created new HTTP session")
        return self._session
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Closed HTTP session")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

# Global session manager instance
session_manager = SessionManager()

async def get_http_session() -> aiohttp.ClientSession:
    """Get the global HTTP session"""
    return await session_manager.get_session()

async def cleanup_sessions():
    """Cleanup all HTTP sessions"""
    await session_manager.close()
