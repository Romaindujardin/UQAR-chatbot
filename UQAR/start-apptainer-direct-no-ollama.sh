#!/bin/bash

# Script de démarrage pour l'Assistant Éducatif UQAR avec Apptainer
# Version simplifiée qui évite les problèmes de fakeroot et n'essaie pas de démarrer Ollama

set -e

echo "🚀 Démarrage de l'Assistant Éducatif UQAR (Apptainer Direct Sans Ollama)"
echo "=========================================================="

# Vérifier que Apptainer est installé
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer n'est pas installé. Veuillez l'installer avant de continuer."
    echo "💡 Installation: https://apptainer.org/docs/admin/main/installation.html"
    exit 1
fi

# Définir les chemins du projet
PROJET_ROOT="${HOME}/UQAR_GIT"
UQAR_DIR="${PROJET_ROOT}/UQAR"
BACKEND_DIR="${UQAR_DIR}/backend"
FRONTEND_DIR="${UQAR_DIR}/frontend"

# Configurer les variables d'environnement Apptainer pour éviter les erreurs d'espace disque
export APPTAINER_CACHEDIR="${HOME}/.apptainer/cache"
export APPTAINER_TMPDIR="${HOME}/.apptainer/tmp"
mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"

# Créer les dossiers nécessaires pour les données persistantes
echo "📁 Création des dossiers nécessaires..."
mkdir -p "${HOME}/apptainer_data/postgres_data"
mkdir -p "${HOME}/apptainer_data/postgres_conf"
mkdir -p "${HOME}/apptainer_data/postgres_run"
mkdir -p "${HOME}/apptainer_data/chromadb_data"
mkdir -p "${HOME}/apptainer_data/uploads"
mkdir -p "${HOME}/apptainer_data/logs"

# Créer les dossiers dans le projet
mkdir -p "${BACKEND_DIR}/logs"
mkdir -p "${BACKEND_DIR}/uploads"
mkdir -p "${BACKEND_DIR}/chroma_data"

# Définir l'adresse IP de l'hôte pour les communications inter-conteneurs
HOST_IP="10.0.30.51"
echo "🔧 Utilisation de l'adresse IP $HOST_IP pour les communications entre services"

# Vérifier les ports disponibles
echo "🔍 Vérification des ports..."
for PORT in 3000 8000 38705 8001; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Le port $PORT est déjà utilisé"
    fi
done

# Vérifier si Ollama est accessible
echo "🔍 Vérification de l'accès à Ollama..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama est accessible sur le port 11434"
else
    echo "⚠️  Ollama n'est pas accessible sur le port 11434. L'application pourrait ne pas fonctionner correctement."
fi

# Démarrer les services en utilisant directement les images Docker
echo "🚀 Démarrage des services avec Apptainer en mode direct..."

# Créer un fichier postgresql.conf temporaire pour écouter sur toutes les interfaces
TEMP_PG_CONF="${HOME}/apptainer_data/postgres_conf/postgresql.conf"
echo "listen_addresses = '*'" > "${TEMP_PG_CONF}"
echo "port = 38705" >> "${TEMP_PG_CONF}"
echo "unix_socket_directories = '/tmp'" >> "${TEMP_PG_CONF}"

# Démarrer PostgreSQL
echo "🔄 Démarrage de PostgreSQL..."
apptainer instance start \
    --bind "${HOME}/apptainer_data/postgres_data:/var/lib/postgresql/data" \
    --bind "${HOME}/apptainer_data/postgres_conf:/etc/postgresql" \
    --bind "${HOME}/apptainer_data/postgres_run:/var/run/postgresql" \
    --env "POSTGRES_USER=dujr0001" \
    --env "POSTGRES_PASSWORD=URJvSIG0fm" \
    --env "POSTGRES_DB=uqar_db" \
    --env "POSTGRES_HOST_AUTH_METHOD=trust" \
    --env "PGPORT=38705" \
    docker://postgres:15 postgres_instance

# Démarrer ChromaDB
echo "🔄 Démarrage de ChromaDB..."
apptainer instance start \
    --env "CHROMA_SERVER_HOST=0.0.0.0" \
    --env "CHROMA_SERVER_HTTP_PORT=8001" \
    --bind "${HOME}/apptainer_data/chromadb_data:/chroma/chroma" \
    docker://chromadb/chroma:latest chromadb_instance

# Attendre que les services de base soient prêts
echo "⏳ Attente du démarrage des services de base..."
sleep 10

