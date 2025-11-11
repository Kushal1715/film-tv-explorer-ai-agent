# Step 5 Complete: AI Agent

## What Was Created

**File**: `agent/main.py`

This file contains the `FilmTVAgent` class - an intelligent chat agent that uses Google Gemini to understand user queries and call the MCP tools via HTTP.

---

## Key Features

### 1. **Google Gemini Integration**

Uses Google's Gemini API with function calling:
- Model: `gemini-2.0-flash` (free tier, fast, and powerful)
- Tool calling: Automatically decides which tools to use
- Conversation history: Maintains context across messages
- Function declarations: Uses Gemini's function calling protocol

### 2. **Tool Integration**

The agent has access to four tools:

#### `search_title`
- Searches for movies/TV shows
- Used when user wants to find specific titles

#### `get_details`
- Gets detailed information about a movie or TV show
- Used when user asks for "more details", "description", or "information about" a title
- Provides comprehensive information: overview, genres, ratings, seasons/episodes, runtime, etc.

#### `get_recommendations`
- Gets recommendations based on a title ID
- Used when user asks "what to watch next" or "similar to X"
- Automatically extracts ID from search results

#### `discover`
- Discovers content with filters (genre, year, language)
- Used when user wants to browse or filter

### 3. **HTTP Client Integration**

Calls the MCP server endpoints:
- `POST /tools/search_title`
- `POST /tools/get_details`
- `POST /tools/get_recommendations`
- `POST /tools/discover`

Handles errors gracefully:
- `404`: TITLE_NOT_FOUND
- `429`: RATE_LIMIT
- Network errors (timeouts, connection errors)
- Invalid JSON responses
- API errors with detailed error messages

### 4. **Command-Line Interface**

Interactive chat interface:
- Prompts user for input
- Displays agent responses
- Maintains conversation history
- Commands: `quit`, `exit`, `clear`

---

## How It Works

```
User types message
    ↓
Agent receives message
    ↓
Gemini analyzes intent
    ↓
Gemini decides which tools to call (if any)
    ↓
Agent calls MCP server endpoints
    ↓
Tool results returned to Gemini
    ↓
Gemini synthesizes final response
    ↓
Agent extracts text from response (handles function calls safely)
    ↓
Agent displays response to user
```

**Key Implementation Details:**
- Robust error handling for function call extraction
- Safe text extraction that skips function call parts
- Handles multiple response formats from Gemini API
- Graceful fallbacks if text extraction fails

---

## Example Conversation

### User:
> "If I loved Inception, what should I watch next?"

### Agent's Process:

1. **Gemini analyzes**: User wants recommendations based on "Inception"
2. **Tool call 1**: `search_title(query="Inception", type="movie")`
   - Returns: `[{"id": 27205, "title": "Inception", ...}]`
3. **Tool call 2**: `get_recommendations(id=27205, type="movie")`
   - Returns: `[{"id": 11324, "title": "Shutter Island", "reason": "..."}, ...]`
4. **Gemini synthesizes**: Creates a friendly response explaining the recommendations

### Agent Response:
> "Since you loved Inception, here are some great recommendations:
> 
> 1. **Shutter Island (2010)** - Similar to Inception (shared Action, Thriller genres, highly rated). Psychological thriller with a twist ending.
> 
> 2. **The Dark Knight (2008)** - Another Christopher Nolan film with complex narrative and action.
> 
> ..."

---

## Code Structure

```python
class FilmTVAgent:
    def __init__(self, server_url, api_key):
        # Configure Gemini API
        # Initialize HTTP client
        # Define function declarations for Gemini
        # Initialize conversation history
    
    async def call_tool(self, tool_name, arguments):
        # Call MCP server endpoint
        # Handle errors (404, 429, network, JSON parsing)
        # Return results or error dict
    
    async def chat(self, user_message):
        # Create Gemini model with tools
        # Build chat history from conversation
        # Send message to Gemini
        # Check for function calls in response
        # Execute function calls if needed
        # Extract text from response (safely handle function calls)
        # Add to conversation history
        # Return to user
```

