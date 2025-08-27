#!/bin/bash

set -e 

echo "🚀 Starting Project Planner in Development Mode..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOL
OPENAI_API_KEY=your_openai_api_key_here
REACT_APP_API_URL=http://localhost:8000
EOL
    echo "🔧 Please edit .env and add your OpenAI API key"
    echo "📝 The frontend is configured to use http://localhost:8000 for API calls"
fi

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
if ! python3 -c "import fastapi, uvicorn, sqlmodel, PyPDF2" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install --break-system-packages -r requirements.txt
fi

echo "🔧 Starting FastAPI backend on http://localhost:8000..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 api/main.py &
BACKEND_PID=$!

echo "🔄 Waiting for backend to start..."
sleep 3

# Test if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo "🎨 Starting React frontend..."
cd frontend

export REACT_APP_API_URL=http://localhost:8000

echo "📱 Frontend will be available at http://localhost:3000"
echo "🔗 Backend API is running at http://localhost:8000"
echo ""
echo "🛑 Press Ctrl+C to stop both services"

# Trap Ctrl+C to cleanup backend process
trap 'echo "🔄 Stopping services..."; kill $BACKEND_PID 2>/dev/null || true; exit 0' INT TERM

npm start

# Cleanup if npm start exits normally
kill $BACKEND_PID 2>/dev/null || true