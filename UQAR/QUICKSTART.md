# 🚀 Guide de Démarrage Rapide - Assistant Éducatif UQAR

## 🔧 Système Linux avec Apptainer/Singularity

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Apptainer/Singularity** (anciennement Singularity) - [Guide d'installation](https://apptainer.org/docs/admin/main/installation.html)
- **Git** pour cloner le projet
- **Pilotes NVIDIA** pour les fonctionnalités GPU
- Au moins **16 GB de RAM** et **20 GB d'espace disque libre**

> ⚠️ Un GPU NVIDIA est fortement recommandé pour des performances optimales

## ⚡ Démarrage en 3 étapes

### 1. Cloner et configurer le projet

```bash
# Cloner le projet
git clone <votre-repo-url>
cd UQAR_GIT

# Exécuter le script de configuration
chmod +x setup-uqar.sh
./setup-uqar.sh
```

Le script de configuration va automatiquement :
- Vérifier les prérequis (Apptainer, pilotes NVIDIA)
- Créer les dossiers nécessaires
- Construire les images Apptainer (.sif) depuis les fichiers de définition (.def)
- Télécharger les données NLTK requises
- Préparer l'environnement pour le démarrage

### 2. Lancer l'application

```bash
# Démarrer tous les services
./run-uqar.sh
```

Le script va automatiquement :
- Démarrer Ollama (et télécharger les modèles nécessaires lors du premier démarrage)
- Démarrer PostgreSQL
- Démarrer ChromaDB
- Démarrer le backend FastAPI
- Démarrer le frontend Next.js

### 3. Accéder à l'application

Une fois tous les services démarrés :

- **Frontend** : http://localhost:3000
- **API Backend** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **ChromaDB** : http://localhost:8001
- **Ollama** : http://localhost:11434

## 👥 Premiers pas

### Créer le premier compte Super-Admin

1. Allez sur http://localhost:3000
2. Cliquez sur "S'inscrire"
3. Remplissez le formulaire en sélectionnant le rôle "Super-Admin"
4. Le compte sera créé en statut "En attente"

### Activer le compte Super-Admin

Comme il n'y a pas encore d'admin pour valider, vous devez activer manuellement le premier compte :

```bash
# Se connecter à la base de données
docker exec -it uqar_postgres psql -U uqar_user -d uqar_db

# Activer le premier utilisateur (remplacez 1 par l'ID correct)
UPDATE users SET status = 'active' WHERE id = 1;
\q
```

### Workflow typique

1. **Super-Admin** :

   - Se connecte et valide les nouveaux comptes enseignants/étudiants
   - Gère les utilisateurs depuis l'interface d'administration

2. **Enseignant** :

   - Crée des sections de cours (ex: "Mathématiques", "Physique")
   - Upload des documents PDF/DOCX dans chaque section
   - Génère et valide des exercices automatiques
   - Surveille l'activité des étudiants

3. **Étudiant** :
   - Accède aux sections de cours disponibles
   - Utilise le chatbot RAG pour poser des questions
   - Fait les exercices validés par les enseignants
   - Consulte ses progrès

## 🔧 Configuration avancée

### Variables d'environnement

Modifiez `backend/.env` pour personnaliser :

```bash
# Sécurité JWT (IMPORTANT en production)
JWT_SECRET_KEY=votre-clé-secrète-très-longue-et-complexe

# Modèle Ollama (autres modèles disponibles)
OLLAMA_MODEL=llama3.1:8b  # ou llama3.1:70b si vous avez 64GB+ RAM

# Limites de fichiers
MAX_FILE_SIZE=104857600  # 100MB
```

### Modèles Ollama disponibles

```bash
# Voir les modèles installés
docker exec -it uqar_ollama ollama list

# Installer d'autres modèles
docker exec -it uqar_ollama ollama pull codellama:7b
docker exec -it uqar_ollama ollama pull mistral:7b
```

## 📊 Monitoring

### Vérifier l'état des services

```bash
# Voir tous les conteneurs
docker-compose ps

# Logs en temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f ollama
```

### Métriques importantes (Apple Silicon)

- **Ollama** : Temps de réponse < 3s pour les requêtes
- **ChromaDB** : Recherche vectorielle < 1s
- **PostgreSQL** : Requêtes < 100ms
- **Frontend** : Chargement initial < 2s

## 🛠️ Commandes utiles

```bash
# Redémarrer un service
docker-compose restart backend

# Reconstruire après modifications
docker-compose up --build

# Arrêter tous les services
docker-compose down

# Nettoyer complètement (ATTENTION: supprime les données)
docker-compose down -v
docker system prune -a

# Interagir directement avec Ollama
docker exec -it uqar_ollama ollama run llama3.1:8b
```

## 🐛 Résolution de problèmes

### Le modèle LLaMA ne se télécharge pas

```bash
# Vérifier les logs Ollama
docker-compose logs ollama

# Télécharger manuellement le modèle
docker exec -it uqar_ollama ollama pull llama3.1:8b

# Redémarrer le service Ollama
docker-compose restart ollama
```

### Erreurs de base de données

```bash
# Recréer la base de données
docker-compose down
docker volume rm uqar_postgres_data
docker-compose up -d postgres
```

### Frontend ne se connecte pas au backend

1. Vérifiez que le backend est démarré : http://localhost:8000/health
2. Vérifiez les CORS dans `backend/.env`
3. Redémarrez le frontend : `docker-compose restart frontend`

### Problèmes de mémoire sur M1

```bash
# Vérifier l'utilisation mémoire
docker stats

# Libérer de la mémoire
docker system prune

# Ajuster la mémoire Docker Desktop (Préférences > Resources)
```

## 📚 Ressources supplémentaires

- **Documentation API** : http://localhost:8000/docs
- **Logs de l'application** : `backend/logs/app.log`
- **Base de données** : Accessible via pgAdmin ou client PostgreSQL
- **ChromaDB** : Interface web sur http://localhost:8001
- **Ollama** : Interface sur http://localhost:11434

## 🎯 Prochaines étapes

1. **Tester le workflow complet** avec un enseignant et un étudiant
2. **Uploader des documents** et tester le RAG
3. **Générer des exercices** et les valider
4. **Optimiser les performances** selon vos besoins
5. **Essayer d'autres modèles** Ollama selon votre RAM

## 🍎 Spécificités Apple Silicon

### Avantages

- **Performance native** sur M1/M2/M3
- **Consommation énergétique optimisée**
- **Pas besoin de GPU externe**
- **Installation simplifiée**

### Modèles recommandés selon votre RAM

- **8-16 GB RAM** : `llama3.1:8b` (4.7GB)
- **32+ GB RAM** : `llama3.1:70b` (40GB)
- **Pour le code** : `codellama:7b` (3.8GB)

---

**Besoin d'aide ?** Consultez les logs avec `docker-compose logs -f` ou créez une issue sur le projet.
