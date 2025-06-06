#!/bin/bash

# Script pour démarrer uniquement PostgreSQL

set -e
PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Démarrage de PostgreSQL pour l'Assistant Éducatif UQAR"
echo "=========================================================="

# Configurer les variables d'environnement Apptainer
export APPTAINER_CACHEDIR="${HOME}/.apptainer/cache"
export APPTAINER_TMPDIR="${HOME}/.apptainer/tmp"
mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"

# Créer les dossiers nécessaires pour PostgreSQL
echo "📁 Création des dossiers PostgreSQL..."
kdir -p "${PROJET_ROOT}/apptainer_data/postgres_data"
mkdir -p "${PROJET_ROOT}/apptainer_data/postgres_conf"
mkdir -p "${PROJET_ROOT}/apptainer_data/postgres_run"

# Configurer PostgreSQL pour écouter sur toutes les interfaces et le port par défaut
echo "🔧 Configuration de PostgreSQL..."
cat > "${PROJET_ROOT}/apptainer_data/postgres_conf/postgresql.conf" << EOL
listen_addresses = '*'
port = 5432
EOL

# Vérifier si le port est disponible
echo "🔍 Vérification du port 5432..."
if ss -tuln | grep -q ":5432 "; then
    echo "⚠️  Le port 5432 est déjà utilisé"
    echo "   Tentative d'arrêt des instances existantes..."
    apptainer instance stop postgres_instance >/dev/null 2>&1 || true
    sleep 2
    if ss -tuln | grep -q ":5432 "; then
        echo "❌ Le port 5432 est toujours utilisé par un autre processus"
        exit 1
    fi
fi

# Démarrer PostgreSQL
echo "🔄 Démarrage de PostgreSQL..."
apptainer instance stop postgres_instance >/dev/null 2>&1 || true
apptainer instance start \
    --bind "${PROJET_ROOT}/apptainer_data/postgres_data:/var/lib/postgresql/data" \
    --bind "${PROJET_ROOT}/apptainer_data/postgres_conf:/etc/postgresql" \
    --env "POSTGRES_USER=uqar_user" \
    --env "POSTGRES_PASSWORD=uqar_password" \
    --env "POSTGRES_DB=uqar_db" \
    --env "POSTGRES_HOST_AUTH_METHOD=trust" \
    docker://postgres:15 postgres_instance

echo "⏳ Attente du démarrage de PostgreSQL..."
sleep 10

# Vérifier si PostgreSQL est en cours d'exécution
echo "🔍 Vérification du statut de PostgreSQL..."
if apptainer exec instance://postgres_instance pg_isready -h localhost -U uqar_user; then
    echo "✅ PostgreSQL est en cours d'exécution sur le port 5432"
    echo "   Base de données: uqar_db"
    echo "   Utilisateur: uqar_user"
    echo "   Mot de passe: uqar_password"
    
    # Vérifier la connexion à la base de données
    echo "🔍 Test de connexion à la base de données..."
    if apptainer exec instance://postgres_instance psql -h localhost -U uqar_user -d uqar_db -c "SELECT version();" > /dev/null 2>&1; then
        echo "✅ Connexion à la base de données réussie"
    else
        echo "⚠️  Connexion à la base de données échouée, mais le serveur est en cours d'exécution"
    fi
else
    echo "❌ PostgreSQL n'a pas pu démarrer correctement"
    echo "   Vérifiez les journaux pour plus d'informations"
    apptainer instance stop postgres_instance
    exit 1
fi

echo ""
echo "💡 Pour arrêter PostgreSQL : apptainer instance stop postgres_instance"
echo "" 