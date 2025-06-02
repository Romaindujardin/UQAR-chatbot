#!/bin/bash

# Script pour vérifier que tout est bien configuré
# Auteur: Claude Sonnett
# Date: 2025-06-02

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🔍 Vérification de l'Assistant Éducatif UQAR dans ${SCRIPT_DIR}"
echo "=============================================================="

# Vérifier que Apptainer est installé
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
else
    APPTAINER_VERSION=$(apptainer --version)
    echo "✅ Apptainer est installé: ${APPTAINER_VERSION}"
fi

# Vérifier les pilotes NVIDIA
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️ Les pilotes NVIDIA ne sont pas détectés. Les performances peuvent être limitées."
else
    NVIDIA_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader)
    echo "✅ Pilotes NVIDIA détectés: ${NVIDIA_VERSION}"
fi

# Vérifier les images Apptainer
echo "🔍 Vérification des images Apptainer..."
if [ -f "${SCRIPT_DIR}/UQAR/chromadb.sif" ]; then
    echo "✅ L'image ChromaDB existe"
else
    echo "❌ L'image ChromaDB est manquante. Exécutez ./setup-uqar.sh"
fi

if [ -f "${SCRIPT_DIR}/UQAR/postgres.sif" ]; then
    echo "✅ L'image PostgreSQL existe"
else
    echo "❌ L'image PostgreSQL est manquante. Exécutez ./setup-uqar.sh"
fi

if [ -f "${SCRIPT_DIR}/UQAR/ollama.sif" ]; then
    echo "✅ L'image Ollama existe"
else
    echo "❌ L'image Ollama est manquante. Exécutez ./setup-uqar.sh"
fi

# Vérifier les dossiers de données
echo "🔍 Vérification des dossiers de données..."
for DIR in "${SCRIPT_DIR}/apptainer_data/logs" "${SCRIPT_DIR}/apptainer_data/ollama_data" \
           "${SCRIPT_DIR}/apptainer_data/chromadb_data" "${SCRIPT_DIR}/apptainer_data/postgres_data" \
           "${SCRIPT_DIR}/apptainer_data/uploads" "${SCRIPT_DIR}/nltk_data"; do
    if [ -d "$DIR" ]; then
        echo "✅ Le dossier $(basename "$DIR") existe"
    else
        echo "❌ Le dossier $(basename "$DIR") est manquant. Exécutez ./setup-uqar.sh"
    fi
done

# Vérifier les données NLTK
echo "🔍 Vérification des données NLTK..."
if [ -d "${SCRIPT_DIR}/nltk_data/tokenizers/punkt" ] && [ -d "${SCRIPT_DIR}/nltk_data/corpora/stopwords" ]; then
    echo "✅ Les données NLTK sont installées"
else
    echo "❌ Les données NLTK sont manquantes. Exécutez ./setup-uqar.sh"
fi

# Vérifier les scripts d'exécution
echo "🔍 Vérification des scripts d'exécution..."
for SCRIPT in "${SCRIPT_DIR}/run-uqar.sh" "${SCRIPT_DIR}/stop-uqar.sh" "${SCRIPT_DIR}/UQAR/start-apptainer-direct-no-ollama.sh"; do
    if [ -x "$SCRIPT" ]; then
        echo "✅ Le script $(basename "$SCRIPT") est exécutable"
    else
        if [ -f "$SCRIPT" ]; then
            echo "⚠️ Le script $(basename "$SCRIPT") existe mais n'est pas exécutable. Exécutez: chmod +x $SCRIPT"
        else
            echo "❌ Le script $(basename "$SCRIPT") est manquant"
        fi
    fi
done

echo ""
echo "📋 Résumé de la vérification:"
if [ -f "${SCRIPT_DIR}/UQAR/chromadb.sif" ] && [ -f "${SCRIPT_DIR}/UQAR/postgres.sif" ] && [ -f "${SCRIPT_DIR}/UQAR/ollama.sif" ] && \
   [ -d "${SCRIPT_DIR}/apptainer_data/logs" ] && [ -d "${SCRIPT_DIR}/apptainer_data/ollama_data" ] && \
   [ -d "${SCRIPT_DIR}/nltk_data/tokenizers/punkt" ] && [ -d "${SCRIPT_DIR}/nltk_data/corpora/stopwords" ] && \
   [ -x "${SCRIPT_DIR}/run-uqar.sh" ] && [ -x "${SCRIPT_DIR}/stop-uqar.sh" ]; then
    echo "✅ L'environnement semble correctement configuré."
    echo ""
    echo "📋 Pour démarrer l'application: ${SCRIPT_DIR}/run-uqar.sh"
else
    echo "⚠️ L'environnement n'est pas complètement configuré."
    echo ""
    echo "📋 Exécutez: ${SCRIPT_DIR}/setup-uqar.sh pour configurer l'environnement"
fi 