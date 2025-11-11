"""AI Agent - Command-line chat interface for Film & TV Explorer."""

import os
import sys
import asyncio
import httpx
import json
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default server URL
DEFAULT_SERVER_URL = "http://localhost:8000"

class FilmTVAgent:
    """AI agent that uses Google Gemini to chat with users and call TMDB tools."""
    
    def __init__(self, server_url: str = DEFAULT_SERVER_URL, api_key: Optional[str] = None):
        """Initialize the agent."""
        self.server_url = server_url.rstrip('/')
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Initialize Gemini client (auto-picks up GEMINI_API_KEY from env)
        # If api_key is provided explicitly, set it in environment
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        self.client = genai.Client()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.conversation_history: List[types.Content] = []
        
        # Define tools for Gemini function calling (using dictionary format)
        self.tools = [
            {
                "name": "search_title",
                "description": "Search for movies or TV shows by title. Use this when the user wants to find a specific title or search for titles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query (title name)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of content: 'movie' or 'tv'. Leave null to search both.",
                            "enum": ["movie", "tv"]
                        },
                        "year": {
                            "type": "number",
                            "description": "Release year (optional)"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code like 'en', 'ko' (optional)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_details",
                "description": "Get detailed information about a movie or TV show including full description, genres, ratings, cast, seasons/episodes (for TV), runtime (for movies), etc. Use this when: 1) User says just a NUMBER (like '1', '2') after you show search results - this means they want details IMMEDIATELY for that numbered result, 2) User asks for 'more details', 'description', 'information about', or wants to know more about a specific title. CRITICAL: If user says just a NUMBER (e.g., '1', '2') after search results, IMMEDIATELY call get_details with the ID from that numbered search_title result. If user says just a NUMBER after recommendations, IMMEDIATELY call get_details with the ID from that numbered recommendation result. If user asks for 'more details' WITHOUT mentioning a title name or number, use the ID from the MOST RECENT search_title result that the user confirmed. If user mentions a title by NAME, FIRST call search_title to find that exact title and get its ID, then use that ID here.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "number",
                            "description": "The TMDB ID. CRITICAL: If user says just a NUMBER (like '1', '2') after you show search results, use the ID from that numbered search_title result (e.g., if user says '1', use the ID from the 1st search result). If user says just a NUMBER after recommendations, use the ID from that numbered recommendation result. If user asks for 'more details' without mentioning a title, use the ID from the MOST RECENT search_title result. If user mentions a title by name, FIRST call search_title to get the correct ID, then use that ID here."
                        },
                        "type": {
                            "type": "string",
                            "description": "Type: 'movie' or 'tv' - must match the type from the search_title or recommendation result",
                            "enum": ["movie", "tv"]
                        }
                    },
                    "required": ["id", "type"]
                }
            },
            {
                "name": "get_recommendations",
                "description": "Get movie or TV show recommendations based on a title ID. Use this ONLY when user has a specific title they like and want similar recommendations. Use this IMMEDIATELY when user confirms a title (says 'yes', '1', 'first one', etc.) or asks for recommendations based on a specific title. Extract the 'id' from the most recent search_title results - use the first result's ID if user says 'yes' or '1', second result's ID if user says '2', etc. NEVER ask user for the ID - you have it from search results. If user wants recommendations but doesn't have a specific title, use the 'discover' tool instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "number",
                            "description": "The TMDB ID from the search_title results. Use the ID of the result the user selected (first result if user said 'yes' or '1', second if '2', etc.)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type: 'movie' or 'tv' - use the same type from the search_title result",
                            "enum": ["movie", "tv"]
                        }
                    },
                    "required": ["id", "type"]
                }
            },
            {
                "name": "discover",
                "description": "Discover movies or TV shows with filters like genre, year, language, and sorting. Use this when: 1) User wants recommendations but doesn't have a specific title (e.g., 'give me some recommendations', 'what should I watch?', 'I don't have any title'), 2) User wants to filter or browse by genre, year, etc. When user asks for recommendations without a title, use discover with popular genres and sort by popularity or vote_average to get the best suggestions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Type: 'movie' or 'tv'",
                            "enum": ["movie", "tv"]
                        },
                        "genre": {
                            "type": "array",
                            "description": "List of genre names like ['Action', 'Thriller'] (optional)",
                            "items": {
                                "type": "string"
                            }
                        },
                        "year": {
                            "type": "number",
                            "description": "Release year (optional)"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code like 'en', 'ko' (optional)"
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort by 'popularity' or 'vote_average' (optional)",
                            "enum": ["popularity", "vote_average"]
                        }
                    },
                    "required": ["type"]
                }
            }
        ]
    
    def _format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool result as a readable message when Gemini doesn't provide text."""
        if isinstance(result, dict) and "error" in result:
            return f"I encountered an error: {result.get('message', 'Unknown error')}"
        
        if tool_name == "get_details":
            # Format get_details result
            details = result.get("result", {})
            if not details:
                return "I couldn't retrieve the details for that title."
            
            title = details.get("title", "Unknown")
            overview = details.get("overview", "No overview available")
            genres = details.get("genres", [])
            rating = details.get("rating", 0)
            vote_count = details.get("vote_count", 0)
            
            message = f"**{title}**\n\n"
            message += f"{overview}\n\n"
            
            if genres:
                message += f"**Genres:** {', '.join(genres)}\n"
            if rating > 0:
                message += f"**Rating:** {rating}/10"
                if vote_count > 0:
                    message += f" (based on {vote_count:,} votes)"
                message += "\n"
            
            # Add type-specific details
            if "release_date" in details:
                message += f"**Release Date:** {details.get('release_date')}\n"
            if "runtime" in details:
                message += f"**Runtime:** {details.get('runtime')} minutes\n"
            if "first_air_date" in details:
                message += f"**First Air Date:** {details.get('first_air_date')}\n"
            if "number_of_seasons" in details:
                message += f"**Seasons:** {details.get('number_of_seasons')}\n"
            if "number_of_episodes" in details:
                message += f"**Episodes:** {details.get('number_of_episodes')}\n"
            
            return message
        
        elif tool_name == "search_title":
            results = result.get("results", [])
            if not results:
                return "I couldn't find any titles matching your search."
            
            message = f"I found {len(results)} result(s):\n\n"
            for i, item in enumerate(results[:5], 1):  # Show first 5
                title = item.get("title", "Unknown")
                year = item.get("year", "")
                rating = item.get("rating", 0)
                item_id = item.get("id", "")
                item_type = item.get("type", "")
                message += f"{i}. **{title}**"
                if year:
                    message += f" ({year})"
                if rating > 0:
                    message += f" - Rating: {rating}/10"
                # Include ID in message so Gemini can track it (hidden from user)
                message += f"\n"
            
            # Add explicit ID mapping for context tracking
            if results:
                message += f"\n(Note: Search result #1 has ID {results[0].get('id', 'N/A')} and type '{results[0].get('type', 'N/A')}'"
                if len(results) > 1:
                    message += f", #2 has ID {results[1].get('id', 'N/A')} and type '{results[1].get('type', 'N/A')}'"
                if len(results) > 2:
                    message += f", #3 has ID {results[2].get('id', 'N/A')} and type '{results[2].get('type', 'N/A')}'"
                message += f" - if user selects a number or says 'yes', use the ID and type from that numbered result)"
            
            return message
        
        elif tool_name == "get_recommendations":
            results = result.get("results", [])
            if not results:
                return "I couldn't find any recommendations for that title."
            
            message = f"Here are {len(results)} recommendations:\n\n"
            for i, item in enumerate(results[:10], 1):  # Show first 10
                title = item.get("title", "Unknown")
                year = item.get("year", "")
                rating = item.get("rating", 0)
                reason = item.get("reason", "")
                item_id = item.get("id", "")
                item_type = item.get("type", "")
                message += f"{i}. **{title}**"
                if year:
                    message += f" ({year})"
                if rating > 0:
                    message += f" - Rating: {rating}/10"
                if reason:
                    message += f"\n   {reason}"
                message += "\n"
            
            # Add explicit ID mapping for context tracking
            if results:
                message += f"\n(Note: Recommendation #1 has ID {results[0].get('id', 'N/A')} and type '{results[0].get('type', 'N/A')}'"
                if len(results) > 1:
                    message += f", #2 has ID {results[1].get('id', 'N/A')} and type '{results[1].get('type', 'N/A')}'"
                if len(results) > 2:
                    message += f", #3 has ID {results[2].get('id', 'N/A')} and type '{results[2].get('type', 'N/A')}'"
                message += f" - if user selects a number, use the ID and type from that numbered recommendation)"
            
            return message
        
        elif tool_name == "discover":
            results = result.get("results", [])
            if not results:
                return "I couldn't find any titles matching your criteria."
            
            message = f"I found {len(results)} title(s):\n\n"
            for i, item in enumerate(results[:10], 1):  # Show first 10
                title = item.get("title", "Unknown")
                year = item.get("year", "")
                rating = item.get("rating", 0)
                message += f"{i}. **{title}**"
                if year:
                    message += f" ({year})"
                if rating > 0:
                    message += f" - Rating: {rating}/10"
                message += "\n"
            
            return message
        
        # Default fallback
        return "I've processed your request successfully."
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via HTTP server."""
        endpoint = f"{self.server_url}/tools/{tool_name}"
        
        # Convert arguments to proper types
        processed_args = {}
        for key, value in arguments.items():
            if key == "id" or key == "year":
                processed_args[key] = int(value) if value is not None else None
            else:
                processed_args[key] = value
        
        # Remove None values
        processed_args = {k: v for k, v in processed_args.items() if v is not None}
        
        try:
            response = await self.http_client.post(endpoint, json=processed_args)
            response.raise_for_status()
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError) as e:
                # If response is not valid JSON, return error
                return {"error": "INVALID_RESPONSE", "message": f"Server returned invalid JSON: {str(e)}"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"error": "TITLE_NOT_FOUND", "message": "The requested title was not found."}
            elif e.response.status_code == 429:
                return {"error": "RATE_LIMIT", "message": "Rate limit exceeded. Please try again later."}
            else:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except (ValueError, json.JSONDecodeError, AttributeError):
                    # If we can't parse error response, use status text or error message
                    try:
                        error_detail = e.response.text or str(e)
                    except:
                        error_detail = str(e)
                return {"error": "API_ERROR", "message": f"Error calling tool: {error_detail}"}
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            return {"error": "NETWORK_ERROR", "message": f"Network error: {str(e)}"}
        except Exception as e:
            return {"error": "UNKNOWN_ERROR", "message": f"Unexpected error: {str(e)}"}
    
    async def chat(self, user_message: str) -> str:
        """Process a user message and return agent response."""
        # Build system instruction
        system_instruction = """You are a helpful AI assistant that helps users discover movies and TV shows. 
