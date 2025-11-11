"""MCP tool implementations for TMDB API."""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

from .api_client import TMDBClient, RateLimitError

logger = logging.getLogger(__name__)

class SearchTitleArgs(BaseModel):
    """Arguments for search_title tool."""
    query: str = Field(..., description="Search query")
    type: Optional[str] = Field(None, description="Type: 'movie' or 'tv'")
    year: Optional[int] = Field(None, description="Release year")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'ko')")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v and v not in ["movie", "tv"]:
            raise ValueError("type must be 'movie' or 'tv'")
        return v

class GetRecommendationsArgs(BaseModel):
    """Arguments for get_recommendations tool."""
    id: int = Field(..., description="TMDB ID of the title")
    type: str = Field(..., description="Type: 'movie' or 'tv'")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["movie", "tv"]:
            raise ValueError("type must be 'movie' or 'tv'")
        return v

class GetDetailsArgs(BaseModel):
    """Arguments for get_details tool."""
    id: int = Field(..., description="TMDB ID of the title")
    type: str = Field(..., description="Type: 'movie' or 'tv'")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["movie", "tv"]:
            raise ValueError("type must be 'movie' or 'tv'")
        return v

class DiscoverArgs(BaseModel):
    """Arguments for discover tool."""
    type: str = Field(..., description="Type: 'movie' or 'tv'")
    genre: Optional[List[str]] = Field(None, description="List of genre names")
    year: Optional[int] = Field(None, description="Release year")
    language: Optional[str] = Field(None, description="Language code")
    sort_by: Optional[str] = Field(None, description="Sort by: 'popularity' or 'vote_average'")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["movie", "tv"]:
            raise ValueError("type must be 'movie' or 'tv'")
        return v
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v):
        if v and v not in ["popularity", "vote_average"]:
            raise ValueError("sort_by must be 'popularity' or 'vote_average'")
        return v

def format_title_result(result: Dict[str, Any], type: str) -> Dict[str, Any]:
    """Format a title result from TMDB API according to MCP spec."""
    release_date = result.get("release_date") or result.get("first_air_date", "")
    year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
    
    return {
        "id": result["id"],
        "title": result.get("title") or result.get("name", "Unknown"),
        "type": type,
        "year": year,
        "rating": result.get("vote_average", 0.0),
        "overview": result.get("overview", ""),
        "poster_path": result.get("poster_path")
    }

async def search_title(client: TMDBClient, args: SearchTitleArgs) -> List[Dict[str, Any]]:
    """Search for movies or TV shows."""
    logger.info(f"Searching for: {args.query} (type={args.type}, year={args.year}, lang={args.language})")
    
    try:
        results = await client.search_title(
            query=args.query,
            type=args.type,
            year=args.year,
            language=args.language
        )
        
        type_str = args.type or "movie"
        formatted = [format_title_result(r, type_str) for r in results[:10]]  # Limit to 10
        
        logger.info(f"Found {len(formatted)} results")
        return formatted
        
    except ValueError as e:
        if str(e) == "TITLE_NOT_FOUND":
            raise
        raise ValueError(f"Invalid arguments: {e}")
    except RateLimitError:
        raise
    except Exception as e:
        logger.error(f"Error in search_title: {e}")
        raise ValueError(f"API error: {e}")

