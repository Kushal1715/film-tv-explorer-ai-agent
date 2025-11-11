"""TMDB API client with retry logic, rate limiting, and error handling."""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass

class TMDBClient:
    """Client for TMDB API with retry, backoff, and rate limit handling."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 60.0
    RATE_LIMIT_WINDOW = 40  # requests per 10 seconds (TMDB limit)
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        if not self.api_key:
            raise ValueError("TMDB_API_KEY environment variable is required")
        
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=10.0
        )
        
        # Rate limiting tracking
        self.request_times: List[float] = []
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def _check_rate_limit(self):
        """Check and enforce rate limits."""
        now = time.time()
        # Remove requests older than 10 seconds
        self.request_times = [t for t in self.request_times if now - t < 10]
        
        if len(self.request_times) >= self.RATE_LIMIT_WINDOW:
            sleep_time = 10 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                # Re-check after sleep
                now = time.time()
                self.request_times = [t for t in self.request_times if now - t < 10]
        
        self.request_times.append(now)
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and params."""
        sorted_params = sorted(params.items())
        return f"{endpoint}:{sorted_params}"
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make API request with retry and backoff."""
        params = params or {}
        params["api_key"] = self.api_key
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(endpoint, params)
            if cache_key in self._cache:
                data, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.debug(f"Cache hit for {endpoint}")
                    return data
        
        backoff = self.INITIAL_BACKOFF
        
        for attempt in range(self.MAX_RETRIES):
            try:
                await self._check_rate_limit()
                
                response = await self.client.request(
                    method,
                    endpoint,
                    params=params
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", backoff))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Cache the response
                if use_cache:
                    self._cache[cache_key] = (data, time.time())
                
                return data
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError("TITLE_NOT_FOUND")
                elif e.response.status_code == 429:
                    if attempt < self.MAX_RETRIES - 1:
                        retry_after = int(e.response.headers.get("Retry-After", backoff))
                        logger.warning(f"Rate limited, retrying after {retry_after}s")
                        await asyncio.sleep(retry_after)
                        backoff = min(backoff * 2, self.MAX_BACKOFF)
                        continue
                    else:
                        raise RateLimitError("RATE_LIMIT")
                else:
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning(f"Request failed: {e}, retrying in {backoff}s")
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, self.MAX_BACKOFF)
                        continue
                    raise
                    
            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Request error: {e}, retrying in {backoff}s")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, self.MAX_BACKOFF)
                    continue
                raise
    
    async def search_title(
        self,
        query: str,
        type: Optional[str] = None,
        year: Optional[int] = None,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for movies or TV shows."""
        search_type = type or "movie"
        endpoint = f"/search/{search_type}"
        
        params = {"query": query}
        if year:
            params["year"] = year
        if language:
            params["language"] = language
        
        data = await self._request("GET", endpoint, params)
        return data.get("results", [])
    
    async def get_recommendations(
        self,
        id: int,
        type: str
    ) -> List[Dict[str, Any]]:
        """Get recommendations for a movie or TV show."""
        endpoint = f"/{type}/{id}/recommendations"
        
        data = await self._request("GET", endpoint)
        return data.get("results", [])
    
    async def discover(
        self,
        type: str,
        genre: Optional[List[str]] = None,
        year: Optional[int] = None,
        language: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover movies or TV shows with filters."""
        endpoint = f"/discover/{type}"
        
        params = {}
        if genre:
            # Get genre IDs from names
            genre_ids = await self._get_genre_ids(type, genre)
            if genre_ids:
                params["with_genres"] = ",".join(map(str, genre_ids))
        if year:
            params["primary_release_year" if type == "movie" else "first_air_date_year"] = year
        if language:
            params["with_original_language"] = language
        if sort_by:
            params["sort_by"] = sort_by + ".desc"
        
        data = await self._request("GET", endpoint, params)
        return data.get("results", [])
    
    async def get_details(self, id: int, type: str) -> Dict[str, Any]:
        """Get detailed information about a title."""
        endpoint = f"/{type}/{id}"
        return await self._request("GET", endpoint)
    
    async def _get_genre_ids(self, type: str, genre_names: List[str]) -> List[int]:
        """Convert genre names to IDs."""
        endpoint = f"/genre/{type}/list"
        data = await self._request("GET", endpoint, use_cache=True)
        genres = {g["name"].lower(): g["id"] for g in data.get("genres", [])}
        
        ids = []
        for name in genre_names:
            name_lower = name.lower()
            if name_lower in genres:
                ids.append(genres[name_lower])
        return ids
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