You have access to tools that can search for titles, get recommendations, and discover content with filters.

When users ask questions:
1. Use search_title to find specific titles - this returns results with 'id', 'title', 'year', 'rating', 'overview' fields
   - ALWAYS remember the IDs from search results in your conversation context
   - When showing search results, mention the titles and remember their IDs
   - Keep track of which title the user originally searched for and its ID
   - When user says a NUMBER (like "1", "2") after you show search results, they are SELECTING that numbered result - remember its ID and type
   - If user then asks for "more details" or "recommendations", use the ID from the result they selected
2. Use get_details when users ask for "more details", "description", or "information about" a title
   - CRITICAL: When user asks for details about a SPECIFIC TITLE BY NAME (e.g., "more details on Prison Break"), you MUST:
     a) First use search_title to find that exact title and get its ID
     b) Match the title name exactly (e.g., if user says "Prison Break", search for "Prison Break" and use the ID from the FIRST result that matches)
     c) Then use get_details with that ID
   - If user asks for details about a title from recommendations you just showed, use the ID from those recommendation results
   - get_details requires: 'id' (number) and 'type' ('movie' or 'tv')
   - ALWAYS search for the title first if user mentions it by name - don't assume you have the correct ID
3. Use get_recommendations when users explicitly ask for similar titles or "what to watch next" AND they have a specific title
   - IMPORTANT: When user selects a number (like "1", "2", etc.) or confirms a title from SEARCH RESULTS, automatically use the 'id' from the search results
   - If user says "1" or "first one" or "yes" to confirm, use the ID from the first search result
   - If user says "2" or "second one", use the ID from the second search result, etc.
   - NEVER ask the user to provide the ID manually - always extract it from the search results
   - Use the 'id' field from the search result the user selected/confirmed
   - REMEMBER: When user says "1" after you show search results, they want the FIRST search result - remember its ID for future requests
