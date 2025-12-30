#!/bin/bash
# Stop script for Spiritual Course Management System

echo "🕉️  Stopping Spiritual Course Management System..."
echo "=============================================="
echo ""

# Find Python processes running app.py
PIDS=$(ps aux | grep "[p]ython.*app.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No application processes found running."
    echo ""

    # Also check for uvicorn processes
    UVICORN_PIDS=$(ps aux | grep "[u]vicorn" | awk '{print $2}')

    if [ -z "$UVICORN_PIDS" ]; then
        echo "✓ Application is not running."
    else
        echo "Found uvicorn processes: $UVICORN_PIDS"
        echo "Stopping uvicorn processes..."
        echo "$UVICORN_PIDS" | xargs kill -TERM 2>/dev/null
        sleep 2

        # Force kill if still running
        REMAINING=$(ps aux | grep "[u]vicorn" | awk '{print $2}')
        if [ ! -z "$REMAINING" ]; then
            echo "Force killing remaining processes..."
            echo "$REMAINING" | xargs kill -9 2>/dev/null
        fi

        echo "✓ All uvicorn processes stopped."
    fi
else
    echo "Found application processes: $PIDS"
    echo "Sending TERM signal to gracefully stop..."
    echo ""

    # Send TERM signal for graceful shutdown
    echo "$PIDS" | xargs kill -TERM 2>/dev/null

    # Wait a few seconds
    sleep 3

    # Check if processes are still running
    REMAINING=$(ps aux | grep "[p]ython.*app.py" | awk '{print $2}')

    if [ ! -z "$REMAINING" ]; then
        echo "Some processes still running. Force killing..."
        echo "$REMAINING" | xargs kill -9 2>/dev/null
        sleep 1
    fi

    # Final check
    FINAL_CHECK=$(ps aux | grep "[p]ython.*app.py" | awk '{print $2}')

    if [ -z "$FINAL_CHECK" ]; then
        echo "✓ Application stopped successfully."
    else
        echo "⚠️  Some processes may still be running."
        echo "   PIDs: $FINAL_CHECK"
    fi
fi

# Also check for any process using port 8000
echo ""
echo "Checking port 8000..."
PORT_PID=$(lsof -ti:8000 2>/dev/null)

if [ ! -z "$PORT_PID" ]; then
    echo "Found process on port 8000 (PID: $PORT_PID)"
    echo "Stopping process on port 8000..."
    kill -TERM $PORT_PID 2>/dev/null
    sleep 2

    # Force kill if needed
    PORT_PID_CHECK=$(lsof -ti:8000 2>/dev/null)
    if [ ! -z "$PORT_PID_CHECK" ]; then
        kill -9 $PORT_PID_CHECK 2>/dev/null
    fi
    echo "✓ Port 8000 is now free."
else
    echo "✓ Port 8000 is free."
fi

echo ""
echo "=============================================="
echo "🕉️  Shutdown complete."
echo "=============================================="
