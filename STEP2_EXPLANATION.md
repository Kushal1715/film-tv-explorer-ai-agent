# Step 2 Complete: TMDB API Client

## What Was Created

**File**: `mcp_server/api_client.py`

This file contains the `TMDBClient` class - a robust client for interacting with the TMDB (The Movie Database) API.

---

## Key Features Implemented

### 1. **Retry Logic with Exponential Backoff**
```python
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # Start with 1 second
MAX_BACKOFF = 60.0     # Max 60 seconds
```

**What it does**:
- If a request fails, it retries up to 3 times
- Each retry waits longer: 1s → 2s → 4s (exponential backoff)
- Prevents overwhelming the API if it's temporarily down

**Why it's important**:
- Network issues are temporary - retries often succeed
- Protects against transient failures
- Makes the system more resilient

---

### 2. **Rate Limiting**
```python
RATE_LIMIT_WINDOW = 40  # requests per 10 seconds
```

**What it does**:
- Tracks how many requests we've made in the last 10 seconds
- If we approach the limit (40 requests), it waits before making more
- Handles 429 (Too Many Requests) errors gracefully

**Why it's important**:
- TMDB API has rate limits (40 requests per 10 seconds)
- Prevents getting blocked for making too many requests
- Automatically waits and retries when rate limited

---

### 3. **Caching**
```python
_cache_ttl = 300  # 5 minutes
```

**What it does**:
- Stores API responses in memory for 5 minutes
- If the same request is made again, returns cached data
- Reduces API calls and improves speed

**Why it's important**:
- Faster responses for repeated queries
- Reduces API usage (stays within rate limits)
- Saves bandwidth

---

### 4. **Error Handling**

**Custom Exceptions**:
- `RateLimitError`: When rate limit is exceeded
- `ValueError("TITLE_NOT_FOUND")`: When a title doesn't exist (404)

**HTTP Status Handling**:
- **404**: Raises `TITLE_NOT_FOUND` error
- **429**: Retries with backoff, or raises `RateLimitError`
- **Other errors**: Retries with exponential backoff

**Why it's important**:
- Provides clear error messages
- Allows the agent to handle errors gracefully
- Prevents crashes from unexpected API responses

---

## Main Methods

### 1. `search_title(query, type, year, language)`
**Purpose**: Search for movies or TV shows

**Example**:
```python
results = await client.search_title("Inception", type="movie", year=2010)
```

**Returns**: List of matching titles with details

---

### 2. `get_recommendations(id, type)`
**Purpose**: Get recommendations for a specific movie/TV show

**Example**:
```python
recs = await client.get_recommendations(27205, "movie")  # Inception's ID
```

**Returns**: List of recommended titles

---

### 3. `discover(type, genre, year, language, sort_by)`
**Purpose**: Discover movies/TV shows with filters

**Example**:
```python
results = await client.discover(
    type="movie",
    genre=["Thriller", "Action"],
    year=2020,
    language="en",
    sort_by="vote_average"
)
```

**Returns**: List of titles matching the filters

---

### 4. `get_details(id, type)`
**Purpose**: Get detailed information about a title

**Example**:
```python
details = await client.get_details(27205, "movie")
```

**Returns**: Full details including genres, cast, overview, etc.

---

## How It Works

```
User Request
    ↓
TMDBClient Method (e.g., search_title)
    ↓
_check_rate_limit() → Wait if needed
    ↓
Check Cache → Return if found
    ↓
_request() → Make HTTP request
    ↓
If error → Retry with backoff (up to 3 times)
    ↓
Cache response → Store for 5 minutes
    ↓
Return results
```

---

## Testing

A simple test file was created: `test_api_client_simple.py`

**To test**:
```bash
# Make sure TMDB_API_KEY is set
export TMDB_API_KEY="your_key_here"

# Or create .env file with:
# TMDB_API_KEY=your_key_here

# Run the test
python test_api_client_simple.py
```

**What it tests**:
1. ✅ Search for a movie
2. ✅ Get movie details
3. ✅ Get recommendations

---

## Code Structure

```python
class TMDBClient:
    # Configuration
    BASE_URL = "https://api.themoviedb.org/3"
    MAX_RETRIES = 3
    ...
    
    # Core request method (handles retry, rate limit, cache)
    async def _request(...)
    
    # Public API methods
    async def search_title(...)
    async def get_recommendations(...)
    async def discover(...)
    async def get_details(...)
    
    # Helper methods
    async def _check_rate_limit(...)
    async def _get_genre_ids(...)
```

---

## What's Next?

**Step 3**: Create MCP Tools
- Use this API client to create the tool functions
- Add input validation with Pydantic
- Format responses according to the MCP spec

---

## Summary

✅ **Created**: `mcp_server/api_client.py`
- Retry logic with exponential backoff
- Rate limiting protection
- Caching (5-minute TTL)
- Comprehensive error handling
- Methods for search, recommendations, discover, and details

**This client is now ready to be used by the MCP tools in Step 3!**

