#!/bin/bash

# Enhanced Knowledge Base Agent - UI Startup Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Enhanced Knowledge Base Agent - Web UI                       ║"
echo "║   Starting Server...                                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory (project root)
cd "$SCRIPT_DIR"

# Determine the port (default to 5000)
PORT=${1:-5000}
HOST="127.0.0.1"

echo ""
echo "🚀 Starting Enhanced Knowledge Base Agent Web Server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""
echo "� Accesis the UI at: http://localhost:$PORT"
echo "📚 API Documentation: http://localhost:$PORT/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server using python -m to ensure proper module resolution
python3 -m enhanced_kb_agent.web.server --host $HOST --port $PORT --debug

