# Migration Script for Nexi DBA AI V3 Refactoring
# Usage: .\migrate_structure.ps1

$ErrorActionPreference = "Stop"

function Move-Safe {
    param ($Source, $Dest)
    if (Test-Path $Source) {
        Write-Host "Moving $Source to $Dest"
        if (-not (Test-Path $Dest)) {
            New-Item -ItemType Directory -Force -Path $Dest | Out-Null
        }
        Move-Item -Path $Source -Destination $Dest -Force
    }
    else {
        Write-Warning "Source not found: $Source"
    }
}

function Move-Content {
    param ($SourceDir, $DestDir)
    if (Test-Path $SourceDir) {
        Write-Host "Moving contents of $SourceDir to $DestDir"
        if (-not (Test-Path $DestDir)) {
            New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
        }
        Get-ChildItem -Path $SourceDir | Move-Item -Destination $DestDir -Force
    }
    else {
        Write-Warning "Source directory not found: $SourceDir"
    }
}

Write-Host "Starting Migration..."

# 1. WEB
New-Item -ItemType Directory -Force -Path "web/dashboard" | Out-Null
New-Item -ItemType Directory -Force -Path "web/legacy" | Out-Null
Move-Content -SourceDir "WebInterface/frontend-react" -DestDir "web/dashboard"
Move-Content -SourceDir "WebInterface/frontend" -DestDir "web/legacy"

# 2. API & AGENTS
New-Item -ItemType Directory -Force -Path "api_agents/api_gateway" | Out-Null
New-Item -ItemType Directory -Force -Path "api_agents/workers" | Out-Null
New-Item -ItemType Directory -Force -Path "api_agents/shared" | Out-Null

# Move Backend
Move-Content -SourceDir "WebInterface/backend" -DestDir "api_agents/api_gateway"

# Move Agents
if (Test-Path "Agents") {
    Get-ChildItem "Agents" | Where-Object { $_.Name -ne "Monitor" -and $_.Name -ne "checkmk_bridge" } | ForEach-Object {
        Move-Safe -Source $_.FullName -Dest "api_agents/workers"
    }
    # Move Monitor/Shared
    Move-Safe -Source "Agents/Monitor" -Dest "api_agents/shared"
}

# 3. ORCHESTRATOR
New-Item -ItemType Directory -Force -Path "orchestrator/core" | Out-Null
if (Test-Path "Orchestrator") {
    Move-Safe -Source "Orchestrator/rag" -Dest "orchestrator"
    Move-Safe -Source "Orchestrator/vector_db" -Dest "orchestrator"
    Move-Safe -Source "Orchestrator/modules" -Dest "orchestrator"
    
    # Move Core
    Move-Safe -Source "Orchestrator/src" -Dest "orchestrator/core"
    Move-Safe -Source "Orchestrator/main.py" -Dest "orchestrator/core"
    Move-Safe -Source "Orchestrator/__init__.py" -Dest "orchestrator/core"
}

# 4. LLM
New-Item -ItemType Directory -Force -Path "llm/client" | Out-Null
New-Item -ItemType Directory -Force -Path "llm/config" | Out-Null
if (Test-Path "Orchestrator") {
    Move-Content -SourceDir "Orchestrator/llm" -DestDir "llm/client"
    Move-Content -SourceDir "Orchestrator/config" -DestDir "llm/config"
}

# 5. MONGO
New-Item -ItemType Directory -Force -Path "mongo/schemas" | Out-Null
New-Item -ItemType Directory -Force -Path "mongo/scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "mongo/seeds" | Out-Null

Move-Safe -Source "MongoDB/struttura_mongo" -Dest "mongo/schemas/definitions"
Move-Safe -Source "MongoDB/Schemas" -Dest "mongo/schemas/json"
Move-Content -SourceDir "MongoDB/scripts" -DestDir "mongo/scripts"
# Move standard files
Move-Safe -Source "MongoDB/docker-compose.yml" -Dest "mongo"
Move-Safe -Source "MongoDB/Script_oracle_to_mongo.sql" -Dest "mongo/scripts"

# Execution seeds
if (Test-Path "execution") {
    Get-ChildItem "execution/seed*" | Move-Item -Destination "mongo/seeds" -Force
}

# 6. LANGRAPH
New-Item -ItemType Directory -Force -Path "langraph" | Out-Null
# (Placeholder or relevant files)

# 7. DOCS
New-Item -ItemType Directory -Force -Path "docs/architecture" | Out-Null
Move-Safe -Source "directives" -Dest "docs"
Move-Content -SourceDir "docs" -DestDir "docs/architecture"

# 8. OPS
New-Item -ItemType Directory -Force -Path "ops/scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "ops/gateway" | Out-Null

Move-Safe -Source "docker-lab" -Dest "ops"
Move-Content -SourceDir "scripts" -DestDir "ops/scripts"
Move-Content -SourceDir "Gateway" -DestDir "ops/gateway"

# CLEANUP
Write-Host "Cleaning up empty directories..."
Remove-Item "WebInterface" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "Agents" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "Orchestrator" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "MongoDB" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "Gateway" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Migration Complete!"