async def get_recommendations(client: TMDBClient, args: GetRecommendationsArgs) -> List[Dict[str, Any]]:
    """Get recommendations for a movie or TV show."""
    logger.info(f"Getting recommendations for {args.type} {args.id}")
    
    try:
        # First get the original title details for context
        details = await client.get_details(args.id, args.type)
        original_title = details.get("title") or details.get("name", "Unknown")
        original_genres = [g["name"] for g in details.get("genres", [])]
        
        # Get recommendations
        results = await client.get_recommendations(args.id, args.type)
        
        formatted = []
        for r in results[:10]:  # Limit to 10
            release_date = r.get("release_date") or r.get("first_air_date", "")
            year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            # Generate reason based on metadata
            reason_parts = []
            # Get genre names from genre_ids
            r_genre_ids = r.get("genre_ids", [])
            # We'll match by IDs since we have the original genres as objects
            original_genre_ids = [g["id"] for g in details.get("genres", [])]
            common_genre_ids = set(original_genre_ids) & set(r_genre_ids)
            if common_genre_ids:
                common_genre_names = [g["name"] for g in details.get("genres", []) if g["id"] in common_genre_ids]
                if common_genre_names:
                    reason_parts.append(f"shared {', '.join(common_genre_names[:2])} genres")
            
            if r.get("vote_average", 0) >= 7.5:
                reason_parts.append("highly rated")
            
            reason = f"Similar to {original_title}" + (f" ({', '.join(reason_parts)})" if reason_parts else "")
            
            formatted.append({
                "id": r["id"],
                "title": r.get("title") or r.get("name", "Unknown"),
                "year": year,
                "reason": reason
            })
        
        logger.info(f"Found {len(formatted)} recommendations")
        return formatted
        
    except ValueError as e:
        if str(e) == "TITLE_NOT_FOUND":
            raise
        raise ValueError(f"Invalid arguments: {e}")
    except RateLimitError:
        raise
    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}")
        raise ValueError(f"API error: {e}")

async def discover(client: TMDBClient, args: DiscoverArgs) -> List[Dict[str, Any]]:
    """Discover movies or TV shows with filters."""
    logger.info(f"Discovering {args.type} (genre={args.genre}, year={args.year}, lang={args.language}, sort={args.sort_by})")
    
    try:
        results = await client.discover(
            type=args.type,
            genre=args.genre,
            year=args.year,
            language=args.language,
            sort_by=args.sort_by
        )
        
        formatted = [format_title_result(r, args.type) for r in results[:20]]  # Limit to 20
        
        logger.info(f"Found {len(formatted)} results")
        return formatted
        
    except ValueError as e:
        raise ValueError(f"Invalid arguments: {e}")
    except RateLimitError:
        raise
    except Exception as e:
        logger.error(f"Error in discover: {e}")
        raise ValueError(f"API error: {e}")

async def get_details(client: TMDBClient, args: GetDetailsArgs) -> Dict[str, Any]:
    """Get detailed information about a movie or TV show."""
    logger.info(f"Getting details for {args.type} {args.id}")
    
    try:
        details = await client.get_details(args.id, args.type)
        
        # Format the response with key information
        formatted = {
            "id": details.get("id"),
            "title": details.get("title") or details.get("name", "Unknown"),
            "overview": details.get("overview", "No overview available"),
            "genres": [g["name"] for g in details.get("genres", [])],
            "rating": details.get("vote_average", 0),
            "vote_count": details.get("vote_count", 0),
            "tagline": details.get("tagline"),
            "status": details.get("status"),
        }
        
        # Add type-specific fields
        if args.type == "movie":
            formatted["release_date"] = details.get("release_date")
            formatted["runtime"] = details.get("runtime")
            formatted["budget"] = details.get("budget")
            formatted["revenue"] = details.get("revenue")
        else:  # TV
            formatted["first_air_date"] = details.get("first_air_date")
            formatted["last_air_date"] = details.get("last_air_date")
            formatted["number_of_seasons"] = details.get("number_of_seasons")
            formatted["number_of_episodes"] = details.get("number_of_episodes")
            formatted["created_by"] = [c["name"] for c in details.get("created_by", [])]
            formatted["networks"] = [n["name"] for n in details.get("networks", [])]
        
        logger.info(f"Retrieved details for {formatted['title']}")
        return formatted
        
    except ValueError as e:
        if str(e) == "TITLE_NOT_FOUND":
            raise
        raise ValueError(f"Invalid arguments: {e}")
    except RateLimitError:
        raise
    except Exception as e:
        logger.error(f"Error in get_details: {e}")
        raise ValueError(f"API error: {e}")

