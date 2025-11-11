#!/bin/bash

# Run Streamlit frontend for Film & TV Explorer

echo "============================================================"
echo "🎬 Film & TV Explorer - Streamlit Frontend"
echo "============================================================"
echo ""
echo "Starting Streamlit app..."
echo ""
echo "The app will open in your browser at:"
echo "  http://localhost:8501"
echo ""
echo "Make sure the MCP server is running in another terminal:"
echo "  python -m mcp_server.http_server"
echo ""
echo "============================================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Streamlit
streamlit run streamlit_app.py

