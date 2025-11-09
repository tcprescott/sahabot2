#!/bin/bash

# SahaBot2 Start Script
# Usage: ./start.sh [dev|prod]

MODE=${1:-dev}

if [ "$MODE" == "dev" ]; then
    echo "Starting SahaBot2 in development mode..."
    poetry run uvicorn main:app --reload --log-level debug --port 8080
elif [ "$MODE" == "prod" ]; then
    echo "Starting SahaBot2 in production mode..."
    export ENVIRONMENT=production
    export DEBUG=False
    # Single worker only - Discord bot runs in application lifecycle
    poetry run uvicorn main:app --host 0.0.0.0 --port 8080
else
    echo "Usage: ./start.sh [dev|prod]"
    exit 1
fi
