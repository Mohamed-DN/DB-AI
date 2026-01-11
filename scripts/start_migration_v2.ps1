# =============================================================================
# NEXI AI CMDB V2 - Clean Migration Start Script (Shadow Mode)
# =============================================================================
# Questo script avvia l'intero stack V2 in parallelo al sistema V1.
# Tutte le porte sono offset di +1000 per evitare conflitti.
#
# Usage: .\scripts\start_migration_v2.ps1
#        .\scripts\start_migration_v2.ps1 -HealthCheckOnly
# =============================================================================

param(
    [switch]$HealthCheckOnly = $false,
    [switch]$SkipDocker = $false
)

# Force UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

$ProjectRoot = "c:\AI-Nexi\Nexi_DB_AI"
$DockerLabPath = "$ProjectRoot\docker-lab"

# --- Colors ---
function Write-Title($msg) { Write-Host "`n$msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Write-Info($msg) { Write-Host "  [INFO] $msg" -ForegroundColor Yellow }

# --- Banner ---
Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "   NEXI AI CMDB V2 - Shadow Environment Startup                " -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""

# =============================================================================
# STEP 1: Check Prerequisites
# =============================================================================
Write-Title "STEP 1: Checking Prerequisites..."

# Check Docker
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker installed: $dockerVersion"
    }
    else {
        throw "Docker not found"
    }
}
catch {
    Write-Fail "Docker is not installed or not in PATH"
    exit 1
}

# Check Docker Desktop running
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker Desktop is running"
    }
    else {
        throw "Docker daemon not running"
    }
}
catch {
    Write-Fail "Docker Desktop is not running. Please start it first."
    exit 1
}

# =============================================================================
# STEP 2: Start Docker Containers (V2)
# =============================================================================
if (-not $HealthCheckOnly -and -not $SkipDocker) {
    Write-Title "STEP 2: Starting Docker Containers (V2 Stack)..."
    
    Set-Location $DockerLabPath
    
    # Check if docker-compose-v2.yml exists
    if (-not (Test-Path "docker-compose-v2.yml")) {
        Write-Fail "docker-compose-v2.yml not found in $DockerLabPath"
        exit 1
    }
    
    # Start V2 containers
    Write-Info "Starting containers with docker-compose-v2.yml..."
    docker-compose -f docker-compose-v2.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "V2 containers started successfully"
    }
    else {
        Write-Fail "Failed to start V2 containers"
        exit 1
    }
    
    # Wait for services to be ready
    Write-Info "Waiting 15 seconds for services to initialize..."
    Start-Sleep -Seconds 15
    
    Set-Location $ProjectRoot
}

# =============================================================================
# STEP 3: Health Checks
# =============================================================================
Write-Title "STEP 3: Running Health Checks..."

$healthResults = @()

# Check MongoDB V2 (port 28017)
try {
    $mongoCheck = Test-NetConnection -ComputerName localhost -Port 28017 -WarningAction SilentlyContinue
    if ($mongoCheck.TcpTestSucceeded) {
        Write-Ok "MongoDB V2 (port 28017) - ONLINE"
        $healthResults += @{Service = "MongoDB V2"; Port = 28017; Status = "OK" }
    }
    else {
        throw "Connection failed"
    }
}
catch {
    Write-Fail "MongoDB V2 (port 28017) - OFFLINE"
    $healthResults += @{Service = "MongoDB V2"; Port = 28017; Status = "FAIL" }
}

# Check Redis V2 (port 7379)
try {
    $redisCheck = Test-NetConnection -ComputerName localhost -Port 7379 -WarningAction SilentlyContinue
    if ($redisCheck.TcpTestSucceeded) {
        Write-Ok "Redis V2 (port 7379) - ONLINE"
        $healthResults += @{Service = "Redis V2"; Port = 7379; Status = "OK" }
    }
    else {
        throw "Connection failed"
    }
}
catch {
    Write-Fail "Redis V2 (port 7379) - OFFLINE"
    $healthResults += @{Service = "Redis V2"; Port = 7379; Status = "FAIL" }
}

# Check Ollama V2 (port 12434)
try {
    $ollamaCheck = Test-NetConnection -ComputerName localhost -Port 12434 -WarningAction SilentlyContinue
    if ($ollamaCheck.TcpTestSucceeded) {
        Write-Ok "Ollama V2 (port 12434) - ONLINE"
        $healthResults += @{Service = "Ollama V2"; Port = 12434; Status = "OK" }
    }
    else {
        throw "Connection failed"
    }
}
catch {
    Write-Fail "Ollama V2 (port 12434) - OFFLINE"
    $healthResults += @{Service = "Ollama V2"; Port = 12434; Status = "FAIL" }
}

