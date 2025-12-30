#!/bin/bash
# Test runner script for Spiritual Course Management System

echo "🕉️  Running Test Suite"
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Ensure test mode
export APP_MODE=test

# Run tests
pytest test_app.py -v -s

echo ""
echo "=============================================="
echo "Tests completed!"
