#!/bin/bash
PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Script pour démarrer Ollama avec llama3.1:70b
# Utilise l'adresse 0.0.0.0 sur le port 11434

# Arrêter Ollama existant si présent
pkill -f ollama 2>/dev/null || true
sleep 2

# Libérer le port 11434 si utilisé
if ss -tuln | grep -q ":11434 "; then
    echo "⚠️ Port 11434 occupé, tentative de libération..."
    fuser -k 11434/tcp 2>/dev/null || true
    sleep 2
fi

# Créer les dossiers nécessaires
mkdir -p "${PROJET_ROOT}/apptainer_data/ollama_data"
mkdir -p "${PROJET_ROOT}/apptainer_data/logs"

# Démarrer Ollama directement en arrière-plan
echo "🔄 Démarrage d'Ollama sur port 11434..."
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=11434 nohup apptainer run --nv \
    --bind "${PROJET_ROOT}/apptainer_data/ollama_data:/root/.ollama" \
    docker://ollama/ollama:latest > ${PROJET_ROOT}/apptainer_data/logs/ollama.log 2>&1 &

# Sauvegarder le PID
echo $! > "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid"
echo "⏳ Ollama démarré avec PID: $!"

# Vérifier le démarrage
sleep 5
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama démarré avec succès"
else
    echo "⚠️ Ollama pourrait ne pas avoir démarré correctement"
    echo "  Vérifiez les logs: ${PROJET_ROOT}/apptainer_data/logs/ollama.log"
fi
