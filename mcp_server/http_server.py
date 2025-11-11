"""HTTP-based MCP server for easier integration."""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .api_client import TMDBClient, RateLimitError
from .tools import (
    SearchTitleArgs,
    GetRecommendationsArgs,
    GetDetailsArgs,
    DiscoverArgs,
    search_title,
    get_recommendations,
    get_details,
    discover
)
from .health import record_tool_call, record_error, get_health_response, get_metrics_response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="TMDB MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health routes
from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("")
async def health():
    """Health check endpoint."""
    return get_health_response()

@health_router.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    return get_metrics_response()

app.include_router(health_router, prefix="/health", tags=["health"])

# Global client instance
_client: Optional[TMDBClient] = None

def get_client() -> TMDBClient:
    """Get or create TMDB client."""
    global _client
    if _client is None:
        _client = TMDBClient()
    return _client

# Request models
class SearchTitleRequest(BaseModel):
    query: str
    type: Optional[str] = None
    year: Optional[int] = None
    language: Optional[str] = None

class GetRecommendationsRequest(BaseModel):
    id: int
    type: str

class GetDetailsRequest(BaseModel):
    id: int
    type: str

class DiscoverRequest(BaseModel):
    type: str
    genre: Optional[List[str]] = None
    year: Optional[int] = None
    language: Optional[str] = None
    sort_by: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "TMDB MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "search_title": "POST /tools/search_title",
            "get_recommendations": "POST /tools/get_recommendations",
            "get_details": "POST /tools/get_details",
            "discover": "POST /tools/discover",
            "health": "GET /health"
        },
        "documentation": "/docs"
    }

@app.post("/tools/search_title")
async def tool_search_title(request: SearchTitleRequest):
    """Search title tool endpoint."""
    start_time = time.time()
    
    try:
        client = get_client()
        args = SearchTitleArgs(**request.model_dump())
        results = await search_title(client, args)
        
        latency = time.time() - start_time
        record_tool_call("search_title", latency, True)
        
        return {"results": results}
    except ValueError as e:
        error_msg = str(e)
        latency = time.time() - start_time
        record_tool_call("search_title", latency, False)
        record_error("ValueError", error_msg)
        
        if error_msg == "TITLE_NOT_FOUND":
            raise HTTPException(status_code=404, detail="TITLE_NOT_FOUND")
        raise HTTPException(status_code=400, detail=error_msg)
    except RateLimitError:
        latency = time.time() - start_time
        record_tool_call("search_title", latency, False)
        record_error("RateLimitError", "RATE_LIMIT")
        raise HTTPException(status_code=429, detail="RATE_LIMIT")
    except Exception as e:
        latency = time.time() - start_time
        record_tool_call("search_title", latency, False)
        record_error("Exception", str(e))
        logger.error(f"Error in search_title: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/get_recommendations")
async def tool_get_recommendations(request: GetRecommendationsRequest):
    """Get recommendations tool endpoint."""
    start_time = time.time()
    
    try:
        client = get_client()
        args = GetRecommendationsArgs(**request.model_dump())
        results = await get_recommendations(client, args)
        
        latency = time.time() - start_time
        record_tool_call("get_recommendations", latency, True)
        
        return {"results": results}
    except ValueError as e:
        error_msg = str(e)
        latency = time.time() - start_time
        record_tool_call("get_recommendations", latency, False)
        record_error("ValueError", error_msg)
        
        if error_msg == "TITLE_NOT_FOUND":
            raise HTTPException(status_code=404, detail="TITLE_NOT_FOUND")
        raise HTTPException(status_code=400, detail=error_msg)
    except RateLimitError:
        latency = time.time() - start_time
        record_tool_call("get_recommendations", latency, False)
        record_error("RateLimitError", "RATE_LIMIT")
        raise HTTPException(status_code=429, detail="RATE_LIMIT")
    except Exception as e:
        latency = time.time() - start_time
        record_tool_call("get_recommendations", latency, False)
        record_error("Exception", str(e))
        logger.error(f"Error in get_recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/get_details")
async def tool_get_details(request: GetDetailsRequest):
    """Get details tool endpoint."""
    start_time = time.time()
    
    try:
        client = get_client()
        args = GetDetailsArgs(**request.model_dump())
        result = await get_details(client, args)
        
        latency = time.time() - start_time
        record_tool_call("get_details", latency, True)
        
        return {"result": result}
    except ValueError as e:
        error_msg = str(e)
        latency = time.time() - start_time
        record_tool_call("get_details", latency, False)
        record_error("ValueError", error_msg)
        
        if error_msg == "TITLE_NOT_FOUND":
            raise HTTPException(status_code=404, detail="TITLE_NOT_FOUND")
        raise HTTPException(status_code=400, detail=error_msg)
    except RateLimitError:
        latency = time.time() - start_time
        record_tool_call("get_details", latency, False)
        record_error("RateLimitError", "RATE_LIMIT")
        raise HTTPException(status_code=429, detail="RATE_LIMIT")
    except Exception as e:
        latency = time.time() - start_time
        record_tool_call("get_details", latency, False)
        record_error("Exception", str(e))
        logger.error(f"Error in get_details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/discover")
async def tool_discover(request: DiscoverRequest):
    """Discover tool endpoint."""
    start_time = time.time()
    
    try:
        client = get_client()
        args = DiscoverArgs(**request.model_dump())
        results = await discover(client, args)
        
        latency = time.time() - start_time
        record_tool_call("discover", latency, True)
        
        return {"results": results}
    except ValueError as e:
        error_msg = str(e)
        latency = time.time() - start_time
        record_tool_call("discover", latency, False)
        record_error("ValueError", error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except RateLimitError:
        latency = time.time() - start_time
        record_tool_call("discover", latency, False)
        record_error("RateLimitError", "RATE_LIMIT")
        raise HTTPException(status_code=429, detail="RATE_LIMIT")
    except Exception as e:
        latency = time.time() - start_time
        record_tool_call("discover", latency, False)
        record_error("Exception", str(e))
        logger.error(f"Error in discover: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("TMDB MCP Server")
    print("="*60)
    print("\nServer starting on http://localhost:8000")
    print("\nAvailable endpoints:")
    print("  GET  http://localhost:8000/          - API info")
    print("  GET  http://localhost:8000/health    - Health check")
    print("  GET  http://localhost:8000/docs      - Interactive API docs")
    print("  POST http://localhost:8000/tools/search_title")
    print("  POST http://localhost:8000/tools/get_recommendations")
    print("  POST http://localhost:8000/tools/discover")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

