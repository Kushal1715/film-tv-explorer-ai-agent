#!/bin/bash
# Helper script to run the AI agent with virtual environment activated

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the agent
python -m agent.main

