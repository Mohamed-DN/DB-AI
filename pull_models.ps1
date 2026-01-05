Write-Host "🚀 Starting AI Model Download for RTX 5070 Ti..." -ForegroundColor Cyan

# Define models to pull
$models = @(
    "qwen2.5:14b",
    "deepseek-coder-v2:16b",
    "qwen2.5-coder:14b",
    "llama3.1:8b"
)

foreach ($model in $models) {
    Write-Host "`n⬇️  Pulling $model..." -ForegroundColor Yellow
    docker exec -it nexi-ollama ollama pull $model
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅  $model installed successfully." -ForegroundColor Green
    }
    else {
        Write-Host "❌  Failed to pull $model." -ForegroundColor Red
    }
}

Write-Host "`n✨ All operations completed." -ForegroundColor Cyan
Read-Host "Press Enter to exit"
