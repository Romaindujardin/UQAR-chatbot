#!/bin/bash

# Script de démarrage pour l'Assistant Éducatif UQAR
# Optimisé pour macOS avec Apple Silicon (M1/M2)

set -e

echo "🚀 Démarrage de l'Assistant Éducatif UQAR"
echo "========================================"
echo "🍎 Optimisé pour macOS Apple Silicon"

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer avant de continuer."
    echo "💡 Téléchargez Docker Desktop pour Mac: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Vérifier que Docker Desktop est en cours d'exécution
if ! docker info &> /dev/null; then
    echo "❌ Docker Desktop n'est pas en cours d'exécution."
    echo "💡 Lancez Docker Desktop depuis vos Applications"
    exit 1
fi

# Créer les dossiers nécessaires
echo "📁 Création des dossiers nécessaires..."
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p backend/chroma_data

# Copier le fichier d'environnement s'il n'existe pas
if [ ! -f backend/.env ]; then
    echo "📝 Création du fichier .env..."
    cp backend/env.example backend/.env
    echo "⚠️  N'oubliez pas de modifier les variables d'environnement dans backend/.env"
fi

# Vérifier les ports disponibles (macOS)
echo "🔍 Vérification des ports..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Le port 3000 est déjà utilisé (Frontend)"
fi

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Le port 8000 est déjà utilisé (Backend)"
fi

if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Le port 5432 est déjà utilisé (PostgreSQL)"
fi

if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Le port 8001 est déjà utilisé (ChromaDB)"
fi

if lsof -Pi :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Le port 11434 est déjà utilisé (Ollama)"
fi

# Construire et démarrer les services
echo "🔨 Construction et démarrage des services..."
echo "⏳ Le téléchargement du modèle LLaMA 3.1 8B peut prendre 5-10 minutes..."
docker-compose up --build -d

echo ""
echo "✅ Services démarrés avec succès !"
echo ""
echo "🌐 Accès aux services :"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Docs API:    http://localhost:8000/docs"
echo "   PostgreSQL:  localhost:5432"
echo "   ChromaDB:    http://localhost:8001"
echo "   Ollama:      http://localhost:11434"
echo ""
echo "📋 Commandes utiles :"
echo "   Voir les logs:        docker-compose logs -f"
echo "   Arrêter les services: docker-compose down"
echo "   Redémarrer:          docker-compose restart"
echo "   Logs Ollama:         docker-compose logs -f ollama"
echo ""
echo "⏳ Les services peuvent prendre quelques minutes à être complètement opérationnels."
echo "   Le modèle LLaMA 3.1 8B (4.7GB) se télécharge automatiquement au premier démarrage."
echo ""
echo "🍎 Optimisé pour Apple Silicon - Performances excellentes sur M1/M2 !"
echo "🎓 Bon apprentissage avec l'Assistant Éducatif UQAR !" 