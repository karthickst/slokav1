#!/bin/bash
# Run script for Spiritual Course Management System

echo "🕉️  Starting Spiritual Course Management System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Using default test configuration."
fi

# Set default mode to test if not specified
export APP_MODE=${APP_MODE:-test}

echo "Running in mode: $APP_MODE"
echo "Starting server on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Run the application
python app.py
