# Assistant Éducatif UQAR

## 🍎 Optimisé pour macOS Apple Silicon (M1/M2/M3)

## 📋 Description

Plateforme locale d'assistant éducatif permettant aux étudiants de réviser via un chatbot RAG (Retrieval-Augmented Generation). L'application offre un système de gestion de cours, génération d'exercices automatiques et chat intelligent basé sur les documents de cours.

**✨ Spécialement optimisé pour les puces Apple Silicon avec Ollama !**

## 🏗️ Architecture

### Stack Technique

- **Backend**: Python + FastAPI
- **Frontend**: Next.js (React)
- **Base de données vectorielle**: ChromaDB (collections par section)
- **Base de données relationnelle**: PostgreSQL
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (optimisé M1)
- **Authentification**: JWT + Argon2
- **IA**: Ollama + LLaMA 3.1 8B (natif Apple Silicon)
- **Conteneurisation**: Docker ou Apptainer

### Rôles Utilisateurs

- **Super-Admin**: Validation des comptes, gestion globale
- **Enseignant**: Gestion des sections, upload de cours, validation d'exercices
- **Étudiant**: Accès aux cours, chatbot RAG, exercices validés

## 🚀 Installation

### Prérequis

- Docker Desktop pour Mac (4.0+) OU Apptainer (1.0.0+)
- macOS 11+ avec Apple Silicon OU Linux 64-bit
- 8 GB RAM minimum, 15 GB espace disque

### Démarrage rapide avec Docker

```bash
# Cloner et démarrer
git clone <repo>
cd UQAR
chmod +x start.sh
./start.sh

# Accès
Frontend: http://localhost:3000
Backend API: http://localhost:8000
```

### Démarrage rapide avec Apptainer (Linux)

```bash
# Cloner le projet
git clone <repo>
cd UQAR

# Installer Apptainer si nécessaire
chmod +x install-apptainer.sh
./install-apptainer.sh

# Démarrer les services
chmod +x start-apptainer.sh
./start-apptainer.sh

# Accès
Frontend: http://localhost:3000
Backend API: http://localhost:8000
```

Pour plus d'informations sur l'utilisation d'Apptainer, consultez le fichier [APPTAINER.md](APPTAINER.md).

## 📁 Structure du Projet

```
UQAR/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Routes API
│   │   ├── core/           # Configuration, sécurité
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── services/       # Logique métier
│   │   └── utils/          # Utilitaires
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Application Next.js
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── pages/          # Pages Next.js
│   │   ├── hooks/          # Hooks personnalisés
│   │   └── utils/          # Utilitaires frontend
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Configuration Docker
├── *.def                   # Fichiers de définition Apptainer
├── start.sh                # Script de démarrage Docker
├── start-apptainer.sh      # Script de démarrage Apptainer
└── README.md
```

## 🔐 Fonctionnalités

### Authentification

- Système de comptes avec validation manuelle
- JWT sécurisé avec refresh tokens
- Hashing Argon2 pour les mots de passe

### Gestion des Cours (Enseignants)

- Création de sections de cours
- Upload de documents (PDF, DOCX, etc.)
- Vectorisation automatique dans ChromaDB
- Génération et validation d'exercices IA

### Apprentissage (Étudiants)

- Chatbot RAG contextuel par section
- Exercices validés par les enseignants
- Filtrage anti-hors-sujet
- Citations précises des sources

### IA Locale Apple Silicon

- Ollama + LLaMA 3.1 8B (performance native M1/M2/M3)
- Génération d'exercices adaptatifs
- RAG avec embeddings optimisés
- 100% local, aucun cloud

## 🍎 Avantages Apple Silicon

### Performance

- **Exécution native** sur puces M1/M2/M3
- **Consommation énergétique réduite**
- **Pas de GPU externe requis**
- **Temps de réponse < 3 secondes**

### Modèles recommandés

- **8-16 GB RAM**: LLaMA 3.1 8B (4.7GB)
- **32+ GB RAM**: LLaMA 3.1 70B (40GB)
- **Développement**: CodeLlama 7B (3.8GB)

## 🎯 Objectifs Pédagogiques

- Accompagnement autonome des étudiants
- Génération d'exercices adaptatifs
- Encouragement à la réflexion critique
- Prévention du plagiat passif

## 📝 Licence

Projet éducatif UQAR - Usage interne
