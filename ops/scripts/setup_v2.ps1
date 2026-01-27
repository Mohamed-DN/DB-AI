<#
.SYNOPSIS
    Nexi AI CMDB V2 - Setup & Startup Script
.DESCRIPTION
    Automates the full setup and startup of the Nexi AI CMDB V2 (Shadow Mode) system.
    1. Checks prerequisites (Docker)
    2. Loads configuration from .env.v2
    3. Stops conflicting V2 processes
    4. Starts Docker containers (using .env.v2 variables)
    5. Checks service health (MongoDB, Redis, Ollama, Qdrant)
    6. Starts Backend API
    7. Starts Frontend UI
.EXAMPLE
    .\setup_v2.ps1
    .\setup_v2.ps1 -SkipDocker
#>

param (
    [switch]$SkipDocker = $false,
    [switch]$SkipFrontend = $false,
    [switch]$SkipBackend = $false
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   NEXI AI CMDB V2 - SETUP & STARTUP" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# -----------------------------------------------------------------------------
# 0. Load Configuration
# -----------------------------------------------------------------------------
$EnvFile = "$PSScriptRoot\..\..\.env"
if (-not (Test-Path $EnvFile)) {
    Write-Error "Configuration file .env not found at $EnvFile"
    exit 1
}

Write-Host "Loading configuration from .env..." -ForegroundColor Gray
$EnvVars = @{}
Get-Content $EnvFile | Where-Object { $_ -match "^[^#].+=" } | ForEach-Object {
    $parts = $_ -split '=', 2
    $key = $parts[0].Trim()
    $val = $parts[1].Trim()
    $EnvVars[$key] = $val
    # Set process-level env var for child processes
    [Environment]::SetEnvironmentVariable($key, $val, "Process")
}

# -----------------------------------------------------------------------------
# 1. Prerequisite Checks
# -----------------------------------------------------------------------------
Write-Host "`n[STEP 1] Checking Prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is NOT installed or not in PATH."
    exit 1
}

# Check if Docker Daemon is running
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker Daemon is NOT running. Please start Docker Desktop."
    exit 1
}
Write-Host "✅ Docker is ready." -ForegroundColor Green

# -----------------------------------------------------------------------------
# 2. Cleanup Old Processes
# -----------------------------------------------------------------------------
Write-Host "`n[STEP 2] Cleaning up old V2 processes..." -ForegroundColor Yellow

# Kill Python Backend on V2 Port
$BackendPort = $EnvVars['BACKEND_PORT']
$ProcId = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
if ($ProcId) {
    Write-Host "Killing existing Backend on port $BackendPort (PID: $ProcId)..." -ForegroundColor Red
    Stop-Process -Id $ProcId -Force -ErrorAction SilentlyContinue
}

# Kill Node Frontend on V2 Port
$FrontendPort = $EnvVars['FRONTEND_PORT']
$ProcId = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
if ($ProcId) {
    Write-Host "Killing existing Frontend on port $FrontendPort (PID: $ProcId)..." -ForegroundColor Red
    Stop-Process -Id $ProcId -Force -ErrorAction SilentlyContinue
}

