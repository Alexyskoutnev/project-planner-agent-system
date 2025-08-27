#!/bin/bash

# Production environment setup script
set -e  # Exit on any error

echo "🚀 Setting up Project Planner for Production..."

# Check if we're in the right directory
if [ ! -f "api/main.py" ]; then
    echo "❌ api/main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOL
OPENAI_API_KEY=your_openai_api_key_here
NODE_ENV=production
REACT_APP_API_URL=/api
EOL
    echo "🔧 Please edit .env and add your OpenAI API key"
fi

# Build frontend for production
echo "📦 Building React frontend for production..."
cd frontend

# Set production environment variables
export NODE_ENV=production
export REACT_APP_API_URL=/api

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Build the frontend
npm run build

cd ..

echo "🔧 Starting FastAPI backend for production..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install Python dependencies if needed
if ! python3 -c "import fastapi, uvicorn, sqlmodel" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Start the backend server
echo "🚀 Starting server on http://localhost:8000"
echo "🌐 Frontend build is available in frontend/build/"
echo "📝 Configure your web server (nginx) to:"
echo "   - Serve frontend/build/ for web requests"
echo "   - Proxy /api requests to http://localhost:8000"
echo ""
echo "🛑 Press Ctrl+C to stop the backend service"

python3 api/main.py