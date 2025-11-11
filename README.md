# Film & TV Explorer - AI Agent with MCP

An intelligent chat agent that helps users discover movies and TV shows using the TMDB API, wrapped in an MCP server.

## Project Structure

```
.
├── agent/              # LLM-based chat agent
├── mcp-server/         # MCP server wrapping TMDB API
├── tests/              # Unit and integration tests
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export TMDB_API_KEY="your_tmdb_api_key_here"
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```
   
   **Get Gemini API Key (FREE)**:
   - Visit https://aistudio.google.com/
   - Sign in with Google account
   - Click "Get API Key" → "Create API Key"
   - Copy and add to `.env` file
   - See `GEMINI_SETUP.md` for detailed instructions

3. **Get TMDB API key**:
   - Sign up at https://www.themoviedb.org/
   - Go to Settings > API
   - Request an API key

## Status

✅ **Step 1**: Project Setup - Complete  
✅ **Step 2**: TMDB API Client - Complete  
✅ **Step 3**: MCP Tools - Complete  
✅ **Step 4**: HTTP Server - Complete  
✅ **Step 5**: AI Agent - Complete  
✅ **Step 6**: Streamlit Web Frontend - Complete

## Quick Start

### 1. Install Dependencies

```bash
cd /home/Kushal7/Desktop/AI-agent
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file or export:
```bash
export TMDB_API_KEY="your_tmdb_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
```

**Get Gemini API Key (FREE)**:
- Visit https://aistudio.google.com/
- Sign in with Google account
- Click "Get API Key" → "Create API Key"
- Copy and add to `.env` file
- See `GEMINI_SETUP.md` for detailed instructions

### 3. Start the MCP Server

In one terminal:
```bash
source venv/bin/activate
python -m mcp_server.http_server
```

The server will start on `http://localhost:8000`

### 4. Run the Agent

**Option A: Command-Line Interface**

In another terminal:
```bash
source venv/bin/activate
python -m agent.main
```

Or use the helper script:
```bash
chmod +x run_agent.sh
./run_agent.sh
```

**Option B: Web Frontend (Recommended)**

In another terminal:
```bash
source venv/bin/activate
./run_streamlit.sh
```

Or directly:
```bash
streamlit run streamlit_app.py
```

The web interface will open at `http://localhost:8501`

## Usage

### Command-Line Interface

Once the agent is running, you can ask questions like:
- "Find Inception"
- "What should I watch if I loved Breaking Bad?"
- "Show me Action movies from 2020"
- "What are the top Korean thrillers?"

Type `quit` or `exit` to end the conversation.

### Web Frontend

1. Open `http://localhost:8501` in your browser
2. Click "Check Server Connection" in the sidebar
3. Click "Initialize Agent" in the sidebar
4. Start chatting! Ask questions about movies and TV shows

The web interface provides:
- Beautiful chat UI
- Message history
- Server status monitoring
- Easy-to-use controls

