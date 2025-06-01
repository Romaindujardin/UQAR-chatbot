#!/bin/bash
# Ultra-minimal script to stop Ollama
if [ -f "${HOME}/apptainer_data/ollama_data/ollama.pid" ]; then
    kill $(cat "${HOME}/apptainer_data/ollama_data/ollama.pid") 2>/dev/null || true
    rm -f "${HOME}/apptainer_data/ollama_data/ollama.pid"
fi
pkill -f ollama 2>/dev/null || true
echo "Ollama stopped" 