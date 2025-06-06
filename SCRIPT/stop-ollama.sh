#!/bin/bash
PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Simple script to stop Ollama

# Kill by PID if available
if [ -f "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid" ]; then
    PID=$(cat "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid")
    kill $PID 2>/dev/null || true
    rm -f "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid"
fi

# Kill all Ollama processes
pkill -f ollama 2>/dev/null || true

# Free port if needed
if ss -tuln | grep -q ":11434 "; then
    fuser -k 11434/tcp 2>/dev/null || true
fi

echo "Ollama stopped" 