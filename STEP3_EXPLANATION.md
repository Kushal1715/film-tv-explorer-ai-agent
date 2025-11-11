# Step 3 Complete: MCP Tools

## What Was Created

**File**: `mcp_server/tools.py`

This file contains the three MCP tools that wrap the TMDB API client:
1. `search_title` - Search for movies/TV shows
2. `get_recommendations` - Get recommendations for a title
3. `discover` - Discover titles with filters

---

## Key Features

### 1. **Input Validation with Pydantic**

Each tool uses Pydantic models to validate inputs:

#### `SearchTitleArgs`
```python
class SearchTitleArgs(BaseModel):
    query: str                    # Required
    type: Optional[str] = None    # Must be "movie" or "tv"
    year: Optional[int] = None    # Must be a number
    language: Optional[str] = None # Language code
```

**Validation**:
- ✅ `type` must be "movie" or "tv" (if provided)
- ✅ `year` must be an integer (if provided)
- ✅ `query` is required

#### `GetRecommendationsArgs`
```python
class GetRecommendationsArgs(BaseModel):
    id: int      # Required - TMDB ID
    type: str    # Required - Must be "movie" or "tv"
```

**Validation**:
- ✅ `type` must be "movie" or "tv"
- ✅ `id` must be an integer

#### `DiscoverArgs`
```python
class DiscoverArgs(BaseModel):
    type: str                           # Required - "movie" or "tv"
    genre: Optional[List[str]] = None   # List of genre names
    year: Optional[int] = None
    language: Optional[str] = None
    sort_by: Optional[str] = None       # Must be "popularity" or "vote_average"
```

**Validation**:
- ✅ `type` must be "movie" or "tv"
- ✅ `sort_by` must be "popularity" or "vote_average" (if provided)

---

### 2. **Response Formatting**

All tools format responses according to the MCP specification:

#### `search_title` Response Format
```python
{
    "id": 27205,
    "title": "Inception",
    "type": "movie",
    "year": 2010,
    "rating": 8.37,
    "overview": "A skilled thief...",
    "poster_path": "/path/to/poster.jpg"
}
```

#### `get_recommendations` Response Format
```python
{
    "id": 11324,
    "title": "Shutter Island",
    "year": 2010,
    "reason": "Similar to Inception (shared Action, Thriller genres, highly rated)"
}
```

**Key Feature**: The `reason` field explains WHY each recommendation is similar using metadata (genres, ratings).

#### `discover` Response Format
Same as `search_title` - returns formatted title results.

---

### 3. **Error Handling**

All tools properly handle errors:

- **TITLE_NOT_FOUND**: Re-raised as-is (from API client)
- **RATE_LIMIT**: Re-raised as-is (from API client)
- **Validation errors**: Caught and re-raised with clear messages
- **Other errors**: Wrapped in ValueError with descriptive message

---

## Tool Functions

### 1. `search_title(client, args)`

**Purpose**: Search for movies or TV shows

**Input**: `SearchTitleArgs` object
- `query`: Search term (required)
- `type`: "movie" or "tv" (optional)
- `year`: Release year (optional)
- `language`: Language code (optional)

**Output**: List of formatted title results (max 10)

**Example**:
```python
args = SearchTitleArgs(query="Inception", type="movie", year=2010)
results = await search_title(client, args)
```

---

### 2. `get_recommendations(client, args)`

**Purpose**: Get recommendations for a specific title

**Input**: `GetRecommendationsArgs` object
- `id`: TMDB ID of the title (required)
- `type`: "movie" or "tv" (required)

**Output**: List of recommendations with reasons (max 10)

**Key Feature**: 
- Fetches original title details to get genres
- Compares genres between original and recommendations
- Generates a "reason" explaining why each recommendation is similar
- Includes rating information in the reason

**Example**:
```python
args = GetRecommendationsArgs(id=27205, type="movie")
recs = await get_recommendations(client, args)
# Returns: [{"id": 11324, "title": "Shutter Island", "year": 2010, "reason": "Similar to Inception (shared Action genres, highly rated)"}, ...]
```

---

### 3. `discover(client, args)`

**Purpose**: Discover movies/TV shows with filters

**Input**: `DiscoverArgs` object
- `type`: "movie" or "tv" (required)
- `genre`: List of genre names (optional)
- `year`: Release year (optional)
- `language`: Language code (optional)
- `sort_by`: "popularity" or "vote_average" (optional)

**Output**: List of formatted title results (max 20)

**Example**:
```python
args = DiscoverArgs(
    type="movie",
    genre=["Action", "Thriller"],
    year=2020,
    language="en",
    sort_by="vote_average"
)
results = await discover(client, args)
```

---

## Helper Functions

### `format_title_result(result, type)`

Formats raw TMDB API response into MCP spec format:
- Extracts year from release_date/first_air_date
- Handles both movies and TV shows
- Returns standardized format with all required fields

---

## Testing

**Test file**: `test_tools.py`

**What it tests**:
1. ✅ `search_title` - Returns correct format
2. ✅ `get_recommendations` - Includes reasons
3. ✅ `discover` - Works with filters
4. ✅ Input validation - Catches invalid inputs

**Run tests**:
```bash
source venv/bin/activate
python test_tools.py
```

---

## How It Works

```
User/Agent calls tool
    ↓
Pydantic validates input
    ↓
Tool function called
    ↓
Calls TMDB API client method
    ↓
Formats response according to MCP spec
    ↓
Returns formatted results
```

---

## MCP Specification Compliance

### Tool 1: `search_title`
- ✅ Returns: `Array<{ id, title, type, year, rating, overview, poster_path? }>`
- ✅ Supports optional filters: type, year, language

### Tool 2: `get_recommendations`
- ✅ Returns: `Array<{ id, title, year, reason? }>`
- ✅ Includes `reason` field with metadata-based explanation

### Tool 3: `discover`
- ✅ Returns: Same format as `search_title`
- ✅ Supports filters: genre, year, language, sort_by

### Error Handling
- ✅ `TITLE_NOT_FOUND` - Raised when title doesn't exist
- ✅ `RATE_LIMIT` - Raised when rate limit exceeded

---

## Summary

✅ **Created**: `mcp_server/tools.py`
- Three MCP tools with input validation
- Proper response formatting per MCP spec
- Error handling
- Metadata-based recommendation reasons

✅ **Tested**: All tools working correctly
- Input validation works
- Response formats match spec
- Recommendations include reasons

**Ready for Step 4: Create HTTP Server (FastAPI) for MCP tools!**


