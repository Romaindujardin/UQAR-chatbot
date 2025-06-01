#!/bin/bash

# Script pour arrêter tous les services

echo "🛑 Arrêt complet de tous les services..."

# Arrêter toutes les instances Apptainer
echo "🔄 Arrêt de toutes les instances Apptainer..."
apptainer instance list | awk '{if(NR>1)print $1}' | xargs -I{} apptainer instance stop {} || echo "Aucune instance Apptainer en cours d'exécution"

# Tuer tous les processus Ollama
echo "🔄 Arrêt de tous les processus Ollama..."
pkill -f ollama 2>/dev/null || echo "Aucun processus Ollama en cours d'exécution"

# Vérifier les ports utilisés par les services
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

echo "✅ Arrêt de tous les services terminé" 