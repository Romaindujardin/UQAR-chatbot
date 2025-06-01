#!/bin/bash

# Script pour arrêter Ollama démarré avec la méthode directe

echo "🛑 Arrêt d'Ollama..."

# Arrêter via PID sauvegardé
if [ -f "${HOME}/apptainer_data/ollama_data/ollama.pid" ]; then
    OLLAMA_PID=$(cat "${HOME}/apptainer_data/ollama_data/ollama.pid")
    echo "🔄 Arrêt du processus Ollama (PID: $OLLAMA_PID)"
    kill $OLLAMA_PID 2>/dev/null || true
    rm -f "${HOME}/apptainer_data/ollama_data/ollama.pid"
fi

# Arrêter toutes les instances Ollama (pour compatibilité)
apptainer instance stop ollama_instance >/dev/null 2>&1 || true

# Arrêter tous les processus Ollama restants
pkill -f ollama 2>/dev/null || true

# Vérifier si le port est libéré
if ss -tuln | grep -q ":11434 "; then
    echo "⚠️ Le port 11434 est toujours utilisé, tentative de libération..."
    fuser -k 11434/tcp 2>/dev/null || true
    sleep 1
    if ! ss -tuln | grep -q ":11434 "; then
        echo "✅ Port 11434 libéré avec succès"
    else
        echo "❌ Impossible de libérer le port 11434"
    fi
else
    echo "✅ Port 11434 libre"
fi

echo "✅ Arrêt d'Ollama terminé"
