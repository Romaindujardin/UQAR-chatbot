#!/bin/bash

# Script de démarrage pour l'Assistant Éducatif UQAR avec Apptainer
# Remplace Docker/Docker Compose par Apptainer

set -e

echo "🚀 Démarrage de l'Assistant Éducatif UQAR (Apptainer)"
echo "===================================================="

# Vérifier que Apptainer est installé
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer n'est pas installé. Veuillez l'installer avant de continuer."
    echo "💡 Installation: https://apptainer.org/docs/admin/main/installation.html"
    exit 1
fi

# Configurer les variables d'environnement Apptainer pour éviter les erreurs d'espace disque
export APPTAINER_CACHEDIR="${HOME}/.apptainer/cache"
export APPTAINER_TMPDIR="${HOME}/.apptainer/tmp"
mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"

# Créer les dossiers nécessaires pour les données persistantes
echo "📁 Création des dossiers nécessaires..."
mkdir -p "${HOME}/apptainer_data/postgres_data"
mkdir -p "${HOME}/apptainer_data/chromadb_data"
mkdir -p "${HOME}/apptainer_data/ollama_data"
mkdir -p "${HOME}/apptainer_data/uploads"
mkdir -p "${HOME}/apptainer_data/logs"

# Créer les dossiers dans le projet
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p backend/chroma_data

# Copier le fichier d'environnement s'il n'existe pas
if [ ! -f backend/.env ]; then
    echo "📝 Création du fichier .env..."
    cp backend/env.example backend/.env
    
    # Mise à jour des URLs de connexion pour Apptainer
    sed -i 's/DATABASE_URL=.*/DATABASE_URL=postgresql:\/\/uqar_user:uqar_password@localhost:5432\/uqar_db/' backend/.env
    sed -i 's/CHROMA_HOST=.*/CHROMA_HOST=localhost/' backend/.env
    sed -i 's/OLLAMA_HOST=.*/OLLAMA_HOST=localhost/' backend/.env
    
    echo "⚠️  N'oubliez pas de vérifier les variables d'environnement dans backend/.env"
fi

# Vérifier les ports disponibles
echo "🔍 Vérification des ports..."
for PORT in 3000 8000 5432 8001 11434; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Le port $PORT est déjà utilisé"
    fi
done

# Construire les images Apptainer
echo "🔨 Construction des images Apptainer..."

echo "🔄 Construction de l'image PostgreSQL..."
apptainer build --ignore-fakeroot-command postgres.sif postgres.def

echo "🔄 Construction de l'image ChromaDB..."
apptainer build --ignore-fakeroot-command chromadb.sif chromadb.def

echo "🔄 Construction de l'image Backend..."
cd backend
apptainer build --ignore-fakeroot-command ../backend.sif backend.def
cd ..

echo "🔄 Construction de l'image Frontend..."
cd frontend
apptainer build --ignore-fakeroot-command ../frontend.sif frontend.def
cd ..

# Démarrer les services
echo "🚀 Démarrage des services..."

# Démarrer PostgreSQL
echo "🔄 Démarrage de PostgreSQL..."
apptainer instance start \
    --bind "${HOME}/apptainer_data/postgres_data:/var/lib/postgresql/data" \
    postgres.sif postgres_instance

# Démarrer ChromaDB
echo "🔄 Démarrage de ChromaDB..."
apptainer instance start \
    --bind "${HOME}/apptainer_data/chromadb_data:/chroma/chroma" \
    chromadb.sif chromadb_instance

# Démarrer Ollama avec méthode directe (plus fiable)
echo "🔄 Démarrage d'Ollama avec support GPU..."

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
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=11434 nohup apptainer run --nv \
    --bind "${HOME}/apptainer_data/ollama_data:/root/.ollama" \
    docker://ollama/ollama:latest > "${HOME}/apptainer_data/logs/ollama.log" 2>&1 &

# Sauvegarder le PID pour arrêt ultérieur
echo $! > "${HOME}/apptainer_data/ollama_data/ollama.pid"
echo "⏳ Ollama démarré avec PID: $!"

# Attendre que les services de base soient prêts
echo "⏳ Attente du démarrage des services de base..."
sleep 10

# Vérifier si Ollama est prêt
echo "🔍 Vérification d'Ollama..."
if curl -s --connect-timeout 5 http://localhost:11434/api/version >/dev/null; then
    echo "✅ Ollama prêt"
    # Vérifier modèle
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:70b"; then
        echo "✅ Modèle llama3.1:70b disponible"
    else 
        echo "⚠️ Modèle llama3.1:70b non trouvé"
    fi
else
    echo "⚠️ Ollama n'est pas prêt, vérifiez les logs: ${HOME}/apptainer_data/logs/ollama.log"
fi

# Démarrer le Backend
echo "🔄 Démarrage du Backend..."
apptainer instance start \
    --bind "./backend:/app" \
    --bind "${HOME}/apptainer_data/uploads:/app/uploads" \
    --bind "${HOME}/apptainer_data/logs:/app/logs" \
    --env "DATABASE_URL=postgresql://uqar_user:uqar_password@localhost:5432/uqar_db" \
    --env "CHROMA_HOST=localhost" \
    --env "CHROMA_PORT=8001" \
    --env "OLLAMA_HOST=localhost" \
    --env "OLLAMA_PORT=11434" \
    --env "OLLAMA_MODEL=llama3.1:70b" \
    --env "JWT_SECRET_KEY=af477b8d25c0527311f097b7098bf98c60b34a6030294231574358ee4ecf4822" \
    --env "DEBUG=true" \
    backend.sif backend_instance

# Démarrer le Frontend
echo "🔄 Démarrage du Frontend..."
apptainer instance start \
    --bind "./frontend:/app" \
    --env "NEXT_PUBLIC_API_URL=http://localhost:8080" \
    frontend.sif frontend_instance

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
echo "   Voir les instances:      apptainer instance list"
echo "   Vérifier le GPU:         nvidia-smi"
echo "   Voir les logs (backend): apptainer instance logs backend_instance"
echo "   Voir logs Ollama:        cat ${HOME}/apptainer_data/logs/ollama.log"
echo "   Arrêter un service:      apptainer instance stop <nom_instance>"
echo "   Arrêter tout:            ./stop-all.sh"
echo "   Shell dans un service:   apptainer shell instance://<nom_instance>"
echo ""
echo "⏳ Les services peuvent prendre quelques minutes à être complètement opérationnels."
echo ""
echo "🎓 Bon apprentissage avec l'Assistant Éducatif UQAR!" 