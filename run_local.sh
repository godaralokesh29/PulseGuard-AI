#!/bin/bash
set -e

echo "Starting PulseGuard-AI without Docker..."

# 1. Start the FastAPI Backend
echo "=> Starting backend on port 8000..."
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# 2. Start the Next.js Frontend
echo "=> Starting frontend on port 3000..."
npm install
npm run dev &
FRONTEND_PID=$!

echo "Both apps are running! Press Ctrl+C to stop them."

# Trap Ctrl+C to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
