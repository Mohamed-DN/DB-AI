Write-Host "Stopping current Ollama..."
docker stop ollama
docker rm ollama

Write-Host "🚀 Starting Ollama with GPU Support (--gpus=all)..."
try {
    docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    Write-Host "✅ Ollama restarted with GPU!"
}
catch {
    Write-Host "❌ Failed to start with GPU. Are NVIDIA drivers installed?"
    Write-Host "Falling back to CPU mode..."
    docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
}
