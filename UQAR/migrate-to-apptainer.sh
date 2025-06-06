#!/bin/bash

# Script de migration de Docker vers Apptainer pour UQAR
# Ce script arrête les services Docker, sauvegarde les données et configure Apptainer

set -e
PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Migration de Docker vers Apptainer pour UQAR"
echo "=============================================="

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Rien à migrer."
else
    echo "🔍 Docker détecté. Vérification des conteneurs en cours d'exécution..."
    
    # Vérifier si des conteneurs UQAR sont en cours d'exécution
    RUNNING_CONTAINERS=$(docker ps --filter "name=uqar_" -q | wc -l)
    
    if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
        echo "🛑 Arrêt des conteneurs Docker UQAR..."
        docker-compose down || echo "⚠️ Impossible d'arrêter proprement avec docker-compose. Tentative alternative..."
        docker stop $(docker ps --filter "name=uqar_" -q) || echo "⚠️ Problème lors de l'arrêt des conteneurs."
    else
        echo "✅ Aucun conteneur UQAR en cours d'exécution."
    fi
    
    # Sauvegarder les données des volumes Docker si présents
    echo "💾 Sauvegarde des données Docker..."
    
    # PostgreSQL
    if docker volume inspect uqar_postgres_data &>/dev/null; then
        echo "  - Sauvegarde des données PostgreSQL..."
        mkdir -p docker_data_backup/postgres
        docker run --rm -v uqar_postgres_data:/data -v $(pwd)/docker_data_backup/postgres:/backup \
            alpine sh -c "cd /data && tar cf /backup/postgres_data.tar ."
    fi
    
    # ChromaDB
    if docker volume inspect uqar_chromadb_data &>/dev/null; then
        echo "  - Sauvegarde des données ChromaDB..."
        mkdir -p docker_data_backup/chromadb
        docker run --rm -v uqar_chromadb_data:/data -v $(pwd)/docker_data_backup/chromadb:/backup \
            alpine sh -c "cd /data && tar cf /backup/chromadb_data.tar ."
    fi
    
    # Ollama
    if docker volume inspect uqar_ollama_data &>/dev/null; then
        echo "  - Sauvegarde des données Ollama..."
        mkdir -p docker_data_backup/ollama
        docker run --rm -v uqar_ollama_data:/data -v $(pwd)/docker_data_backup/ollama:/backup \
            alpine sh -c "cd /data && tar cf /backup/ollama_data.tar ."
    fi
    
    # Uploads
    if docker volume inspect uqar_uploaded_files &>/dev/null; then
        echo "  - Sauvegarde des fichiers uploadés..."
        mkdir -p docker_data_backup/uploads
        docker run --rm -v uqar_uploaded_files:/data -v $(pwd)/docker_data_backup/uploads:/backup \
            alpine sh -c "cd /data && tar cf /backup/uploaded_files.tar ."
    fi
    
    echo "✅ Sauvegarde des données Docker terminée dans docker_data_backup/"
fi

# Installer Apptainer si nécessaire
if ! command -v apptainer &> /dev/null; then
    echo "🔄 Installation d'Apptainer..."
    chmod +x install-apptainer.sh
    ./install-apptainer.sh
else
    APPTAINER_VERSION=$(apptainer --version | awk '{print $3}')
    echo "✅ Apptainer est déjà installé (version $APPTAINER_VERSION)"
fi

# Créer les répertoires pour Apptainer
echo "📁 Création des répertoires Apptainer..."
mkdir -p "${PROJET_ROOT}/apptainer_data/postgres_data"
mkdir -p "${PROJET_ROOT}/apptainer_data/chromadb_data" 
mkdir -p "${PROJET_ROOT}/apptainer_data/ollama_data"
mkdir -p "${PROJET_ROOT}/apptainer_data/uploads"
mkdir -p "${PROJET_ROOT}/apptainer_data/logs"

# Restaurer les données Docker si disponibles
echo "🔄 Restauration des données Docker vers Apptainer..."

# PostgreSQL
if [ -f docker_data_backup/postgres/postgres_data.tar ]; then
    echo "  - Restauration des données PostgreSQL..."
    tar -xf docker_data_backup/postgres/postgres_data.tar -C "${PROJET_ROOT}/apptainer_data/postgres_data"
fi

# ChromaDB
if [ -f docker_data_backup/chromadb/chromadb_data.tar ]; then
    echo "  - Restauration des données ChromaDB..."
    tar -xf docker_data_backup/chromadb/chromadb_data.tar -C "${PROJET_ROOT}/apptainer_data/chromadb_data"
fi

# Ollama
if [ -f docker_data_backup/ollama/ollama_data.tar ]; then
    echo "  - Restauration des données Ollama..."
    tar -xf docker_data_backup/ollama/ollama_data.tar -C "${PROJET_ROOT}/apptainer_data/ollama_data"
fi

# Uploads
if [ -f docker_data_backup/uploads/uploaded_files.tar ]; then
    echo "  - Restauration des fichiers uploadés..."
    tar -xf docker_data_backup/uploads/uploaded_files.tar -C "${PROJET_ROOT}/apptainer_data/uploads"
fi

# Ajuster les permissions
echo "🔄 Ajustement des permissions..."
chmod -R 755 "${PROJET_ROOT}/apptainer_data"

echo ""
echo "✅ Migration terminée !"
echo ""
echo "📝 Étapes suivantes :"
echo "  1. Démarrer les services avec : ./start-apptainer.sh"
echo "  2. Vérifier que tout fonctionne correctement"
echo "  3. Consulter APPTAINER.md pour plus d'informations"
echo ""
echo "⚠️ Si vous rencontrez des problèmes, les sauvegardes de vos données Docker"
echo "   sont disponibles dans le dossier docker_data_backup/"
echo ""
echo "🎓 Bon apprentissage avec l'Assistant Éducatif UQAR !" 