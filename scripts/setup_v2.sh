#!/bin/bash

# NEXI AI CMDB V2 - Setup & Startup Script (Mac/Linux)
# Mimics setup_v2.ps1

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$SCRIPT_DIR/.."
ENV_FILE="$ROOT_DIR/.env.v2"

echo "================================================================="
echo "   NEXI AI CMDB V2 - SETUP & STARTUP (Mac/Linux)"
echo "================================================================="

# 0. Load Configuration
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Configuration file .env.v2 not found at $ENV_FILE"
    exit 1
fi

echo "Loading configuration from .env.v2..."
# Parse .env file line by line
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    
    # Extract key and value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        key=$(echo "${BASH_REMATCH[1]}" | xargs)
        value=$(echo "${BASH_REMATCH[2]}" | xargs)
        # Remove inline comments if any (simple case)
        # value=${value%% #*} # This might be risky if value contains #
        
        # Check if key is valid identifier
        if [[ "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            export "$key=$value"
        fi
    fi
done < "$ENV_FILE"

# 1. Prerequisite Checks
echo -e "\n[STEP 1] Checking Prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "Docker is NOT installed or not in PATH."
    exit 1
fi

# Check if Docker Daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker Daemon is NOT running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is ready."

# 2. Cleanup Old Processes
echo -e "\n[STEP 2] Cleaning up old V2 processes..."

kill_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -ti :$port)
    if [ -n "$pid" ]; then
        echo "Killing existing $name on port $port (PID: $pid)..."
        kill -9 $pid
    fi
}

if [ -n "$BACKEND_PORT" ]; then kill_port $BACKEND_PORT "Backend"; fi
if [ -n "$FRONTEND_PORT" ]; then kill_port $FRONTEND_PORT "Frontend"; fi

# 3. Docker Infrastructure (V2)
if [[ "$*" != *"--skip-docker"* ]]; then
    echo -e "\n[STEP 3] Starting V2 Infrastructure (Docker)..."
    COMPOSE_FILE="$ROOT_DIR/docker-lab/docker-compose-v2.yml"
    
    echo "Running docker-compose with .env.v2..."
    # Pull first to avoid timeouts/crashes during up
    echo "Pulling images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull --ignore-pull-failures

    echo "Starting containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    echo "✅ V2 Infrastructure Started."
    echo "Waiting 10s for services to initialize..."
    sleep 10
else
    echo "Skipping Docker startup."
fi

# 4. Service Health Checks
echo -e "\n[STEP 4] Verifying Service Health..."
check_port() {
    local port=$1
    local name=$2
    if nc -z localhost $port; then
        echo "✅ $name is UP (Port $port)"
    else
        echo "❌ $name is DOWN (Port $port)"
    fi
}

check_port "${MONGODB_PORT:-28017}" "MongoDB V2"
check_port "${REDIS_PORT:-7379}" "Redis V2"
check_port "${OLLAMA_PORT:-12434}" "Ollama V2"
check_port "${QDRANT_PORT:-7333}" "Qdrant V2"

# 5. Start Backend API
if [[ "$*" != *"--skip-backend"* ]]; then
    echo -e "\n[STEP 5] Starting Backend API (Port ${BACKEND_PORT})..."
    BACKEND_DIR="$ROOT_DIR/WebInterface/backend"
    
    cd "$BACKEND_DIR"
    
    if [ ! -d "venv" ]; then
        echo "Creating python venv..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    echo "Installing/Updating Python requirements..."
    pip install -r requirements.txt
    
    # Export specific vars for backend
    export MONGO_CONTAINER="nexi-mongodb2"
    export MONGODB_DB="$MONGODB_DB"
    export MONGO_USERNAME="$MONGO_USERNAME"
    export MONGO_PASSWORD="$MONGO_PASSWORD"

    echo "Starting Uvicorn..."
    # Run in background
    nohup python -m uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > "$ROOT_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "Backend started with PID $BACKEND_PID. Logs at $ROOT_DIR/backend.log"
    
    cd "$SCRIPT_DIR"
    echo "✅ Backend API Started."
fi

# 6. Start Frontend
if [[ "$*" != *"--skip-frontend"* ]]; then
    echo -e "\n[STEP 6] Starting Frontend UI (Port ${FRONTEND_PORT})..."
    FRONTEND_DIR="$ROOT_DIR/WebInterface/frontend-react"
    
    cd "$FRONTEND_DIR"
    
    if [ ! -d "node_modules" ]; then
        echo "Installing Frontend dependencies..."
        npm install
    fi
    
    echo "Starting Vite..."
    # Run in background
    nohup npm run dev:v2 > "$ROOT_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend started with PID $FRONTEND_PID. Logs at $ROOT_DIR/frontend.log"
    
    cd "$SCRIPT_DIR"
    echo "✅ Frontend UI Started."
fi

# 7. Seed MongoDB
echo -e "\n[STEP 7] Seeding MongoDB Collections..."
SEED_SCRIPT="$ROOT_DIR/execution/seed_mongodb.py"
if [ -f "$SEED_SCRIPT" ]; then
    source "$ROOT_DIR/WebInterface/backend/venv/bin/activate"
    python "$SEED_SCRIPT"
else
    echo "⚠️  Seed script not found, skipping."
fi

echo -e "\n================================================================="
echo "   NEXI AI CMDB V2 IS READY 🚀"
echo "================================================================="
echo "   Dashboard:    http://localhost:${FRONTEND_PORT}"
echo "   API Docs:     http://localhost:${BACKEND_PORT}/docs"
echo "   Mongo UI:     http://localhost:${MONGO_EXPRESS_PORT}"
echo "================================================================="