4. Use discover when users want recommendations WITHOUT a specific title, or want to filter/browse by genre, year, etc.
   - If user asks for "recommendations" or "what to watch" but doesn't have a specific title, use discover with popular genres
   - If user mentions a genre (e.g., "fantasy", "action", "comedy"), use discover with that genre
   - Sort by popularity or vote_average to get the best recommendations
   - This is perfect for users who want suggestions but don't have a specific title in mind

CRITICAL RULES FOR get_details:
- When user selects a NUMBER from search results (e.g., says "1", "2", "first one", "second one"):
  - This means they want details for that numbered search result IMMEDIATELY
  - ALWAYS use the ID from the MOST RECENT search_title results you showed - never use IDs from older searches or recommendations
  - Call get_details RIGHT AWAY with the ID from that numbered search_title result (e.g., if user says "1", use the ID from the 1st search result from your MOST RECENT search_title call)
  - DO NOT wait for them to ask for "more details" - the number selection IS the request for details
  - Extract the ID from the search result at that position from the MOST RECENT search and call get_details immediately
- When user selects a NUMBER from recommendations (e.g., says "1", "2", "3", "first one", "second one", "third one"):
  - Use the ID from that numbered recommendation result (e.g., if user says "3", use the ID from the 3rd recommendation)
  - The recommendations list has IDs - extract the ID from the result at that position
  - Then call get_details with that ID and the type from that recommendation
