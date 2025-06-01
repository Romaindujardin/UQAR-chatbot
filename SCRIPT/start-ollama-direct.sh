#!/bin/bash
# Ultra-minimal script to start Ollama
mkdir -p "${HOME}/apptainer_data/ollama_data" "${HOME}/apptainer_data/logs" 
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=11434 nohup apptainer run --nv --bind "${HOME}/apptainer_data/ollama_data:/root/.ollama" docker://ollama/ollama:latest > ~/apptainer_data/logs/ollama.log 2>&1 &
echo $! > "${HOME}/apptainer_data/ollama_data/ollama.pid"
echo "Ollama started. Check ~/apptainer_data/logs/ollama.log for logs." 