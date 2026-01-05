# Script per scaricare modelli LLM ottimizzati per RTX 5070 Ti (16GB VRAM)
# Eseguire da PowerShell dopo aver avviato il container Ollama

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  LLM Models Setup for RTX 5070 Ti    " -ForegroundColor Cyan
Write-Host "  16GB VRAM - GDDR7 Optimized         " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# -------------------------------------------------------------------
# CONFIGURAZIONE OTTIMALE PER 16GB VRAM
# -------------------------------------------------------------------
# Con RTX 5070 Ti (16GB VRAM GDDR7), possiamo eseguire:
# - Modelli fino a ~32B parametri con quantizzazione Q4_K_M
# - Context window fino a 16K (8K raccomandato per stabilita')
# - 100% GPU offload per massime prestazioni
# -------------------------------------------------------------------

Write-Host "`n>> MODELLO GENERALISTA (Raccomandato per Chat, Reasoning)" -ForegroundColor Green

# OPZIONE 1: Qwen3-30B-A3B (MoE, eccellente per reasoning)
# ~13GB VRAM a Q4, ottimo per chat e ragionamento
Write-Host "Scaricando Qwen3-30B-A3B (MoE, ~13GB Q4)..." -ForegroundColor Yellow
docker exec nexi-ollama ollama pull qwen3:30b-a3b

# OPZIONE 2: Mistral-Small-3.1-24B (molto veloce, ~14GB Q4)
Write-Host "Scaricando Mistral-Small-3.1-24B (~14GB Q4)..." -ForegroundColor Yellow
docker exec nexi-ollama ollama pull mistral-small3.1:24b

Write-Host "`n>> MODELLO CODING (Raccomandato per SQL, Python, Scripts)" -ForegroundColor Green

# OPZIONE 1: DeepSeek-R1-Distill-Qwen-14B (eccellente per coding)
# ~9GB VRAM, ottimo per SQL e reasoning su codice
Write-Host "Scaricando DeepSeek-R1-Distill-Qwen-14B (~9GB)..." -ForegroundColor Yellow
docker exec nexi-ollama ollama pull deepseek-r1:14b

# OPZIONE 2: Qwen3-14B (ottimo per coding generico)
Write-Host "Scaricando Qwen3-14B (~9GB Q4)..." -ForegroundColor Yellow
docker exec nexi-ollama ollama pull qwen3:14b

Write-Host "`n>> MODELLO VELOCE (Per risposte rapide)" -ForegroundColor Green
# Llama 3.2 8B - molto veloce, buon fallback
Write-Host "Scaricando Llama 3.2 8B (~5GB)..." -ForegroundColor Yellow
docker exec nexi-ollama ollama pull llama3.2:8b

Write-Host "`n>> MODELLO EMBEDDING (Per RAG)" -ForegroundColor Green
# nomic-embed-text per embeddings veloci
Write-Host "Scaricando nomic-embed-text..." -ForegroundColor Yellow
docker exec nexi-ollama ollama pull nomic-embed-text:latest

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  DOWNLOAD COMPLETATO!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`n>> Modelli disponibili:" -ForegroundColor Yellow
docker exec nexi-ollama ollama list

Write-Host @"

====================================================
  IMPOSTAZIONI CONSIGLIATE PER 16GB VRAM
====================================================

Per OLLAMA (gia' configurato nel sistema):
  - GPU Offload: 100% (automatico con CUDA)
  - Context Window: 8192 tokens (default)
  - Batch Size: 512

Per LM STUDIO - File GGUF consigliati da HuggingFace:
  
  1. GENERALISTA (~20B-30B):
     - File: Qwen3-30B-A3B-Q4_K_M.gguf
       Repo: https://huggingface.co/bartowski/Qwen3-30B-A3B-GGUF
     - File: Mistral-Small-3.1-24B-Instruct-2503.Q4_K_M.gguf
       Repo: https://huggingface.co/tensorcore/Mistral-Small-3.1-24B
       
  2. CODING (14B):
     - File: DeepSeek-R1-Distill-Qwen-14B-Q5_K_M.gguf
       Repo: https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF
     - File: Qwen3-14B-Q5_K_M.gguf
       Repo: https://huggingface.co/bartowski/Qwen3-14B-GGUF

  SETTINGS IN LM STUDIO:
    - GPU Layers: 99 (tutto su GPU)
    - CPU Threads: 0 (non usare CPU)
    - Context Length: 8192-16384
    - Batch Size: 512
    - mmap: OFF (per GPU pura)
    - mlock: OFF

====================================================
"@
