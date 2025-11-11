# Step 4 Complete: HTTP Server (FastAPI)

## What Was Created

**Files**:
- `mcp_server/http_server.py` - FastAPI HTTP server
- `mcp_server/health.py` - Health and metrics endpoints

This creates an HTTP API server that exposes the MCP tools as REST endpoints.

---

## Key Features

### 1. **FastAPI Server**

Creates a modern, fast HTTP server with:
- Automatic API documentation at `/docs`
- Type validation using Pydantic
- Async support for high performance
- CORS enabled for frontend integration

### 2. **Three Tool Endpoints**

#### `POST /tools/search_title`
- Searches for movies/TV shows
- Request body: `{"query": "Inception", "type": "movie", "year": 2010, "language": "en"}`
- Returns: `{"results": [...]}`

#### `POST /tools/get_recommendations`
- Gets recommendations for a title
- Request body: `{"id": 27205, "type": "movie"}`
- Returns: `{"results": [...]}` with reasons

#### `POST /tools/discover`
- Discovers titles with filters
- Request body: `{"type": "movie", "genre": ["Action"], "year": 2020, "sort_by": "vote_average"}`
- Returns: `{"results": [...]}`

### 3. **Health & Observability**

#### `GET /health`
- Health check endpoint
- Returns server status, uptime, and metrics

#### `GET /health/metrics`
- Detailed metrics
- Tool call counts, latencies, success rates
- Recent errors

#### `GET /`
- API information
- Lists all available endpoints

### 4. **Error Handling**

Proper HTTP status codes:
- **200**: Success
- **400**: Bad request (validation errors)
- **404**: TITLE_NOT_FOUND
- **429**: RATE_LIMIT
- **500**: Server error

### 5. **Observability**

- Records all tool calls with latencies
- Tracks success/failure rates
- Logs errors with timestamps
- Provides metrics endpoint

---

## How to Run

### Start the Server

```bash
cd /home/Kushal7/Desktop/AI-agent
source venv/bin/activate
python -m mcp_server.http_server
```

Or using uvicorn directly:
```bash
uvicorn mcp_server.http_server:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### Access API Documentation

Open in browser: `http://localhost:8000/docs`

FastAPI automatically generates interactive API documentation where you can test endpoints!

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/health/metrics` | GET | Detailed metrics |
| `/docs` | GET | Interactive API docs (Swagger UI) |
| `/tools/search_title` | POST | Search for titles |
| `/tools/get_recommendations` | POST | Get recommendations |
| `/tools/discover` | POST | Discover with filters |

---

## Example Usage

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Search for a movie
curl -X POST http://localhost:8000/tools/search_title \
  -H "Content-Type: application/json" \
  -d '{"query": "Inception", "type": "movie"}'

# Get recommendations
curl -X POST http://localhost:8000/tools/get_recommendations \
  -H "Content-Type: application/json" \
  -d '{"id": 27205, "type": "movie"}'
```

### Using Python

```python
import httpx

async with httpx.AsyncClient() as client:
    # Search
    response = await client.post(
        "http://localhost:8000/tools/search_title",
        json={"query": "Inception", "type": "movie"}
    )
    results = response.json()["results"]
    
    # Get recommendations
    response = await client.post(
        "http://localhost:8000/tools/get_recommendations",
        json={"id": 27205, "type": "movie"}
    )
    recommendations = response.json()["results"]
```

---

## Testing

**Test file**: `test_http_server.py`

**To test**:
1. Start the server in one terminal:
   ```bash
   python -m mcp_server.http_server
   ```

2. Run tests in another terminal:
   ```bash
   python test_http_server.py
   ```

---

## Features

### ✅ CORS Enabled
- Allows frontend applications to call the API
- Ready for web frontend integration

### ✅ Automatic Documentation
- Swagger UI at `/docs`
- ReDoc at `/redoc`
- Interactive API testing

### ✅ Observability
- Tracks all tool calls
- Records latencies
- Monitors errors
- Provides metrics endpoint

### ✅ Error Handling
- Proper HTTP status codes
- Clear error messages
- Handles rate limits gracefully

---

## Architecture

```
HTTP Request
    ↓
FastAPI Server (http_server.py)
    ↓
Route Handler (e.g., /tools/search_title)
    ↓
Validate Request (Pydantic)
    ↓
Call Tool Function (tools.py)
    ↓
TMDB API Client (api_client.py)
    ↓
TMDB API
    ↓
Format Response
    ↓
Record Metrics
    ↓
Return JSON Response
```

---

## Next Steps

**Step 5**: Create the Agent
- Will use this HTTP server to call tools
- OpenAI-powered chat agent
- Command-line interface

**Step 6**: Add Streamlit Frontend
- Will call this HTTP server
- Beautiful web chatbox
- User-friendly interface

---

## Summary

✅ **Created**: HTTP server with FastAPI
- Three tool endpoints
- Health and metrics endpoints
- Automatic API documentation
- CORS enabled for frontend
- Observability built-in

✅ **Ready for**: 
- Agent integration (Step 5)
- Frontend integration (Step 6)

**The server is ready to be used by the agent and frontend!**

