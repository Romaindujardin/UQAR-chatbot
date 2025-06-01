#!/bin/bash

# Script de test pour macOS Apple Silicon
# Vérifie que tous les services UQAR fonctionnent correctement

set -e

echo "🧪 Test de l'Assistant Éducatif UQAR sur macOS"
echo "============================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les résultats
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Vérifier que Docker Desktop est en cours d'exécution
echo -e "${BLUE}🔍 Vérification de Docker Desktop...${NC}"
if docker info &> /dev/null; then
    print_result 0 "Docker Desktop est en cours d'exécution"
else
    print_result 1 "Docker Desktop n'est pas en cours d'exécution"
    echo -e "${YELLOW}💡 Lancez Docker Desktop depuis vos Applications${NC}"
    exit 1
fi

# Vérifier que les services sont démarrés
echo -e "${BLUE}🔍 Vérification des conteneurs...${NC}"
containers=("uqar_postgres" "uqar_chromadb" "uqar_ollama" "uqar_backend" "uqar_frontend")

for container in "${containers[@]}"; do
    if docker ps | grep -q "$container"; then
        print_result 0 "Conteneur $container est en cours d'exécution"
    else
        print_result 1 "Conteneur $container n'est pas en cours d'exécution"
    fi
done

# Attendre que les services soient prêts
echo -e "${BLUE}⏳ Attente que les services soient prêts...${NC}"
sleep 10

# Test des endpoints
echo -e "${BLUE}🔍 Test des endpoints...${NC}"

# Test PostgreSQL
if docker exec uqar_postgres pg_isready -U uqar_user &> /dev/null; then
    print_result 0 "PostgreSQL est accessible"
else
    print_result 1 "PostgreSQL n'est pas accessible"
fi

# Test ChromaDB
if curl -s http://localhost:8001/api/v1/heartbeat &> /dev/null; then
    print_result 0 "ChromaDB est accessible"
else
    print_result 1 "ChromaDB n'est pas accessible"
fi

# Test Ollama
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    print_result 0 "Ollama est accessible"
    
    # Vérifier si le modèle est téléchargé
    if docker exec uqar_ollama ollama list | grep -q "llama3.1:8b"; then
        print_result 0 "Modèle LLaMA 3.1 8B est installé"
    else
        print_result 1 "Modèle LLaMA 3.1 8B n'est pas encore installé"
        echo -e "${YELLOW}⏳ Le modèle se télécharge en arrière-plan...${NC}"
    fi
else
    print_result 1 "Ollama n'est pas accessible"
fi

# Test Backend FastAPI
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_result 0 "Backend FastAPI est accessible"
else
    print_result 1 "Backend FastAPI n'est pas accessible"
fi

# Test Frontend Next.js
if curl -s http://localhost:3000 &> /dev/null; then
    print_result 0 "Frontend Next.js est accessible"
else
    print_result 1 "Frontend Next.js n'est pas accessible"
fi

# Test de performance Apple Silicon
echo -e "${BLUE}🍎 Test de performance Apple Silicon...${NC}"

# Vérifier l'architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    print_result 0 "Architecture Apple Silicon détectée ($ARCH)"
else
    print_result 1 "Architecture non-Apple Silicon détectée ($ARCH)"
fi

# Test de mémoire
MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
echo -e "${BLUE}💾 Mémoire disponible: ${MEMORY_GB}GB${NC}"

if [ $MEMORY_GB -ge 8 ]; then
    print_result 0 "Mémoire suffisante pour LLaMA 3.1 8B"
else
    print_result 1 "Mémoire insuffisante (minimum 8GB recommandé)"
fi

# Test simple d'Ollama
echo -e "${BLUE}🤖 Test simple d'Ollama...${NC}"
if docker exec uqar_ollama ollama list | grep -q "llama3.1:8b"; then
    echo -e "${YELLOW}⏳ Test de génération de texte...${NC}"
    
    # Test simple de génération
    RESPONSE=$(docker exec uqar_ollama ollama run llama3.1:8b "Dis bonjour en français" 2>/dev/null | head -1)
    
    if [ ! -z "$RESPONSE" ]; then
        print_result 0 "Génération de texte fonctionne"
        echo -e "${GREEN}📝 Réponse: $RESPONSE${NC}"
    else
        print_result 1 "Génération de texte ne fonctionne pas"
    fi
else
    echo -e "${YELLOW}⏳ Modèle en cours de téléchargement, test ignoré${NC}"
fi

# Résumé
echo ""
echo -e "${BLUE}📊 Résumé du test${NC}"
echo "=================="

# Vérifier les logs pour des erreurs
ERROR_COUNT=$(docker-compose logs --tail=50 2>/dev/null | grep -i error | wc -l)
if [ $ERROR_COUNT -eq 0 ]; then
    print_result 0 "Aucune erreur détectée dans les logs"
else
    print_result 1 "$ERROR_COUNT erreurs détectées dans les logs"
    echo -e "${YELLOW}💡 Consultez les logs avec: docker-compose logs${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Test terminé !${NC}"
echo ""
echo -e "${BLUE}🌐 Accès aux services :${NC}"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Docs API:    http://localhost:8000/docs"
echo ""
echo -e "${BLUE}📋 Commandes utiles :${NC}"
echo "   Logs en temps réel: docker-compose logs -f"
echo "   Arrêter:           docker-compose down"
echo "   Redémarrer:        docker-compose restart"
echo ""
echo -e "${GREEN}🍎 Optimisé pour Apple Silicon M1/M2/M3 !${NC}" 