# -----------------------------------------------------------------------------
# 3. Docker Infrastructure (V2)
# -----------------------------------------------------------------------------
if (-not $SkipDocker) {
    Write-Host "`n[STEP 3] Starting V2 Infrastructure (Docker)..." -ForegroundColor Yellow
    $ComposeFile = "$PSScriptRoot\..\docker-lab\docker-compose.yml"
    
    # We use --env-file to pass .env.v2 to docker-compose
    Write-Host "Running docker-compose with .env.v2..." -ForegroundColor Gray
    docker-compose -f $ComposeFile --env-file $EnvFile up -d

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start Docker containers."
        exit 1
    }
    Write-Host "✅ V2 Infrastructure Started." -ForegroundColor Green
    
    # Wait for Health
    Write-Host "Waiting 10s for services to initialize..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
}
else {
    Write-Host "Skipping Docker startup (User Request)." -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# 4. Service Health Checks
# -----------------------------------------------------------------------------
Write-Host "`n[STEP 4] Verifying Service Health..." -ForegroundColor Yellow

function Test-Port($port, $name) {
    if (-not $port) {
        Write-Host "⚠️  $name PORT not defined. Skipping check." -ForegroundColor Gray
        return $false
    }
    # Use 127.0.0.1 to force IPv4 and avoid ::1 connection issues
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -WarningAction SilentlyContinue
    if ($conn.TcpTestSucceeded) {
        Write-Host "✅ $name is UP (Port $port)" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "❌ $name is DOWN (Port $port)" -ForegroundColor Red
        return $false
    }
}

Test-Port $EnvVars['MONGODB_PORT'] "MongoDB V2"
Test-Port $EnvVars['REDIS_PORT'] "Redis Core V2"
Test-Port $EnvVars['REDIS_MILANO_PORT'] "Redis Milano (GW1)"
Test-Port $EnvVars['REDIS_BRATISLAVA_PORT'] "Redis Bratislava (GW2)"
Test-Port $EnvVars['REDIS_CAIRO_PORT'] "Redis Cairo (GW3)"
Test-Port $EnvVars['OLLAMA_PORT'] "Ollama V2"
Test-Port $EnvVars['QDRANT_PORT'] "Qdrant V2"
Test-Port $EnvVars['MONGO_EXPRESS_PORT'] "Mongo Express V2"

# -----------------------------------------------------------------------------
# 5. Start Backend API
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# 5. Start Backend API
# -----------------------------------------------------------------------------
if (-not $SkipBackend) {
    Write-Host "`n[STEP 5] Starting Backend API (Port $($EnvVars['BACKEND_PORT']))..." -ForegroundColor Yellow
    
    $BackendDir = "$PSScriptRoot\..\..\api_agents\api_gateway"
    
    # 5.1 Check Dependencies (Backend)
    Write-Host "Checking Python dependencies..." -ForegroundColor Gray
    if (-not (Test-Path "$BackendDir\venv") -and -not (Get-Command uvicorn -ErrorAction SilentlyContinue)) {
        # Simple check: just run pip install every time to be safe, or check imports
        Write-Host "Installing/Updating Python requirements..." -ForegroundColor Cyan
        pip install -r "$BackendDir\requirements.txt" | Out-Null
    }
    else {
        # Still run it to be sure new deps are there
        pip install -r "$BackendDir\requirements.txt"
    }

    # Pass critical env vars explicitly as args if needed, or rely on Process Env we set earlier
    # IMPORTANT: MongoProxy needs MONGO_CONTAINER which is likely 'nexi-mongodb2' from compose
    # We set these in Process Env in Step 0, so python should pick them up.
    
    # Explicitly set connection params for MongoProxy inside backend
    $env:MONGO_CONTAINER = "nexi-mongodb2"
    $env:MONGODB_DB = $EnvVars['MONGODB_DB']
    $env:MONGO_USERNAME = $EnvVars['MONGO_USERNAME']
    $env:MONGO_PASSWORD = $EnvVars['MONGO_PASSWORD']

    # Use 'python -m uvicorn' instead of 'uvicorn' to avoid PATH issues on some systems
    Start-Process -FilePath "python" `
        -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port $($EnvVars['BACKEND_PORT']) --reload" `
        -WorkingDirectory $BackendDir `
        -NoNewWindow
    
    Write-Host "✅ Backend API Started." -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 6. Start Frontend
# -----------------------------------------------------------------------------
if (-not $SkipFrontend) {
    Write-Host "`n[STEP 6] Starting Frontend UI (Port $($EnvVars['FRONTEND_PORT']))..." -ForegroundColor Yellow
    
    $FrontendDir = "$PSScriptRoot\..\..\web\dashboard"
    
    # Check node_modules
    if (-not (Test-Path "$FrontendDir\node_modules")) {
        Write-Host "Installing Frontend dependencies (npm install)... This may take a while." -ForegroundColor Cyan
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm install" -WorkingDirectory $FrontendDir -Wait
    }
    
    # Start Vite with V2 config
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c npm run dev" `
        -WorkingDirectory $FrontendDir
                  
    Write-Host "✅ Frontend UI Started." -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 7. Seed MongoDB (if empty)
# -----------------------------------------------------------------------------
Write-Host "`n[STEP 7] Seeding MongoDB Collections..." -ForegroundColor Yellow
$SeedScript = "$PSScriptRoot\..\..\mongo\seeds\seed_mongodb.py"
if (Test-Path $SeedScript) {
    python $SeedScript
}
else {
    Write-Host "⚠️  Seed script not found, skipping." -ForegroundColor Gray
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "   NEXI AI CMDB V2 IS READY 🚀" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   Dashboard:    http://localhost:$($EnvVars['FRONTEND_PORT'])"
Write-Host "   API Docs:     http://localhost:$($EnvVars['BACKEND_PORT'])/docs"
Write-Host "   Mongo UI:     http://localhost:$($EnvVars['MONGO_EXPRESS_PORT'])"
Write-Host "   Ollama:       http://localhost:$($EnvVars['OLLAMA_PORT'])"
Write-Host "=================================================================" -ForegroundColor Cyan

