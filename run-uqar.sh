#!/bin/bash

# Script central pour démarrer l'Assistant Éducatif UQAR depuis le dossier UQAR_GIT
# Auteur: Claude Sonnett
# Date: 2025-06-01

set -e

# Définir les chemins relatifs
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLLAMA_DATA_DIR="${SCRIPT_DIR}/apptainer_data/ollama_data"
LOGS_DIR="${SCRIPT_DIR}/apptainer_data/logs"

echo "🚀 Démarrage de l'Assistant Éducatif UQAR depuis ${SCRIPT_DIR}"
echo "============================================================="

# Créer les dossiers nécessaires
mkdir -p "${OLLAMA_DATA_DIR}"
mkdir -p "${LOGS_DIR}"
mkdir -p "${SCRIPT_DIR}/uqar_data/chromadb"
mkdir -p "${SCRIPT_DIR}/uqar_data/postgres"
mkdir -p "${SCRIPT_DIR}/uqar_data/uploads"

# 1. Démarrer Ollama avec la méthode directe
echo "🔄 Démarrage d'Ollama..."

# Arrêter Ollama existant si présent
pkill -f ollama 2>/dev/null || true
sleep 2

# Libérer le port 11434 si utilisé
if ss -tuln | grep -q ":11434 "; then
    echo "⚠️ Port 11434 occupé, tentative de libération..."
    fuser -k 11434/tcp 2>/dev/null || true
    sleep 2
fi

# Démarrer Ollama directement en arrière-plan
# Option 1: Processus direct (méthode actuelle)
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=11434 nohup apptainer run --nv \
    --bind "${OLLAMA_DATA_DIR}:/root/.ollama" \
    "${SCRIPT_DIR}/UQAR/ollama.sif" > "${LOGS_DIR}/ollama.log" 2>&1 &

# Sauvegarder le PID
echo $! > "${OLLAMA_DATA_DIR}/ollama.pid"
echo "⏳ Ollama démarré avec PID: $!"

# Option 2: Instance Apptainer (commentée par défaut)
# Décommentez ces lignes et commentez l'option 1 si vous voulez qu'Ollama apparaisse dans "apptainer instance list"
#
# apptainer instance start \
#     --nv \
#     --bind "${OLLAMA_DATA_DIR}:/root/.ollama" \
#     --env "OLLAMA_HOST=0.0.0.0" \
#     --env "OLLAMA_PORT=11434" \
#     "${SCRIPT_DIR}/UQAR/ollama.sif" ollama_instance
# echo "⏳ Ollama démarré comme instance Apptainer"

# Attendre que Ollama démarre
echo "⏳ Attente du démarrage d'Ollama..."
for i in {1..15}; do
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "✅ Ollama est prêt!"
        break
    fi
    sleep 1
    echo -n "."
done

# 2. Démarrer le reste des services avec le script existant
echo "🔄 Démarrage des autres services..."
cd "${SCRIPT_DIR}/UQAR"
./start-apptainer-direct-no-ollama.sh

echo ""
echo "✅ Tous les services ont été démarrés!"
echo ""
echo "🌐 Accès aux services :"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Docs API:    http://localhost:8000/docs"
echo "   ChromaDB:    http://localhost:8001"
echo "   Ollama:      http://localhost:11434"
echo ""
echo "📋 Pour arrêter tous les services : ${SCRIPT_DIR}/stop-uqar.sh"
echo "" 