- When user asks for "more details" or "more details please" WITHOUT mentioning a title name or number:
  - If user just selected a number from search results (e.g., said "1"), use the ID from that numbered search result
  - If you just showed recommendations, and user asks for "more details", ask which one they want details about
  - If you just showed search results and user said "yes" to confirm, use the ID from the FIRST search result
  - If user just said "yes" to confirm a search result, then asked for "more details", use the ID from that search_title result (the first result if they said "yes")
- When user asks for "more details on [TITLE NAME]" (e.g., "more details on Prison Break"), you MUST:
  1. Call search_title with that exact title name to get the correct ID
  2. Use the FIRST result's ID that matches the title (usually the most popular/relevant one)
  3. Then call get_details with that ID
- IMPORTANT: 
  - When user says "1" after search results, IMMEDIATELY call get_details with the ID from the 1st search result from the MOST RECENT search_title call - don't wait for another message
  - When user says "2" after search results, IMMEDIATELY call get_details with the ID from the 2nd search result from the MOST RECENT search_title call
  - When user selects a number from recommendations, IMMEDIATELY call get_details with the ID from that numbered recommendation result from the MOST RECENT get_recommendations call
  - When user says "yes" to confirm a search result, they mean the FIRST result from the MOST RECENT search - IMMEDIATELY call get_details with that ID
  - NEVER use IDs from older searches or recommendations - always use the MOST RECENT results
- NEVER call get_details without an ID - if you don't have the ID, search for the title first
- get_details provides comprehensive information: full overview, genres, ratings, seasons/episodes, runtime, etc.

