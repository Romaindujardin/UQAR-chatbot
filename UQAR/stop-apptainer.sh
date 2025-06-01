#!/bin/bash

# Script d'arrêt pour l'Assistant Éducatif UQAR avec Apptainer

echo "🛑 Arrêt des services Apptainer pour UQAR"
echo "========================================"

# Vérifier que Apptainer est installé
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer n'est pas installé."
    exit 1
fi

# Lister les instances en cours d'exécution
echo "📋 Instances Apptainer en cours d'exécution :"
apptainer instance list

# Arrêter Ollama avec la méthode directe
echo "🔄 Arrêt d'Ollama (méthode directe)..."
if [ -f "${HOME}/apptainer_data/ollama_data/ollama.pid" ]; then
    OLLAMA_PID=$(cat "${HOME}/apptainer_data/ollama_data/ollama.pid")
    echo "   Arrêt du processus Ollama (PID: $OLLAMA_PID)"
    kill $OLLAMA_PID 2>/dev/null || true
    rm -f "${HOME}/apptainer_data/ollama_data/ollama.pid"
fi

# Arrêter les instances une par une pour un arrêt plus propre
echo "🔄 Arrêt des instances Apptainer..."

echo "🔄 Arrêt du Frontend..."
apptainer instance stop frontend_instance 2>/dev/null || echo "Frontend déjà arrêté"

echo "🔄 Arrêt du Backend..."
apptainer instance stop backend_instance 2>/dev/null || echo "Backend déjà arrêté"

echo "🔄 Arrêt d'Ollama (instance)..."
apptainer instance stop ollama_instance 2>/dev/null || echo "Ollama déjà arrêté"

echo "🔄 Arrêt de ChromaDB..."
apptainer instance stop chromadb_instance 2>/dev/null || echo "ChromaDB déjà arrêté"

echo "🔄 Arrêt de PostgreSQL..."
apptainer instance stop postgres_instance 2>/dev/null || echo "PostgreSQL déjà arrêté"

# Tuer tous les processus Ollama restants
echo "🔄 Arrêt de tous les processus Ollama restants..."
pkill -f ollama 2>/dev/null || echo "Aucun processus Ollama en cours d'exécution"

# Vérifier qu'aucune instance ne reste
REMAINING=$(apptainer instance list | grep -c "uqar" || true)
if [ $REMAINING -gt 0 ]; then
    echo "⚠️ Certaines instances n'ont pas été arrêtées proprement."
    echo "🔄 Arrêt forcé de toutes les instances restantes..."
    apptainer instance stop --all
fi

echo ""
echo "✅ Tous les services ont été arrêtés !"
echo ""
echo "Pour redémarrer les services, exécutez: ./start-apptainer.sh" 