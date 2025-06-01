#!/bin/bash

# Simple script to stop Ollama

# Kill by PID if available
if [ -f "${HOME}/apptainer_data/ollama_data/ollama.pid" ]; then
    PID=$(cat "${HOME}/apptainer_data/ollama_data/ollama.pid")
    kill $PID 2>/dev/null || true
    rm -f "${HOME}/apptainer_data/ollama_data/ollama.pid"
fi

# Kill all Ollama processes
pkill -f ollama 2>/dev/null || true

# Free port if needed
if ss -tuln | grep -q ":11434 "; then
    fuser -k 11434/tcp 2>/dev/null || true
fi

echo "Ollama stopped" 