#!/bin/sh
# Start script for Railway deployment

# Get the PORT from environment or use default
PORT=${PORT:-8000}

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
