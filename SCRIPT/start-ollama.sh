#!/bin/bash
PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Commande directe pour démarrer Ollama avec llama3.1:70b
# Utilise l'adresse 0.0.0.0 sur le port 11434

# Stop any existing Ollama
pkill -f ollama 2>/dev/null || true
sleep 2

# Free port if needed
if ss -tuln | grep -q ":11434 "; then
    fuser -k 11434/tcp 2>/dev/null || true
    sleep 2
fi

# Create necessary directories
kdir -p "${PROJET_ROOT}/apptainer_data/ollama_data"
mkdir -p "${PROJET_ROOT}/apptainer_data/logs"

# Start Ollama in background with specific parameters
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=11434 nohup apptainer run --nv \
    --bind "${PROJET_ROOT}/apptainer_data/ollama_data:/root/.ollama" \
    docker://ollama/ollama:latest > ${PROJET_ROOT}/apptainer_data/logs/ollama.log 2>&1 &

# Save PID
echo $! > "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid"
echo "Ollama started with PID: $!"
echo "Check logs at: ${PROJET_ROOT}/apptainer_data/logs/ollama.log" 