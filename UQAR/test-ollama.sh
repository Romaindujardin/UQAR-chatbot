#!/bin/bash

# Script pour tester l'état d'Ollama

echo "🔍 Vérification d'Ollama..."

# Vérifier si le processus Ollama est en cours d'exécution
if [ -f "${HOME}/apptainer_data/ollama_data/ollama.pid" ]; then
    OLLAMA_PID=$(cat "${HOME}/apptainer_data/ollama_data/ollama.pid")
    if ps -p $OLLAMA_PID > /dev/null; then
        echo "✅ Processus Ollama en cours d'exécution (PID: $OLLAMA_PID)"
    else
        echo "❌ PID $OLLAMA_PID existe mais le processus n'est pas actif"
    fi
else
    echo "❌ Fichier PID non trouvé"
fi

# Vérifier si le port est ouvert
if ss -tuln | grep -q ":11434 "; then
    echo "✅ Port 11434 est ouvert"
else
    echo "❌ Port 11434 n'est pas ouvert"
fi

# Vérifier l'API Ollama
if curl -s --connect-timeout 5 http://localhost:11434/api/version > /dev/null; then
    VERSION=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*' | cut -d'"' -f4)
    echo "✅ API Ollama répond (version: $VERSION)"
    
    # Vérifier les modèles disponibles
    echo "📋 Modèles disponibles:"
    curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*' | cut -d'"' -f4 | sort | uniq | while read model; do
        echo "   - $model"
    done
    
    # Tester un prompt rapide
    echo -e "\n🤖 Test de génération:"
    echo "Prompt: \"Bonjour, comment vas-tu?\""
    RESPONSE=$(curl -s http://localhost:11434/api/generate -d '{"model": "llama3.1:70b", "prompt": "Bonjour, comment vas-tu?", "stream": false}' | grep -o '"response":"[^"]*' | cut -d'"' -f4)
    echo -e "Réponse: \"${RESPONSE:0:100}...\""
    
    # Vérifier la configuration du backend
    if [ -f "${HOME}/UQAR/backend/app/core/config.py" ]; then
        BACKEND_PORT=$(grep "OLLAMA_PORT" "${HOME}/UQAR/backend/app/core/config.py" | grep -o "11[0-9]*")
        BACKEND_MODEL=$(grep "OLLAMA_MODEL" "${HOME}/UQAR/backend/app/core/config.py" | grep -o '"[^"]*"' | tr -d '"')
        echo "ℹ️ Configuration backend: Port=$BACKEND_PORT, Modèle=$BACKEND_MODEL"
        
        if [ "$BACKEND_PORT" != "11434" ]; then
            echo "⚠️ Le port du backend ($BACKEND_PORT) ne correspond pas au port d'Ollama (11434)"
        fi
    fi
else
    echo "❌ API Ollama ne répond pas"
    echo "📝 Vérifiez les logs: ${HOME}/apptainer_data/logs/ollama.log"
fi

echo -e "\n💡 Commandes utiles:"
echo "   Démarrer Ollama:  ./start-ollama-direct.sh"
echo "   Arrêter Ollama:   ./stop-ollama-direct.sh"
echo "   Logs Ollama:      cat ${HOME}/apptainer_data/logs/ollama.log" 