"""Streamlit web frontend for Film & TV Explorer AI Agent."""

import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from agent.main import FilmTVAgent
import httpx

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Film & TV Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    .agent-message {
        background-color: #f5f5f5;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "server_status" not in st.session_state:
    st.session_state.server_status = None

# Helper function to run async code in Streamlit
def run_async(coro):
    """Run async coroutine in Streamlit, handling event loop properly."""
    # Streamlit runs in different threads, so we need to create a fresh loop each time
    # Use asyncio.run() which properly handles this
    try:
        # Check if there's already a running loop (shouldn't happen in Streamlit, but just in case)
        try:
            asyncio.get_running_loop()
            # If we get here, there's a running loop - this shouldn't happen in Streamlit
            # But if it does, we need to use nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass
        except RuntimeError:
            # No running loop - this is the normal case in Streamlit
            pass
        
        # Use asyncio.run() which creates a fresh event loop
        return asyncio.run(coro)
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # Loop was closed, try again with a fresh one
            return asyncio.run(coro)
        raise

# Check server connection
async def check_server():
    """Check if MCP server is running."""
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{server_url}/health")
            if response.status_code == 200:
                return True, "Connected"
            else:
                return False, "Server returned error"
    except Exception as e:
        return False, f"Cannot connect: {str(e)}"

# Initialize agent
def init_agent():
    """Initialize the AI agent."""
    try:
        server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        # Always create a fresh agent to avoid event loop issues
        # Close old agent if it exists
        if st.session_state.agent is not None:
            try:
                # Try to close the old agent's HTTP client
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(st.session_state.agent.close())
                loop.close()
            except:
                pass  # Ignore errors when closing
        
        # Create new agent
        st.session_state.agent = FilmTVAgent(server_url=server_url)
        return True
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return False

# Main UI
def main():
    # Auto-initialize agent on first load
    if st.session_state.agent is None:
        try:
            init_agent()
        except Exception as e:
            # Agent initialization failed, but continue - user can retry
            pass
    
    # Header
    st.markdown('<h1 class="main-header">🎬 Film & TV Explorer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Powered by Google Gemini AI</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Server status check
        st.subheader("Server Status")
        if st.button("Check Server Connection"):
            with st.spinner("Checking server..."):
                try:
                    is_connected, message = run_async(check_server())
                    
                    if is_connected:
                        st.success("✅ " + message)
                        st.session_state.server_status = "connected"
                    else:
                        st.error("❌ " + message)
                        st.session_state.server_status = "disconnected"
                        st.info("💡 Make sure the MCP server is running:\n```bash\npython -m mcp_server.http_server\n```")
                except Exception as e:
                    st.error(f"❌ Error checking server: {str(e)}")
                    st.session_state.server_status = "disconnected"
        
        if st.session_state.server_status:
            if st.session_state.server_status == "connected":
                st.success("✅ Server Connected")
            else:
                st.error("❌ Server Disconnected")
        
        st.divider()
        
        # Agent status
        st.subheader("Agent Status")
        if st.session_state.agent:
            st.success("✅ Agent Ready")
            # Allow re-initialization if needed
            if st.button("🔄 Re-initialize Agent"):
                with st.spinner("Re-initializing agent..."):
                    if init_agent():
                        st.success("✅ Agent re-initialized!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to re-initialize agent")
        else:
            st.warning("⚠️ Agent not initialized")
            if st.button("Initialize Agent"):
                with st.spinner("Initializing agent..."):
                    if init_agent():
                        st.success("✅ Agent initialized!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to initialize agent")
        
        st.divider()
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            if st.session_state.agent:
                st.session_state.agent.reset_conversation()
            st.rerun()
        
        st.divider()
        
        # Instructions
        st.subheader("💡 How to Use")
        st.markdown("""
        1. Make sure the MCP server is running
        2. The agent initializes automatically when you open the app
        3. Type your questions in the chat
        4. Ask about movies/TV shows!
        
        **Example questions:**
        - "Find Inception"
        - "What should I watch if I loved Breaking Bad?"
        - "Show me Action movies from 2020"
        - "What are the top Korean thrillers?"
        
        **Note:** If the agent fails to initialize, check that your `GEMINI_API_KEY` is set in your `.env` file.
        """)
    
    # Main chat interface
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about movies or TV shows..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        if st.session_state.agent is None:
            with st.chat_message("assistant"):
                error_msg = "⚠️ Agent not initialized. Please check that your GEMINI_API_KEY is set in your .env file and try refreshing the page."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
        else:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Ensure agent's HTTP client is ready for new event loop
                        # Recreate HTTP client if needed
                        if hasattr(st.session_state.agent, 'http_client'):
                            try:
                                # Close old client
                                old_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(old_loop)
                                old_loop.run_until_complete(st.session_state.agent.http_client.aclose())
                                old_loop.close()
                            except:
                                pass
                            # Create new client
                            st.session_state.agent.http_client = httpx.AsyncClient(timeout=30.0)
                        
                        # Run async agent chat using helper function
                        response = run_async(st.session_state.agent.chat(prompt))
                        
                        # Display response
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        import traceback
                        st.code(traceback.format_exc())
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "Film & TV Explorer | Powered by Google Gemini AI | TMDB API"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

