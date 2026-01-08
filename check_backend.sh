#!/bin/bash
# Quick script to check if backend is running

echo "Checking backend status..."
echo ""

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Port 8000 is in use (backend likely running)"
else
    echo "❌ Port 8000 is NOT in use (backend not running)"
    echo ""
    echo "Start the backend with:"
    echo "  python scripts/start_server.py"
    echo "  or"
    echo "  make backend"
    exit 1
fi

# Try to reach the health endpoint
echo ""
echo "Testing backend health endpoint..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "   Response: $HEALTH"
else
    echo "❌ Backend health check failed"
    echo "   Make sure the backend is running on http://localhost:8000"
    exit 1
fi

# Try to reach the models endpoint
echo ""
echo "Testing models endpoint..."
if curl -s http://localhost:8000/api/v1/models > /dev/null 2>&1; then
    echo "✅ Models endpoint is accessible"
    MODELS_COUNT=$(curl -s http://localhost:8000/api/v1/models | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('models', [])))" 2>/dev/null || echo "unknown")
    echo "   Found $MODELS_COUNT models"
else
    echo "❌ Models endpoint failed"
    echo "   Check backend logs for errors"
    exit 1
fi

echo ""
echo "✅ Backend is running and accessible!"