# Check Qdrant V2 (port 7333)
try {
    $qdrantCheck = Test-NetConnection -ComputerName localhost -Port 7333 -WarningAction SilentlyContinue
    if ($qdrantCheck.TcpTestSucceeded) {
        Write-Ok "Qdrant V2 (port 7333) - ONLINE"
        $healthResults += @{Service = "Qdrant V2"; Port = 7333; Status = "OK" }
    }
    else {
        throw "Connection failed"
    }
}
catch {
    Write-Fail "Qdrant V2 (port 7333) - OFFLINE"
    $healthResults += @{Service = "Qdrant V2"; Port = 7333; Status = "FAIL" }
}

# Check Mongo Express V2 (port 9081)
try {
    $meCheck = Test-NetConnection -ComputerName localhost -Port 9081 -WarningAction SilentlyContinue
    if ($meCheck.TcpTestSucceeded) {
        Write-Ok "Mongo Express V2 (port 9081) - ONLINE"
        $healthResults += @{Service = "Mongo Express V2"; Port = 9081; Status = "OK" }
    }
    else {
        throw "Connection failed"
    }
}
catch {
    Write-Fail "Mongo Express V2 (port 9081) - OFFLINE"
    $healthResults += @{Service = "Mongo Express V2"; Port = 9081; Status = "FAIL" }
}

if ($HealthCheckOnly) {
    Write-Title "Health Check Complete"
    $passed = ($healthResults | Where-Object { $_.Status -eq "OK" }).Count
    $total = $healthResults.Count
    Write-Host "`n  Result: $passed/$total services online" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })
    exit $(if ($passed -eq $total) { 0 } else { 1 })
}

# =============================================================================
# STEP 4: Start Backend API (V2)
# =============================================================================
Write-Title "STEP 4: Starting Backend API (Port 9000)..."

# Set V2 environment variables
$env:MONGODB_PORT = "28017"
$env:MONGODB_HOST = "localhost"
$env:MONGODB_DB = "nexi_cmdb_v2"
$env:OLLAMA_HOST = "http://localhost:12434"
$env:QDRANT_HOST = "http://localhost:7333"

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    cd '$ProjectRoot\WebInterface\backend'
    `$env:MONGODB_PORT = '28017'
    `$env:MONGODB_HOST = 'localhost'  
    `$env:MONGODB_DB = 'nexi_cmdb_v2'
    `$env:OLLAMA_HOST = 'http://localhost:12434'
    `$env:QDRANT_HOST = 'http://localhost:7333'
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host '  NEXI AI CMDB V2 - Backend API        ' -ForegroundColor Cyan
    Write-Host '  Port: 9000                           ' -ForegroundColor Cyan
    Write-Host '========================================' -ForegroundColor Cyan
    python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
"@

Write-Ok "Backend API V2 starting on port 9000"
Start-Sleep -Seconds 3

# =============================================================================
# STEP 5: Start React Frontend (V2)
# =============================================================================
Write-Title "STEP 5: Starting React Frontend (Port 4002)..."

Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    cd '$ProjectRoot\WebInterface\frontend-react'
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host '  NEXI AI CMDB V2 - React Frontend     ' -ForegroundColor Cyan
    Write-Host '  Port: 4002                           ' -ForegroundColor Cyan
    Write-Host '========================================' -ForegroundColor Cyan
    npm run dev -- --config vite.config.v2.ts
"@

Write-Ok "React Frontend V2 starting on port 4002"
Start-Sleep -Seconds 3

# =============================================================================
# FINAL: Summary
# =============================================================================
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "   V2 SHADOW ENVIRONMENT STARTED SUCCESSFULLY!                 " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points (V2 System):" -ForegroundColor Cyan
Write-Host "  - React Dashboard V2:  http://localhost:4002" -ForegroundColor White
Write-Host "  - Backend API V2:      http://localhost:9000" -ForegroundColor White
Write-Host "  - Mongo Express V2:    http://localhost:9081" -ForegroundColor White
Write-Host "  - Open WebUI V2:       http://localhost:4001" -ForegroundColor White
Write-Host ""
Write-Host "Original System (V1) - Should still be available:" -ForegroundColor Yellow
Write-Host "  - React Dashboard V1:  http://localhost:3002" -ForegroundColor Gray
Write-Host "  - Backend API V1:      http://localhost:8000" -ForegroundColor Gray
Write-Host "  - Mongo Express V1:    http://localhost:8081" -ForegroundColor Gray
Write-Host ""
Write-Host "Docker Commands:" -ForegroundColor Cyan
Write-Host "  - Stop V2:  docker-compose -f docker-lab/docker-compose-v2.yml down" -ForegroundColor Gray
Write-Host "  - Logs V2:  docker-compose -f docker-lab/docker-compose-v2.yml logs -f" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Enter to open V2 Dashboard..." -ForegroundColor Gray
Read-Host
Start-Process "http://localhost:4002"