---

## Running the Agent

### Prerequisites

1. **MCP Server must be running**:
   ```bash
   python -m mcp_server.http_server
   ```

2. **Environment variables set**:
   - `GEMINI_API_KEY` - Required (get free API key from Google AI Studio)
   - `TMDB_API_KEY` - Required (for server)

### Start the Agent

```bash
# Activate virtual environment
source venv/bin/activate

# Run the agent
python -m agent.main
```

Or use the helper script:
```bash
chmod +x run_agent.sh
./run_agent.sh
```

### Example Session

```
============================================================
🎬 Film & TV Explorer - AI Agent (Powered by Gemini)
============================================================

I can help you discover movies and TV shows!
Ask me questions like:
  - 'Find Inception'
  - 'What should I watch if I loved Breaking Bad?'
  - 'Show me Action movies from 2020'

Type 'quit' or 'exit' to end the conversation.
Type 'clear' to reset the conversation history.
============================================================

✅ Connected to MCP server

You: Find Inception

Agent: I found "Inception" (2010), a science fiction action film directed by Christopher Nolan...

You: What should I watch next?

Agent: Based on Inception, here are some recommendations...
```

---

## Features

### ✅ Natural Language Understanding
- Understands questions in plain English
- Handles variations: "find", "search", "show me"
- Interprets intent correctly

### ✅ Autonomous Tool Selection
- Decides which tools to use automatically
- Can chain multiple tools (search → recommendations)
- Handles complex queries

### ✅ Context Awareness
- Maintains conversation history
- Remembers previous messages
- Can reference earlier parts of conversation

### ✅ Error Handling
- Handles API errors gracefully (404, 429, network errors)
- Safe text extraction from Gemini responses
- Handles function call conversion errors
- Provides helpful error messages
- Continues conversation after errors
- Robust JSON parsing with fallbacks

### ✅ User-Friendly Interface
- Clear prompts and instructions
- Formatted responses
- Easy to use commands

---

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required - Your Google Gemini API key (free tier available)
- `MCP_SERVER_URL`: Optional - Default: `http://localhost:8000`

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### Customization

You can modify:
- **Model**: Change `gemini-2.0-flash` to other Gemini models (e.g., `gemini-pro`, `gemini-1.5-pro`)
- **System prompt**: Modify the system instruction in `chat()` method
- **Function declarations**: Update tool descriptions for better tool selection
- **Error handling**: Customize error messages and fallback behavior

---

## Testing

### Manual Testing

1. Start the MCP server
2. Start the agent
3. Try various queries:
   - Simple search: "Find The Matrix"
   - Recommendations: "What's similar to Breaking Bad?"
   - Discovery: "Show me Action movies from 2020"
   - Complex: "If I loved Inception, what should I watch next?"

### Expected Behavior

- ✅ Agent understands queries
- ✅ Calls appropriate tools
- ✅ Returns helpful responses
- ✅ Handles errors gracefully
- ✅ Maintains conversation context

---

## What's Next?

**Step 6**: Add Streamlit Frontend
- Web-based chat interface
- Beautiful UI with movie posters
- Accessible in browser
- No command-line needed

---

## Summary

✅ **Created**: `agent/main.py`
- Google Gemini-powered chat agent
- Function calling integration (4 tools: search_title, get_details, get_recommendations, discover)
- Command-line interface
- Conversation history management
- Robust error handling (API errors, network errors, text extraction)
- Safe function call handling
- Free tier support (Gemini API)

✅ **Key Improvements**:
- Migrated from OpenAI to Google Gemini (free tier available)
- Added `get_details` tool for comprehensive title information
- Enhanced error handling for all edge cases
- Improved text extraction that safely handles function calls
- Better context awareness and tool selection

✅ **Ready for**: 
- Production use (command-line)
- Frontend integration (Step 6)

**The agent is now fully functional and ready to help users discover movies and TV shows!**

