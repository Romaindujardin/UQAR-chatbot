#!/bin/bash

# Script pour arrêter tous les services de l'Assistant Éducatif UQAR
# Auteur: Claude Sonnett
# Date: 2025-06-01

# Définir les chemins relatifs
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLLAMA_DATA_DIR="${SCRIPT_DIR}/apptainer_data/ollama_data"

echo "🛑 Arrêt de l'Assistant Éducatif UQAR..."
echo "========================================="

# 1. Arrêter Ollama avec la méthode directe
echo "🔄 Arrêt d'Ollama..."
if [ -f "${OLLAMA_DATA_DIR}/ollama.pid" ]; then
    OLLAMA_PID=$(cat "${OLLAMA_DATA_DIR}/ollama.pid")
    echo "   Arrêt du processus Ollama (PID: $OLLAMA_PID)"
    kill $OLLAMA_PID 2>/dev/null || true
    rm -f "${OLLAMA_DATA_DIR}/ollama.pid"
fi

# 2. Arrêter toutes les instances Apptainer
echo "🔄 Arrêt de toutes les instances Apptainer..."
apptainer instance list | awk '{if(NR>1)print $1}' | xargs -I{} apptainer instance stop {} 2>/dev/null || echo "Aucune instance Apptainer en cours d'exécution"

# 3. Tuer tous les processus Ollama restants
echo "🔄 Arrêt de tous les processus Ollama restants..."
pkill -f ollama 2>/dev/null || echo "Aucun processus Ollama en cours d'exécution"

# 4. Vérifier les ports utilisés par les services
echo "🔍 Vérification des ports ouverts..."
echo "Ports Ollama (11434, 11435):"
ss -tuln | grep -E '11434|11435' || echo "Aucun port Ollama n'est ouvert"
echo "Port PostgreSQL (5432, 38705):"
ss -tuln | grep -E '5432|38705' || echo "Aucun port PostgreSQL n'est ouvert"
echo "Port Backend (8000):"
ss -tuln | grep 8000 || echo "Aucun port Backend n'est ouvert"
echo "Port Frontend (3000):"
ss -tuln | grep 3000 || echo "Aucun port Frontend n'est ouvert"
echo "Port ChromaDB (8001):"
ss -tuln | grep 8001 || echo "Aucun port ChromaDB n'est ouvert"

# 5. Forcer la libération des ports si nécessaire
for PORT in 11434 11435 5432 38705 8000 3000 8001; do
    if ss -tuln | grep -q ":$PORT "; then
        echo "⚠️ Port $PORT toujours utilisé, tentative de libération forcée..."
        fuser -k ${PORT}/tcp 2>/dev/null || true
    fi
done

echo ""
echo "✅ Arrêt de tous les services terminé"
echo ""
echo "📋 Pour redémarrer les services : ${SCRIPT_DIR}/run-uqar.sh" 