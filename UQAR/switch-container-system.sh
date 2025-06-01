#!/bin/bash

# Script pour basculer entre Docker et Apptainer
# Usage: ./switch-container-system.sh [docker|apptainer]

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [docker|apptainer]"
    echo "Exemple: $0 apptainer"
    exit 1
fi

SYSTEM=$1

if [ "$SYSTEM" != "docker" ] && [ "$SYSTEM" != "apptainer" ]; then
    echo "Erreur: Le système doit être 'docker' ou 'apptainer'"
    exit 1
fi

echo "🔄 Basculement vers $SYSTEM..."

# Arrêter les services en cours
if [ "$SYSTEM" = "docker" ]; then
    # Arrêter Apptainer si en cours d'exécution
    if command -v apptainer &> /dev/null && apptainer instance list | grep -q "instance"; then
        echo "🛑 Arrêt des instances Apptainer..."
        ./stop-apptainer.sh
    fi
else
    # Arrêter Docker si en cours d'exécution
    if command -v docker &> /dev/null && docker ps --filter "name=uqar_" -q | grep -q "."; then
        echo "🛑 Arrêt des conteneurs Docker..."
        docker-compose down || docker stop $(docker ps --filter "name=uqar_" -q)
    fi
fi

# Changer le lien symbolique pour start.sh
if [ -L start.sh ]; then
    rm start.sh
fi

if [ "$SYSTEM" = "docker" ]; then
    echo "🔗 Configuration de start.sh pour utiliser Docker..."
    ln -s start-docker.sh start.sh
    echo "✅ Basculement vers Docker terminé !"
    echo ""
    echo "Pour démarrer les services Docker, exécutez :"
    echo "  ./start.sh"
else
    echo "🔗 Configuration de start.sh pour utiliser Apptainer..."
    ln -s start-apptainer.sh start.sh
    echo "✅ Basculement vers Apptainer terminé !"
    echo ""
    echo "Pour démarrer les services Apptainer, exécutez :"
    echo "  ./start.sh"
fi

echo ""
echo "ℹ️  Note: Si vous basculez fréquemment entre les deux systèmes,"
echo "   pensez à migrer vos données avec migrate-to-apptainer.sh" 