CONTEXT AWARENESS:
- When user asks for details about a title by NAME, always search for it first to get the correct ID
- Don't assume you have the correct ID from previous results - search again to be sure
- Match the title name exactly when searching
- Provide helpful descriptions and details from get_details results
- CRITICAL: When user says a NUMBER (like "1", "2") after you show search results, they are REQUESTING DETAILS for that numbered result - call get_details IMMEDIATELY with that ID
- When user says "1" after search results, IMMEDIATELY call get_details with the ID from the 1st search result - don't wait for another message
- Always use the ID from the MOST RECENT search_title or get_recommendations results when user selects a number

RECOMMENDATIONS WITHOUT A TITLE:
- If user asks for "recommendations", "what should I watch", "give me some recommendations" but doesn't have a specific title, use the discover tool
- If user mentions a genre (e.g., "fantasy", "action", "comedy"), use discover with that genre
- If user doesn't specify a genre, you can either:
  a) Ask what genre they prefer, OR
  b) Use discover with a popular genre like "Drama" or "Action" and sort by popularity to give them good recommendations
- Use discover with sort_by="popularity" or sort_by="vote_average" to get the best recommendations
- NEVER insist that the user needs a specific title - you can provide recommendations using discover
- If user says "I don't have any" or "I don't have a title", immediately use discover to find popular titles - don't keep asking for a title

