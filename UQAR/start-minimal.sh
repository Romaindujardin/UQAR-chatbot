#!/bin/bash

# Script de démarrage minimal pour l'Assistant Éducatif UQAR
# Cette version évite complètement les constructions de conteneurs
# et utilise des commandes directes

set -e

echo "🚀 Démarrage minimal de l'Assistant Éducatif UQAR"
echo "=============================================="

# Créer les dossiers nécessaires
echo "📁 Création des dossiers nécessaires..."
mkdir -p "${HOME}/uqar_data/postgres"
mkdir -p "${HOME}/uqar_data/chromadb"
mkdir -p "${HOME}/uqar_data/ollama"
mkdir -p "${HOME}/uqar_data/uploads"
mkdir -p "${HOME}/uqar_data/logs"

# Créer les dossiers dans le projet
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p backend/chroma_data

# Vérifier les ports disponibles
echo "🔍 Vérification des ports..."
for PORT in 3000 8000 5432 8001 11434; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Le port $PORT est déjà utilisé"
    fi
done

# Installer les dépendances du backend
echo "🔄 Installation des dépendances du backend..."
cd backend
pip3 install -r requirements.txt
cd ..

# Installer les dépendances du frontend
echo "🔄 Installation des dépendances du frontend..."
cd frontend
npm install
cd ..

# Démarrer les services
echo "🚀 Démarrage des services..."

# Démarrer PostgreSQL (utilisation de la commande système plutôt qu'un conteneur)
echo "🔄 Démarrage de PostgreSQL..."
if command -v postgres &> /dev/null; then
    if ! pg_isready -h localhost -p 5432 &> /dev/null; then
        # Initialiser la base de données si nécessaire
        if [ ! -f "${HOME}/uqar_data/postgres/PG_VERSION" ]; then
            echo "Initialisation de la base de données PostgreSQL..."
            pg_ctl initdb -D "${HOME}/uqar_data/postgres"
        fi
        
        # Démarrer PostgreSQL
        pg_ctl -D "${HOME}/uqar_data/postgres" -l "${HOME}/uqar_data/logs/postgres.log" start || true
        
        # Créer la base de données et l'utilisateur si nécessaire
        if ! psql -c '\l' | grep -q uqar_db; then
            createdb uqar_db
            psql -c "CREATE USER uqar_user WITH PASSWORD 'uqar_password' SUPERUSER;"
            psql -d uqar_db -f backend/init.sql || true
        fi
    else
        echo "PostgreSQL est déjà en cours d'exécution"
    fi
else
    echo "⚠️ PostgreSQL n'est pas installé sur le système"
    echo "Veuillez l'installer avec: sudo apt-get install postgresql"
fi

# Démarrer le backend
echo "🔄 Démarrage du backend..."
cd backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "${HOME}/uqar_data/logs/backend.log" 2>&1 &
cd ..

# Démarrer le frontend
echo "🔄 Démarrage du frontend..."
cd frontend
nohup npm run dev > "${HOME}/uqar_data/logs/frontend.log" 2>&1 &
cd ..

echo ""
echo "✅ Services démarrés avec succès !"
echo ""
echo "🌐 Accès aux services :"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Docs API:    http://localhost:8000/docs"
echo "   PostgreSQL:  localhost:5432"
echo ""
echo "📋 Pour voir les logs :"
echo "   Backend:    tail -f ${HOME}/uqar_data/logs/backend.log"
echo "   Frontend:   tail -f ${HOME}/uqar_data/logs/frontend.log"
echo "   PostgreSQL: tail -f ${HOME}/uqar_data/logs/postgres.log"
echo ""
echo "🛑 Pour arrêter les services :"
echo "   ./stop-minimal.sh"
echo ""
echo "🎓 Bon apprentissage avec l'Assistant Éducatif UQAR !" 