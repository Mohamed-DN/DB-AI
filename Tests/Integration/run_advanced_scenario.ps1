$env:PYTHONPATH = "c:\AI-Nexi\Nexi_DB_AI"
$env:PYTHONIOENCODING = "utf-8"
$env:MONGO_URI = "mongodb://admin:nexi2024@127.0.0.1:27017/?authSource=admin"

Write-Host "STEP 0: CLEANUP"
docker stop nexi-pg-milano-stg 2>$null
docker rm nexi-pg-milano-stg 2>$null
docker start nexi-pg-bratislava-dev
docker start nexi-pg-milano-dev
# Clean MongoDB
docker exec nexi-mongodb mongosh nexi_cmdb --username admin --password nexi2024 --authenticationDatabase admin --eval "db.monitoring_alerts.deleteMany({}); db.inventory_databases.deleteMany({});"

Write-Host "Environment Clean. Waiting for DBs..."
Start-Sleep -Seconds 10

Write-Host "STEP 1: DEPLOYING NEW DATABASE (Milano STG)..."
docker run -d --name nexi-pg-milano-stg -p 5435:5432 -e POSTGRES_PASSWORD=nexi2024 postgres:15
Start-Sleep -Seconds 10

Write-Host "STEP 2: RUNNING SCOUT (Discovery phase - Everything UP)..."
python c:\AI-Nexi\Nexi_DB_AI\Agents\Scout\main.py

Write-Host "STEP 3: DISASTER - BRATISLAVA DOWN..."
docker stop nexi-pg-bratislava-dev
Start-Sleep -Seconds 5

Write-Host "STEP 4: RUNNING CRITICAL ALERT AGENT (Detection)..."
python c:\AI-Nexi\Nexi_DB_AI\Agents\CriticalAlert\main.py --email mohamed.d.n.2002@gmail.com --once

Write-Host "STEP 5: RUNNING AI ORCHESTRATOR (Response)..."
python c:\AI-Nexi\Nexi_DB_AI\Orchestrator\main.py --once