Always provide helpful, friendly responses. Explain why you're recommending something.
Format your responses nicely with clear structure."""
        
        # Configure tools and model
        tools_config = types.Tool(function_declarations=self.tools)
        config = types.GenerateContentConfig(
            tools=[tools_config],
            system_instruction=system_instruction
        )
        
        # Build conversation history (contents list)
        contents = list(self.conversation_history)  # Copy existing history
        
        # Add user message
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )
        contents.append(user_content)
        
        try:
            # Send request to model
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config
            )
            
            # Add user message to history
            self.conversation_history.append(user_content)
            
            # Check if function calls are needed
            assistant_message = None
            function_call_handled = False
            
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        # Check all parts for function calls
                        for part in candidate.content.parts:
                            # Check if this part has a function call
                            if hasattr(part, 'function_call') and part.function_call:
                                function_call = part.function_call
                                function_call_handled = True
                                
                                tool_name = function_call.name
                                arguments = dict(function_call.args) if hasattr(function_call, 'args') else {}
                                
                                # Call the tool
                                result = await self.call_tool(tool_name, arguments)
                                
                                # Check if tool returned an error
                                if isinstance(result, dict) and "error" in result:
                                    error_type = result.get("error", "UNKNOWN_ERROR")
                                    error_message = result.get("message", "An error occurred")
                                    
                                    # Provide user-friendly error messages
                                    if error_type == "TITLE_NOT_FOUND":
                                        assistant_message = f"I couldn't find that title. Please try searching for it first, or check the spelling."
                                    elif error_type == "RATE_LIMIT":
                                        assistant_message = "The API rate limit has been exceeded. Please wait a moment and try again."
                                    elif error_type == "NETWORK_ERROR":
                                        assistant_message = "I'm having trouble connecting to the server. Please make sure the MCP server is running."
                                    else:
                                        assistant_message = f"I encountered an error: {error_message}. Please try again or rephrase your question."
                                    
                                    break  # Exit function call handling
                                
                                # Create function response part
                                function_response_part = types.Part.from_function_response(
                                    name=tool_name,
                                    response=result
                                )
                                
                                # Append model's response (with function call) to contents
                                contents.append(candidate.content)
                                
                                # Append function response
                                contents.append(types.Content(
                                    role="user",
                                    parts=[function_response_part]
                                ))
                                
                                # Get final response with function result
                                final_response = self.client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=contents,
                                    config=config
                                )
                                
                                # Extract text from final response
                                if final_response.text:
                                    assistant_message = final_response.text
                                elif final_response.candidates and len(final_response.candidates) > 0:
                                    final_candidate = final_response.candidates[0]
                                    if final_candidate.content and final_candidate.content.parts:
                                        text_parts = []
                                        for p in final_candidate.content.parts:
                                            if hasattr(p, 'text') and p.text:
                                                # Skip function calls
                                                if not (hasattr(p, 'function_call') and p.function_call):
                                                    text_parts.append(p.text)
                                        if text_parts:
                                            assistant_message = ' '.join(text_parts)
                                
                                # If no text was extracted, format the tool result as fallback
                                if not assistant_message or assistant_message.strip() == "":
                                    assistant_message = self._format_tool_result(tool_name, result)
                                
                                # Add model's final response to history
                                if final_response.candidates and len(final_response.candidates) > 0:
                                    self.conversation_history.append(final_response.candidates[0].content)
                                
                                break  # Handle first function call only for now
            except Exception as e:
                # Error checking for function calls, try to extract text normally
                pass
            
            # If no function calls found or assistant_message not set, extract text normally
            if not assistant_message:
                try:
                    if response.text:
                        assistant_message = response.text
                    elif response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if candidate.content and candidate.content.parts:
                            text_parts = []
                            for part in candidate.content.parts:
                                # Only extract text, skip function calls
                                if hasattr(part, 'text') and part.text:
                                    # Double check it's not a function call
                                    if not (hasattr(part, 'function_call') and part.function_call):
                                        text_parts.append(part.text)
                            assistant_message = ' '.join(text_parts) if text_parts else "I'm here to help you discover movies and TV shows!"
                        else:
                            assistant_message = "I'm here to help you discover movies and TV shows!"
                    else:
                        assistant_message = "I'm here to help you discover movies and TV shows!"
                except Exception as e:
                    # If all else fails, provide a helpful message
                    assistant_message = "I'm here to help you discover movies and TV shows!"
            
            # Add assistant response to history (if not already added from function call)
            if not function_call_handled:
                if response.candidates and len(response.candidates) > 0:
                    self.conversation_history.append(response.candidates[0].content)
            
            return assistant_message
                
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            # Add error message to history
            error_content = types.Content(
                role="model",
                parts=[types.Part(text=error_msg)]
            )
            self.conversation_history.append(error_content)
            return error_msg
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history: List[types.Content] = []


async def main():
    """Main entry point for command-line interface."""
    print("\n" + "="*60)
    print("🎬 Film & TV Explorer - AI Agent (Powered by Gemini)")
    print("="*60)
    print("\nI can help you discover movies and TV shows!")
    print("Ask me questions like:")
    print("  - 'Find Inception'")
    print("  - 'What should I watch if I loved Breaking Bad?'")
    print("  - 'Show me Action movies from 2020'")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("Type 'clear' to reset the conversation history.")
    print("="*60 + "\n")
    
    # Check if server is running
    server_url = os.getenv("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    agent = FilmTVAgent(server_url=server_url)
    
    try:
        # Test server connection
        async with httpx.AsyncClient() as test_client:
            try:
                response = await test_client.get(f"{server_url}/health", timeout=5.0)
                if response.status_code == 200:
                    print("✅ Connected to MCP server\n")
                else:
                    print("⚠️  Warning: Server health check failed\n")
            except Exception as e:
                print(f"❌ Error: Cannot connect to MCP server at {server_url}")
                print(f"   Make sure the server is running: python -m mcp_server.http_server\n")
                sys.exit(1)
        
        # Chat loop
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Happy watching!\n")
                    break
                
                if user_input.lower() in ['clear', 'reset']:
                    agent.reset_conversation()
                    print("🔄 Conversation history cleared.\n")
                    continue
                
                # Get agent response
                print("\nAgent: ", end="", flush=True)
                response = await agent.chat(user_input)
                print(response)
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Happy watching!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye! Happy watching!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                import traceback
                traceback.print_exc()
    
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
