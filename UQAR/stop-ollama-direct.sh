#!/bin/bash
# Ultra-minimal script to stop Ollama
PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid" ]; then
    kill $(cat "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid") 2>/dev/null || true
    rm -f "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid"
fi
pkill -f ollama 2>/dev/null || true
echo "Ollama stopped" 