#!/bin/bash

# Script pour configurer l'Assistant Éducatif UQAR après clonage
# Ce script télécharge et configure tous les éléments nécessaires 
# pour faire fonctionner l'application sans les fichiers .sif
# Auteur: Claude Sonnett
# Date: 2025-06-02

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🔧 Configuration de l'Assistant Éducatif UQAR dans ${SCRIPT_DIR}"
echo "=============================================================="

# Vérifier que Apptainer est installé
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer n'est pas installé. Veuillez l'installer avant de continuer."
    echo "   Consultez: ${SCRIPT_DIR}/UQAR/APPTAINER.md ou exécutez ${SCRIPT_DIR}/UQAR/install-apptainer.sh"
    exit 1
fi

# Vérifier les pilotes NVIDIA
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️ Les pilotes NVIDIA ne semblent pas être installés. Certaines fonctionnalités peuvent ne pas fonctionner correctement."
    read -p "Continuer quand même? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Créer les dossiers nécessaires
mkdir -p "${SCRIPT_DIR}/apptainer_data/logs"
mkdir -p "${SCRIPT_DIR}/apptainer_data/ollama_data"
mkdir -p "${SCRIPT_DIR}/apptainer_data/chromadb_data"
mkdir -p "${SCRIPT_DIR}/apptainer_data/postgres_data"
mkdir -p "${SCRIPT_DIR}/apptainer_data/postgres_run"
mkdir -p "${SCRIPT_DIR}/apptainer_data/uploads"
mkdir -p "${SCRIPT_DIR}/uqar_data/chromadb"
mkdir -p "${SCRIPT_DIR}/uqar_data/postgres"
mkdir -p "${SCRIPT_DIR}/uqar_data/uploads"
mkdir -p "${SCRIPT_DIR}/nltk_data"

# Construire les images Apptainer depuis les fichiers .def
echo "🔄 Construction des images Apptainer..."

cd "${SCRIPT_DIR}/UQAR"

# Construire ChromaDB
if [ ! -f "${SCRIPT_DIR}/UQAR/chromadb.sif" ]; then
    echo "🔄 Construction de l'image ChromaDB..."
    sudo apptainer build chromadb.sif chromadb.def
else
    echo "✅ L'image ChromaDB existe déjà."
fi

# Construire PostgreSQL
if [ ! -f "${SCRIPT_DIR}/UQAR/postgres.sif" ]; then
    echo "🔄 Construction de l'image PostgreSQL..."
    sudo apptainer build postgres.sif postgres.def
else
    echo "✅ L'image PostgreSQL existe déjà."
fi

# Construire Ollama
if [ ! -f "${SCRIPT_DIR}/UQAR/ollama.sif" ]; then
    echo "🔄 Construction de l'image Ollama (peut prendre du temps)..."
    sudo apptainer build ollama.sif ollama.def
else
    echo "✅ L'image Ollama existe déjà."
fi

# Télécharger les données NLTK nécessaires
echo "🔄 Téléchargement des données NLTK..."
python3 -m pip install --user nltk
python3 -c "import nltk; nltk.download('punkt', download_dir='${SCRIPT_DIR}/nltk_data'); nltk.download('stopwords', download_dir='${SCRIPT_DIR}/nltk_data')"

# Rendre les scripts exécutables
chmod +x ${SCRIPT_DIR}/*.sh
chmod +x ${SCRIPT_DIR}/UQAR/*.sh

echo ""
echo "✅ Configuration terminée!"
echo ""
echo "📋 Pour démarrer l'application: ${SCRIPT_DIR}/run-uqar.sh"
echo "📋 Pour arrêter l'application: ${SCRIPT_DIR}/stop-uqar.sh"
echo ""
echo "⚠️ Lors du premier démarrage, Ollama va télécharger les modèles nécessaires (plusieurs GB)."
echo "   Cela peut prendre du temps selon votre connexion Internet." 