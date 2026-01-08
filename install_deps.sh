#!/bin/bash
# Install all backend dependencies

echo "Installing backend dependencies..."
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install the package in editable mode with all dependencies
echo "Installing sputnik package with dependencies..."
pip install -e .

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "You can now start the backend with:"
echo "  python scripts/start_server.py"
echo "  or"
echo "  make backend"
