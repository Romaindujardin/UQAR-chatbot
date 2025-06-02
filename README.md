# Assistant Éducatif UQAR

Ce dépôt contient le code source et les scripts de déploiement pour l'Assistant Éducatif UQAR.

## Structure du dossier

- `UQAR/` : Code source principal du projet (backend et frontend)
- `apptainer_data/` : Données persistantes pour les conteneurs Apptainer
- `apptainer_sandbox/` : Sandboxes pour les conteneurs Apptainer
- `backend/` : Version légère du backend pour tests
- `uqar_data/` : Données utilisateur (chromadb, postgres, uploads)
- `SCRIPT/` : Scripts individuels pour démarrer/arrêter des services spécifiques

## Scripts principaux

- `setup-uqar.sh` : Script initial pour configurer l'environnement après clonage
- `check-uqar.sh` : Script pour vérifier que l'environnement est correctement configuré
- `run-uqar.sh` : Script principal pour démarrer tous les services
- `stop-uqar.sh` : Script pour arrêter tous les services
- `start-no-ollama.sh` : Script pour démarrer les services sans Ollama

## Prérequis

- Apptainer installé
- NVIDIA GPU avec pilotes installés
- 16 Go de RAM minimum
- 20 Go d'espace disque libre

## Installation après clonage

```bash
# Configurer l'environnement (construction des images, création des dossiers, etc.)
./setup-uqar.sh

# Vérifier que tout est correctement configuré
./check-uqar.sh

# Démarrer l'application
./run-uqar.sh
```

## Démarrage rapide (après configuration)

```bash
# Démarrer l'application complète
./run-uqar.sh

# Arrêter l'application
./stop-uqar.sh
```

## Services

L'application se compose des services suivants :

- **Frontend** : Interface utilisateur (port 3000)
- **Backend** : API REST (port 8000)
- **PostgreSQL** : Base de données (port 38705)
- **ChromaDB** : Base de données vectorielle (port 8001)
- **Ollama** : Modèle de langage local (port 11434)

## Accès aux services

- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- ChromaDB : http://localhost:8001
- Ollama : http://localhost:11434

## Logs

Les logs sont disponibles dans les dossiers suivants :

- Frontend : `apptainer_data/logs/frontend.log`
- Backend : `apptainer_data/logs/backend.log`
- Ollama : `apptainer_data/logs/ollama.log`

## Développement

Pour contribuer au projet, consultez le fichier DEVELOPMENT.md dans le dossier UQAR/.

## Licence

Ce projet est sous licence MIT. 