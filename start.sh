#!/bin/bash

# SahaBot2 Start Script
# Usage: ./start.sh [dev|prod]

MODE=${1:-dev}

if [ "$MODE" == "dev" ]; then
    echo "Starting SahaBot2 in development mode..."
    poetry run python main.py
elif [ "$MODE" == "prod" ]; then
    echo "Starting SahaBot2 in production mode..."
    export ENVIRONMENT=production
    export DEBUG=False
    poetry run uvicorn main:app --host 0.0.0.0 --port 80 --workers 4
else
    echo "Usage: ./start.sh [dev|prod]"
    exit 1
fi
