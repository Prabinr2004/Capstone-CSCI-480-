#!/bin/bash
# Simple script to run the Color Blender app

echo "🎨 Color Blender App Launcher"
echo "==============================="

# Kill any existing Flask processes
echo "Cleaning up old processes..."
pkill -9 -f "python app.py" 2>/dev/null
pkill -9 -f "flask" 2>/dev/null
sleep 2

# Find an available port starting from 3000
PORT=3000
while lsof -i :$PORT >/dev/null 2>&1; do
    PORT=$((PORT + 1))
done

echo "✅ Starting app on port $PORT..."
echo "📱 Access from your computer: http://localhost:$PORT"
echo "🌐 Access from your network: http://10.25.9.184:$PORT"
echo ""
echo "Press CTRL+C to stop the app"
echo ""

# Run the app
PORT=$PORT ./.venv/bin/python app.py
