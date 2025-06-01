#!/bin/bash

# Script d'arrêt minimal pour l'Assistant Éducatif UQAR
# Arrête les services démarrés par start-minimal.sh

echo "🛑 Arrêt des services UQAR"
echo "========================"

# Arrêter le frontend
echo "🔄 Arrêt du Frontend..."
pkill -f "node.*dev" || echo "Frontend déjà arrêté"

# Arrêter le backend
echo "🔄 Arrêt du Backend..."
pkill -f "uvicorn app.main:app" || echo "Backend déjà arrêté"

# Arrêter PostgreSQL
echo "🔄 Arrêt de PostgreSQL..."
if command -v pg_ctl &> /dev/null; then
    pg_ctl -D "${HOME}/uqar_data/postgres" stop -m fast || echo "PostgreSQL déjà arrêté"
else
    echo "PostgreSQL n'est pas installé"
fi

echo ""
echo "✅ Tous les services ont été arrêtés"
echo ""
echo "Pour redémarrer les services, exécutez : ./start-minimal.sh" 