# Créer un résolveur DNS personnalisé
echo "🔄 Configuration des hosts pour la communication entre conteneurs..."
HOSTS_FILE="${HOME}/apptainer_data/hosts"
echo "127.0.0.1 localhost" > "${HOSTS_FILE}"
echo "$HOST_IP postgres_host" >> "${HOSTS_FILE}"
echo "$HOST_IP chroma_host" >> "${HOSTS_FILE}"
echo "$HOST_IP ollama_host" >> "${HOSTS_FILE}"

# Démarrer le Backend - nous créons une image Python de base et montons le code
echo "🔄 Démarrage du Backend..."
apptainer instance start \
    --bind "${BACKEND_DIR}:/app" \
    --bind "${HOME}/apptainer_data/uploads:/app/uploads" \
    --bind "${HOME}/apptainer_data/logs:/app/logs" \
    --bind "${HOSTS_FILE}:/etc/hosts" \
    --env "PYTHONDONTWRITEBYTECODE=1" \
    --env "PYTHONUNBUFFERED=1" \
    --env "PYTHONPATH=/app" \
    --env "DATABASE_URL=postgresql://dujr0001:URJvSIG0fm@$HOST_IP:38705/uqar_db" \
    --env "CHROMA_HOST=$HOST_IP" \
    --env "CHROMA_PORT=8001" \
    --env "OLLAMA_HOST=$HOST_IP" \
    --env "OLLAMA_PORT=11434" \
    --env "OLLAMA_MODEL=tinyllama" \
    --env "JWT_SECRET_KEY=af477b8d25c0527311f097b7098bf98c60b34a6030294231574358ee4ecf4822" \
    --env "DEBUG=true" \
    docker://python:3.11-slim backend_instance

# Installer les dépendances et démarrer l'application backend
echo "🔄 Installation des dépendances backend..."
apptainer exec instance://backend_instance bash -c "cd /app && pip install -r /app/requirements.txt && python -m spacy download fr_core_news_sm"
apptainer exec instance://backend_instance bash -c "cd /app && python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords')\""

# Démarrer l'application backend en arrière-plan
echo "🔄 Démarrage de l'application backend..."
nohup apptainer exec instance://backend_instance bash -c "cd /app && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" > "${HOME}/apptainer_data/logs/backend.log" 2>&1 &

# Démarrer le Frontend
echo "🔄 Démarrage du Frontend..."
apptainer instance start \
    --bind "${FRONTEND_DIR}:/app" \
    --env "NODE_ENV=development" \
    --env "NEXT_TELEMETRY_DISABLED=1" \
    --env "NEXT_PUBLIC_API_URL=http://$HOST_IP:8000" \
    docker://node:18-alpine frontend_instance

# Installer les dépendances et démarrer l'application frontend
echo "🔄 Installation des dépendances frontend..."
apptainer exec instance://frontend_instance sh -c "cd /app && npm install"

# Démarrer l'application frontend en arrière-plan avec -H 0.0.0.0 pour écouter sur toutes les interfaces
echo "🔄 Démarrage de l'application frontend..."
nohup apptainer exec instance://frontend_instance sh -c "cd /app && npm run dev -- -p 3000 -H 0.0.0.0" > "${HOME}/apptainer_data/logs/frontend.log" 2>&1 &

echo ""
echo "✅ Services démarrés avec succès !"
echo ""
echo "🌐 Accès aux services :"
echo "   Frontend:    http://$HOST_IP:3000"
echo "   Backend API: http://$HOST_IP:8000"
echo "   Docs API:    http://$HOST_IP:8000/docs"
echo "   PostgreSQL:  $HOST_IP:38705"
echo "   ChromaDB:    http://$HOST_IP:8001"
echo "   Ollama:      http://$HOST_IP:11434 (service existant)"
echo ""
echo "🌐 Pour accéder depuis votre machine locale, utilisez un tunnel SSH :"
echo "   ssh -L 3000:localhost:3000 -L 8000:localhost:8000 -L 8001:localhost:8001 -L 11434:localhost:11434 dujr0001@srgpu01"
echo "   Puis accédez à http://localhost:3000"
echo ""
echo "📋 Commandes utiles :"
echo "   Voir les instances:      apptainer instance list"
echo "   Vérifier le GPU:         nvidia-smi"
echo "   Voir les logs backend:   tail -f ${HOME}/apptainer_data/logs/backend.log"
echo "   Voir les logs frontend:  tail -f ${HOME}/apptainer_data/logs/frontend.log"
echo "   Arrêter un service:      apptainer instance stop <nom_instance>"
echo "   Arrêter tout:            apptainer instance stop --all"
echo "   Shell dans un service:   apptainer shell instance://<nom_instance>"
echo ""
echo "⏳ Les services peuvent prendre quelques minutes à être complètement opérationnels."
echo ""
echo "🎓 Bon apprentissage avec l'Assistant Éducatif UQAR !"